//
//  WebSocketManager.swift
//  AgentLinker macOS
//

import Foundation

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

class WebSocketManager: ObservableObject {
    @Published var isConnected = false
    @Published var isListening = false
    @Published var isControllerConnected = false
    @Published var accessGranted = false
    @Published var connectionState: ConnectionState = .disconnected
    @Published var lastError: String?
    @Published var lastMessage: String?

    private var webSocketTask: URLSessionWebSocketTask?
    private let serverUrl: String
    private var reconnectTimer: Timer?
    private let heartbeatQueue = DispatchQueue(label: "com.agentlinker.heartbeat", qos: .background)
    private var reconnectAttempts = 0
    private let maxReconnectAttempts = 10
    private let heartbeatInterval: TimeInterval = 30
    private var currentDeviceId: String = ""
    private var currentDeviceName: String = ""
    private var currentToken: String = ""
    private var currentMode: ConnectionMode = .active
    private var connectionRequestHandler: ((ConnectionRequest) -> Void)?

    init(serverUrl: String = "ws://43.98.243.80:8080/ws/client") {
        self.serverUrl = serverUrl
    }

    func setConnectionRequestHandler(_ handler: @escaping (ConnectionRequest) -> Void) {
        self.connectionRequestHandler = handler
    }

    // MARK: - Active Connection (Client Initiated)
    func connect(deviceId: String, deviceName: String, token: String, mode: ConnectionMode = .active) {
        print("🔗 connect() called with deviceId: \(deviceId), deviceName: \(deviceName)")
        self.currentDeviceId = deviceId
        self.currentDeviceName = deviceName
        self.currentToken = token
        self.currentMode = mode

        DispatchQueue.main.async {
            self.connectionState = .connecting
        }

        guard let url = URL(string: serverUrl) else {
            print("❌ Invalid server URL: \(self.serverUrl)")
            DispatchQueue.main.async {
                self.lastError = "Invalid server URL"
                self.connectionState = .failed
            }
            return
        }

        print("🔗 Connecting to: \(url)")

        let session = URLSession(configuration: .default)
        webSocketTask = session.webSocketTask(with: url)

        // 检查 WebSocketTask 状态
        NSLog("🔗 WebSocketTask created, state: \(webSocketTask?.state.rawValue ?? -1)")

        webSocketTask?.resume()

        NSLog("🔗 WebSocketTask resumed, state: \(webSocketTask?.state.rawValue ?? -1)")
        print("🔗 WebSocket task started")

        // 在主线程设置连接状态
        DispatchQueue.main.async {
            self.isConnected = true
        }

        // 等待一小段时间让 WebSocket 连接建立
        DispatchQueue.main.asyncAfter(deadline: .now() + 1.0) { [weak self] in
            guard let self = self else { return }
            NSLog("🔗 After delay, WebSocketTask state: \(self.webSocketTask?.state.rawValue ?? -1)")

            switch mode {
            case .active:
                self.registerActive(deviceId: deviceId, deviceName: deviceName, token: token)
            case .passive:
                self.registerPassive(deviceId: deviceId, token: token)
            }

            // 开始接收消息
            self.receiveMessage()
            self.startHeartbeat()
        }
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

        connect(deviceId: deviceId, deviceName: currentDeviceName, token: token, mode: .passive)
    }

    // MARK: - Message Receiving
    private func receiveMessage() {
        webSocketTask?.receive { [weak self] result in
            switch result {
            case .success(let message):
                switch message {
                case .string(let text):
                    print("📥 Received text: \(text)")
                    self?.handleMessage(text)
                case .data(let data):
                    print("📥 Received data: \(data.count) bytes")
                @unknown default:
                    break
                }
                // 继续接收下一条消息
                self?.receiveMessage()

            case .failure(let error):
                print("❌ Receive error: \(error)")
                self?.handleError(error)
            }
        }
    }

    // MARK: - Event Handlers
    private func handleConnected() {
        print("✅ handleConnected() called - WebSocket connected")
        isConnected = true
        reconnectAttempts = 0
        lastError = nil

        print("📤 Sending register message for device: \(currentDeviceId)")
        switch currentMode {
        case .active:
            registerActive(deviceId: currentDeviceId, deviceName: currentDeviceName, token: currentToken)
        case .passive:
            registerPassive(deviceId: currentDeviceId, token: currentToken)
        }

        DispatchQueue.main.async {
            self.objectWillChange.send()
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

    private func handleError(_ error: Error?) {
        let errorMsg = error?.localizedDescription ?? "unknown"
        print("❌ WebSocket error: \(errorMsg)")
        DispatchQueue.main.async {
            self.lastError = errorMsg
            self.isConnected = false
            self.connectionState = .failed
        }
    }

    // MARK: - Registration
    private func registerActive(deviceId: String, deviceName: String, token: String) {
        NSLog("📤 registerActive() called, WebSocketTask state: \(webSocketTask?.state.rawValue ?? -1)")
        let register: [String: Any] = [
            "type": "register",
            "device_id": deviceId,
            "device_name": deviceName,
            "token": token,
            "platform": "macOS",
            "mode": "active",
            "auto_accept": true
        ]
        print("📤 registerActive() - sending register message")
        NSLog("📤 Register message: \(register)")
        sendJSON(register)
    }

    private func registerPassive(deviceId: String, token: String) {
        let register: [String: Any] = [
            "type": "register",
            "device_id": deviceId,
            "token": token,
            "platform": "macOS",
            "mode": "passive",
            "auto_accept": false
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
        print("📥 handleMessage: \(string)")

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
        case "exec":
            handleExec(json)
        default:
            print("ℹ️ Unknown message type: \(msgType)")
        }
    }

    private func handleRegistered(_ json: [String: Any]) {
        print("✅ Device registered successfully")

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

        startHeartbeat()
    }

    private func handlePong() {
        print("💓 Pong received")
    }

    private func handlePairingKey(_ json: [String: Any]) {
        if let pairingKey = json["pairing_key"] as? String {
            if pairingKey.hasPrefix("AUTO_") {
                print("🔓 Auto-paired, no key needed")
                DispatchQueue.main.async {
                    self.connectionState = .listening
                }
            } else {
                print("🔑 Pairing key received: \(pairingKey)")
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
    }

    private func handleExec(_ json: [String: Any]) {
        print("⚙️ Exec received: \(json)")

        let reqId = json["req_id"] as? String ?? UUID().uuidString
        let action = json["action"] as? String ?? ""
        let params = json["params"] as? [String: Any] ?? [:]

        // 执行命令
        var result: [String: Any] = [
            "type": "result",
            "req_id": reqId
        ]

        switch action {
        case "shell":
            if let command = params["command"] as? String {
                let output = executeShellCommand(command)
                result["data"] = [
                    "success": true,
                    "output": output
                ]
            }
        case "ping":
            result["data"] = [
                "success": true,
                "message": "pong"
            ]
        default:
            result["data"] = [
                "success": false,
                "error": "Unknown action: \(action)"
            ]
        }

        // 发送结果
        sendJSON(result)
    }

    private func executeShellCommand(_ command: String) -> String {
        let task = Process()
        task.executableURL = URL(fileURLWithPath: "/bin/zsh")
        task.arguments = ["-c", command]

        let pipe = Pipe()
        task.standardOutput = pipe
        task.standardError = pipe

        do {
            try task.run()
            task.waitUntilExit()

            let data = pipe.fileHandleForReading.readDataToEndOfFile()
            return String(data: data, encoding: .utf8) ?? ""
        } catch {
            return "Error: \(error.localizedDescription)"
        }
    }

    // MARK: - Connection Control
    func disconnect() {
        stopHeartbeat()
        reconnectTimer?.invalidate()
        reconnectTimer = nil
        webSocketTask?.cancel(with: .normalClosure, reason: nil)
        webSocketTask = nil

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
        guard isConnected else {
            lastError = "Not connected"
            return
        }

        do {
            let encoder = JSONEncoder()
            let data = try encoder.encode(message)
            if let jsonString = String(data: data, encoding: .utf8) {
                sendString(jsonString)
            }
        } catch {
            lastError = "Failed to encode message: \(error.localizedDescription)"
        }
    }

    private func sendJSON(_ json: [String: Any]) {
        NSLog("📤 sendJSON called, WebSocketTask state: \(webSocketTask?.state.rawValue ?? -1)")
        do {
            let data = try JSONSerialization.data(withJSONObject: json)
            if let jsonString = String(data: data, encoding: .utf8) {
                print("📤 Sending JSON: \(jsonString)")
                NSLog("📤 JSON content: \(jsonString)")
                sendString(jsonString)
            }
        } catch {
            print("❌ Failed to send JSON: \(error)")
            NSLog("❌ JSON serialization error: \(error)")
        }
    }

    private func sendString(_ string: String) {
        NSLog("📤 sendString called, WebSocketTask: \(webSocketTask != nil ? "exists" : "nil"), state: \(webSocketTask?.state.rawValue ?? -1)")
        guard let task = webSocketTask, task.state == .running else {
            NSLog("❌ Cannot send - WebSocketTask not running")
            return
        }
        let message = URLSessionWebSocketTask.Message.string(string)
        task.send(message) { error in
            if let error = error {
                print("❌ Send error: \(error)")
                NSLog("❌ Send error: \(error)")
            } else {
                print("📤 Sent successfully")
                NSLog("📤 Sent successfully")
            }
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
        NSLog("💓 startHeartbeat() called")
        stopHeartbeat()

        // 立即发送初始心跳
        sendPing()

        // 使用 DispatchQueue 定时发送心跳
        heartbeatQueue.asyncAfter(deadline: .now() + heartbeatInterval) { [weak self] in
            self?.heartbeatLoop()
        }
    }

    private func heartbeatLoop() {
        guard webSocketTask != nil, isConnected else {
            NSLog("💓 Heartbeat loop stopped - not connected")
            return
        }

        sendPing()

        // 继续下一次心跳
        heartbeatQueue.asyncAfter(deadline: .now() + heartbeatInterval) { [weak self] in
            self?.heartbeatLoop()
        }
    }

    private func stopHeartbeat() {
        NSLog("💓 stopHeartbeat() called")
    }

    private func sendPing() {
        NSLog("💓 sendPing() called, WebSocketTask: \(webSocketTask != nil ? "exists" : "nil")")
        guard webSocketTask != nil else {
            print("💓 Cannot send ping - no connection")
            NSLog("💓 Cannot send ping - no connection")
            return
        }

        let pingMessage: [String: Any] = [
            "type": "ping",
            "time": Date().timeIntervalSince1970,
            "device_id": currentDeviceId
        ]

        do {
            let data = try JSONSerialization.data(withJSONObject: pingMessage)
            if let jsonString = String(data: data, encoding: .utf8) {
                sendString(jsonString)
                print("💓 Heartbeat sent")
                NSLog("💓 Heartbeat message: \(jsonString)")
            }
        } catch {
            print("Failed to send heartbeat: \(error)")
            NSLog("❌ Heartbeat error: \(error)")
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