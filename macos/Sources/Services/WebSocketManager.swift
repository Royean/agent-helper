//
//  WebSocketManager.swift
//  AgentLinker macOS
//

import Foundation
import Starscream

enum ConnectionMode {
    case active      // 客户端主动发起
    case passive     // 等待服务端发起
}

enum ConnectionState {
    case disconnected
    case connecting
    case connected
    case listening      // 被动监听中
    case requested      // 收到连接请求
    case authorized     // 已授权控制
    case reconnecting   // 重新连接中
    case failed
}

class WebSocketManager: ObservableObject, WebSocketDelegate {
    @Published var isConnected = false
    @Published var isListening = false
    @Published var isControllerConnected = false
    @Published var accessGranted = false
    @Published var connectionState: ConnectionState = .disconnected
    @Published var lastError: String?
    @Published var lastMessage: String?

    private var socket: WebSocket?
    private let serverUrl: String
    private var reconnectTimer: Timer?
    private var heartbeatTimer: Timer?
    private var reconnectAttempts = 0
    private let maxReconnectAttempts = 10
    private let heartbeatInterval: TimeInterval = 30
    private var currentDeviceId: String = ""
    private var currentDeviceName: String = ""
    private var currentToken: String = ""
    private var currentMode: ConnectionMode = .active
    private var connectionRequestHandler: ((ConnectionRequest) -> Void)?

    init(serverUrl: String = "ws://127.0.0.1:8080/ws/client") {
        self.serverUrl = serverUrl
    }

    func setConnectionRequestHandler(_ handler: @escaping (ConnectionRequest) -> Void) {
        self.connectionRequestHandler = handler
    }

    // MARK: - Active Connection (Client Initiated)
    func connect(deviceId: String, deviceName: String, token: String, mode: ConnectionMode = .active) {
        self.currentDeviceId = deviceId
        self.currentDeviceName = deviceName
        self.currentToken = token
        self.currentMode = mode

        DispatchQueue.main.async {
            self.connectionState = .connecting
        }

        guard let url = URL(string: serverUrl) else {
            DispatchQueue.main.async {
                self.lastError = "Invalid server URL"
                self.connectionState = .failed
            }
            return
        }

        var request = URLRequest(url: url)
        request.timeoutInterval = 10

        socket = WebSocket(request: request)
        socket?.delegate = self
        socket?.connect()
    }

    // MARK: - Passive Listening (Server Initiated)
    func startListening(deviceId: String, token: String) {
        self.currentDeviceId = deviceId
        self.currentToken = token
        self.currentMode = .passive

        DispatchQueue.main.async {
            self.isListening = true
            self.connectionState = .listening
        }

        // 被动模式下，先建立基础连接
        connect(deviceId: deviceId, deviceName: currentDeviceName, token: token, mode: .passive)
    }

    func didReceive(event: WebSocketEvent, client: WebSocketClient) {
        switch event {
        case .connected:
            handleConnected()

        case .disconnected(let reason, _):
            handleDisconnected(reason: reason)

        case .text(let string):
            handleMessage(string)

        case .binary(let data):
            print("Received binary data: \(data.count) bytes")

        case .ping(let data):
            print("Ping received: \(data?.count ?? 0) bytes")

        case .pong(let data):
            print("Pong received: \(data?.count ?? 0) bytes")

        case .viabilityChanged(let isViable):
            handleViabilityChanged(isViable)

        case .reconnectSuggested(let shouldReconnect):
            handleReconnectSuggested(shouldReconnect)

        case .peerClosed:
            handlePeerClosed()

        case .error(let error):
            handleError(error)

        default:
            break
        }
    }

    // MARK: - Event Handlers
    private func handleConnected() {
        print("✅ WebSocket connected")
        DispatchQueue.main.async {
            self.isConnected = true
            self.reconnectAttempts = 0
            self.lastError = nil
        }

        // 根据模式发送不同的注册消息
        switch currentMode {
        case .active:
            registerActive(deviceId: currentDeviceId, deviceName: currentDeviceName, token: currentToken)
        case .passive:
            registerPassive(deviceId: currentDeviceId, token: currentToken)
        }
    }

    private func handleDisconnected(reason: String) {
        print("❌ WebSocket disconnected: \(reason)")
        DispatchQueue.main.async {
            self.isConnected = false
            self.isControllerConnected = false
            self.accessGranted = false
            self.connectionState = .disconnected
        }
        stopHeartbeat()
        scheduleReconnect()
    }

    private func handleViabilityChanged(_ isViable: Bool) {
        print("Viability changed: \(isViable)")
        if !isViable {
            DispatchQueue.main.async {
                self.connectionState = .reconnecting
            }
        }
    }

    private func handleReconnectSuggested(_ shouldReconnect: Bool) {
        print("Reconnect suggested: \(shouldReconnect)")
        if shouldReconnect {
            scheduleReconnect()
        }
    }

    private func handlePeerClosed() {
        print("Peer closed connection")
        DispatchQueue.main.async {
            self.isConnected = false
            self.isControllerConnected = false
            self.accessGranted = false
            self.connectionState = .disconnected
        }
    }

    private func handleError(_ error: Error?) {
        let errorMsg = error?.localizedDescription ?? "unknown"
        print("WebSocket error: \(errorMsg)")
        DispatchQueue.main.async {
            self.lastError = errorMsg
            self.isConnected = false
            self.connectionState = .failed
        }
    }

    // MARK: - Registration
    private func registerActive(deviceId: String, deviceName: String, token: String) {
        // 主动连接模式 - 客户端发起，直接注册为可用设备
        let register: [String: Any] = [
            "type": "register",
            "device_id": deviceId,
            "device_name": deviceName,
            "token": token,
            "mode": "active",
            "auto_accept": true  // 主动模式下自动接受控制
        ]
        sendJSON(register)
    }

    private func registerPassive(deviceId: String, token: String) {
        // 被动连接模式 - 等待服务端发起，需要用户确认
        let register: [String: Any] = [
            "type": "register",
            "device_id": deviceId,
            "token": token,
            "mode": "passive",
            "auto_accept": false  // 被动模式下需要用户确认
        ]
        sendJSON(register)
    }

    // MARK: - Connection Request Handling
    func acceptConnection(request: ConnectionRequest) {
        let response: [String: Any] = [
            "type": "connection_response",
            "accepted": true,
            "controller_id": request.controllerId,
            "device_id": currentDeviceId
        ]
        sendJSON(response)

        DispatchQueue.main.async {
            self.isControllerConnected = true
            self.accessGranted = true
            self.connectionState = .authorized
        }

        startHeartbeat()
    }

    func rejectConnection(request: ConnectionRequest) {
        let response: [String: Any] = [
            "type": "connection_response",
            "accepted": false,
            "controller_id": request.controllerId,
            "device_id": currentDeviceId,
            "reason": "User rejected"
        ]
        sendJSON(response)

        DispatchQueue.main.async {
            self.connectionState = .listening
        }
    }

    // MARK: - Message Handling
    private func handleMessage(_ string: String) {
        print("📥 Received: \(string)")

        DispatchQueue.main.async {
            self.lastMessage = string
        }

        guard let data = string.data(using: .utf8),
              let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
              let msgType = json["type"] as? String else {
            print("Failed to parse message")
            return
        }

        switch msgType {
        case "registered":
            handleRegistered(json)
        case "pong":
            handlePong()
        case "pairing_key":
            handlePairingKey(json)
        case "connection_request":
            handleConnectionRequest(json)
        case "controller_connected":
            handleControllerConnected(json)
        case "controller_disconnected":
            handleControllerDisconnected()
        case "error":
            handleServerError(json)
        case "command":
            handleCommand(json)
        default:
            print("ℹ️ Unknown message type: \(msgType)")
        }
    }

    private func handleRegistered(_ json: [String: Any]) {
        print("✅ Device registered successfully")

        // 检查是否为自动接受模式
        if let autoAccept = json["auto_accept"] as? Bool, autoAccept {
            print("🔓 Auto-pair mode enabled")
            DispatchQueue.main.async {
                self.connectionState = .authorized
                self.isControllerConnected = true
                self.accessGranted = true
            }
        } else {
            DispatchQueue.main.async {
                self.connectionState = .connected
            }
        }

        // 启动心跳
        startHeartbeat()
    }

    private func handlePong() {
        print("💓 Pong received")
    }

    private func handlePairingKey(_ json: [String: Any]) {
        // 自动配对模式下不显示配对密钥
        if let pairingKey = json["pairing_key"] as? String {
            // 检查是否为自动配对密钥
            if pairingKey.hasPrefix("AUTO_") {
                print("🔓 Auto-paired, no key needed")
                DispatchQueue.main.async {
                    self.connectionState = .listening
                }
            } else {
                print("🔑 Pairing key received (hidden)")
                // 可选：自动复制到剪贴板
                // NSPasteboard.general.setString(pairingKey, forType: .string)
            }
        }
    }

    private func handleConnectionRequest(_ json: [String: Any]) {
        guard let controllerId = json["controller_id"] as? String,
              let controllerName = json["controller_name"] as? String else {
            return
        }

        print("📥 Connection request from: \(controllerName)")

        let request = ConnectionRequest(
            controllerId: controllerId,
            controllerName: controllerName,
            timestamp: Date()
        )

        DispatchQueue.main.async {
            self.connectionState = .requested
            self.connectionRequestHandler?(request)
        }
    }

    private func handleControllerConnected(_ json: [String: Any]) {
        print("✅ Controller connected")
        DispatchQueue.main.async {
            self.isControllerConnected = true
            self.accessGranted = true
            self.connectionState = .authorized
        }
        startHeartbeat()
    }

    private func handleControllerDisconnected() {
        print("❌ Controller disconnected")
        DispatchQueue.main.async {
            self.isControllerConnected = false
            self.accessGranted = false
            self.connectionState = .connected
        }
        stopHeartbeat()
    }

    private func handleServerError(_ json: [String: Any]) {
        if let msg = json["msg"] as? String {
            print("❌ Server error: \(msg)")
            DispatchQueue.main.async {
                self.lastError = msg
            }
        }
    }

    private func handleCommand(_ json: [String: Any]) {
        print("📊 Command received: \(json)")
        // 处理控制命令...
    }

    // MARK: - Connection Control
    func disconnect() {
        stopHeartbeat()
        reconnectTimer?.invalidate()
        reconnectTimer = nil
        socket?.disconnect()
        socket = nil

        DispatchQueue.main.async {
            self.isConnected = false
            self.isListening = false
            self.isControllerConnected = false
            self.accessGranted = false
            self.connectionState = .disconnected
        }
    }

    // MARK: - Messaging
    func send(message: WebSocketMessage) {
        guard isConnected, let socket = socket else {
            lastError = "Not connected"
            return
        }

        do {
            let encoder = JSONEncoder()
            let data = try encoder.encode(message)
            if let jsonString = String(data: data, encoding: .utf8) {
                socket.write(string: jsonString)
                print("📤 Sent: \(jsonString)")
            }
        } catch {
            lastError = "Failed to encode message: \(error.localizedDescription)"
        }
    }

    private func sendJSON(_ json: [String: Any]) {
        guard isConnected, let socket = socket else {
            print("Cannot send - not connected")
            return
        }

        do {
            let data = try JSONSerialization.data(withJSONObject: json)
            if let jsonString = String(data: data, encoding: .utf8) {
                socket.write(string: jsonString)
                print("📤 Sent: \(jsonString)")
            }
        } catch {
            print("Failed to send JSON: \(error)")
        }
    }

    // MARK: - Reconnect
    private func scheduleReconnect() {
        guard reconnectAttempts < maxReconnectAttempts else {
            DispatchQueue.main.async {
                self.lastError = "Max reconnect attempts reached"
                self.connectionState = .failed
            }
            return
        }

        reconnectAttempts += 1
        let delay = min(Double(reconnectAttempts) * 2.0, 30.0)

        DispatchQueue.main.async {
            self.connectionState = .reconnecting
        }

        reconnectTimer?.invalidate()
        reconnectTimer = Timer.scheduledTimer(withTimeInterval: delay, repeats: false) { [weak self] _ in
            print("🔄 Reconnecting (attempt \(self?.reconnectAttempts ?? 0)/\(self?.maxReconnectAttempts ?? 10))...")
            self?.connect(
                deviceId: self?.currentDeviceId ?? "",
                deviceName: self?.currentDeviceName ?? "",
                token: self?.currentToken ?? "",
                mode: self?.currentMode ?? .active
            )
        }
    }

    // MARK: - Heartbeat
    private func startHeartbeat() {
        heartbeatTimer?.invalidate()
        heartbeatTimer = Timer.scheduledTimer(withTimeInterval: heartbeatInterval, repeats: true) { [weak self] _ in
            self?.sendPing()
        }
        // 立即发送第一个 ping
        sendPing()
    }

    private func stopHeartbeat() {
        heartbeatTimer?.invalidate()
        heartbeatTimer = nil
    }

    private func sendPing() {
        guard isConnected, let socket = socket else { return }

        let pingMessage: [String: Any] = [
            "type": "ping",
            "time": Date().timeIntervalSince1970,
            "device_id": currentDeviceId
        ]

        do {
            let data = try JSONSerialization.data(withJSONObject: pingMessage)
            if let jsonString = String(data: data, encoding: .utf8) {
                socket.write(string: jsonString)
                print("💓 Heartbeat sent")
            }
        } catch {
            print("Failed to send heartbeat: \(error)")
        }
    }
}

// MARK: - Connection Request Struct
struct ConnectionRequest: Identifiable {
    let id = UUID()
    let controllerId: String
    let controllerName: String
    let timestamp: Date
}
