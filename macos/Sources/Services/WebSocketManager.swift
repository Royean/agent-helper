//
//  WebSocketManager.swift
//  AgentLinker macOS
//

import Foundation
import Starscream

class WebSocketManager: ObservableObject {
    @Published var isConnected = false
    @Published var lastError: String?
    
    private var socket: WebSocket?
    private let serverUrl: String
    private var reconnectTimer: Timer?
    private var reconnectAttempts = 0
    private let maxReconnectAttempts = 5
    
    init(serverUrl: String = "ws://43.98.243.80:8080/ws/client") {
        self.serverUrl = serverUrl
    }
    
    func connect(deviceId: String, deviceName: String, token: String) {
        guard let url = URL(string: serverUrl) else {
            lastError = "Invalid server URL"
            return
        }
        
        var request = URLRequest(url: url)
        request.timeoutInterval = 5
        
        socket = WebSocket(request: request)
        
        socket?.onEvent = { [weak self] event in
            switch event {
            case .connected:
                print("✅ WebSocket connected")
                self?.isConnected = true
                self?.reconnectAttempts = 0
                self?.lastError = nil
                
                // 注册设备
                self?.registerDevice(deviceId: deviceId, deviceName: deviceName, token: token)
                
            case .disconnected(let error, _):
                print("❌ WebSocket disconnected: \(error?.localizedDescription ?? "unknown")")
                self?.isConnected = false
                self?.scheduleReconnect(deviceId: deviceId, deviceName: deviceName, token: token)
                
            case .text(let string):
                self?.handleMessage(string)
                
            case .binary(let data):
                print("Received binary data: \(data.count) bytes")
                
            case .ping(let data):
                print("Ping received: \(data?.count ?? 0) bytes")
                
            case .pong(let data):
                print("Pong received: \(data?.count ?? 0) bytes")
                
            case .viabilityChanged(let isViable):
                print("Viability changed: \(isViable)")
                
            case .reconnectSuggested(let shouldReconnect):
                print("Reconnect suggested: \(shouldReconnect)")
                if shouldReconnect {
                    self?.scheduleReconnect(deviceId: deviceId, deviceName: deviceName, token: token)
                }
                
            case .peerClosed:
                print("Peer closed connection")
                self?.isConnected = false
                
            case .error(let error):
                print("WebSocket error: \(error?.localizedDescription ?? "unknown")")
                self?.lastError = error?.localizedDescription
                self?.isConnected = false
            }
        }
        
        socket?.connect()
    }
    
    func disconnect() {
        reconnectTimer?.invalidate()
        reconnectTimer = nil
        socket?.disconnect()
        socket = nil
        isConnected = false
    }
    
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
    
    private func registerDevice(deviceId: String, deviceName: String, token: String) {
        let register = DeviceRegister(
            device_id: deviceId,
            device_name: deviceName,
            device_type: "mac",
            os: ProcessInfo.processInfo.operatingSystemVersionString,
            token: token
        )
        send(message: register)
    }
    
    private func scheduleReconnect(deviceId: String, deviceName: String, token: String) {
        guard reconnectAttempts < maxReconnectAttempts else {
            lastError = "Max reconnect attempts reached"
            return
        }
        
        reconnectAttempts += 1
        let delay = Double(reconnectAttempts) * 2.0 // Exponential backoff
        
        reconnectTimer?.invalidate()
        reconnectTimer = Timer.scheduledTimer(withTimeInterval: delay, repeats: false) { [weak self] _ in
            print("🔄 Reconnecting (attempt \(self?.reconnectAttempts ?? 0)/\(self?.maxReconnectAttempts ?? 5))...")
            self?.connect(deviceId: deviceId, deviceName: deviceName, token: token)
        }
    }
    
    private func handleMessage(_ string: String) {
        print("📥 Received: \(string)")
        
        guard let data = string.data(using: .utf8) else { return }
        
        do {
            if let json = try JSONSerialization.jsonObject(with: data) as? [String: Any] {
                // 处理服务器消息
                if let action = json["action"] as? String {
                    switch action {
                    case "device.registered":
                        print("✅ Device registered successfully")
                    case "command.result":
                        print("📊 Command result received")
                    default:
                        break
                    }
                }
            }
        } catch {
            print("Failed to parse message: \(error)")
        }
    }
}
