//
//  Messages.swift
//  AgentLinker macOS
//

import Foundation

// WebSocket 消息协议
protocol WebSocketMessage: Codable {
    var action: String { get }
}

// 设备注册消息
struct DeviceRegister: WebSocketMessage {
    let action = "device.register"
    let device_id: String
    let device_name: String
    let device_type: String
    let os: String
    let token: String
}

// 设备状态更新
struct DeviceStatusUpdate: WebSocketMessage {
    let action = "device.status"
    let device_id: String
    let status: String
}

// 配对请求
struct PairingRequest: WebSocketMessage {
    let action = "device.pair"
    let device_id: String
    let pairing_key: String
}

// 命令执行请求
struct CommandRequest: WebSocketMessage {
    let action = "command.exec"
    let device_id: String
    let command: String
    let args: [String: Any]?
}

// 服务器响应
struct ServerResponse: Codable {
    let action: String
    let success: Bool
    let data: [String: Any]?
    let error: String?
}
