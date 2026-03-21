//
//  Device.swift
//  AgentLinker macOS
//

import Foundation

enum DeviceType: String, Codable, CaseIterable {
    case mac = "macOS"
    case windows = "Windows"
    case linux = "Linux"
    
    var icon: String {
        switch self {
        case .mac: return "desktopcomputer"
        case .windows: return "laptopcomputer"
        case .linux: return "server.rack"
        }
    }
}

enum DeviceStatus: String, Codable {
    case online = "online"
    case offline = "offline"
    case pairing = "pairing"
    
    var color: String {
        switch self {
        case .online: return "green"
        case .offline: return "gray"
        case .pairing: return "yellow"
        }
    }
}

struct Device: Codable, Identifiable, Equatable, Hashable {
    let id: String
    let name: String
    let type: DeviceType
    let os: String
    var status: DeviceStatus
    let lastSeen: Date
    let ipAddress: String?
    let pairingKey: String?
    
    static let mock = Device(
        id: "device_123",
        name: "MacBook Pro",
        type: .mac,
        os: "macOS 14.0",
        status: .online,
        lastSeen: Date(),
        ipAddress: "192.168.1.100",
        pairingKey: "AL-XXXX-XXXX-XXXX"
    )
}
