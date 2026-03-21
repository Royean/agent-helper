//
//  DeviceManager.swift
//  AgentLinker macOS
//

import Foundation
import Combine
import AppKit

class DeviceManager: ObservableObject {
    @Published var deviceId: String = ""
    @Published var deviceName: String = ""
    @Published var pairingKey: String = ""
    @Published var serverUrl: String = ""
    @Published var isConnected = false
    @Published var statusMessage: String = ""
    
    private let configManager: ConfigManager
    private var cancellables = Set<AnyCancellable>()
    
    init() {
        self.configManager = ConfigManager()
        loadConfig()
    }
    
    func loadConfig() {
        deviceId = configManager.deviceId
        deviceName = configManager.deviceName
        serverUrl = configManager.serverUrl
        pairingKey = generatePairingKey()
    }
    
    func saveConfig() {
        configManager.deviceId = deviceId
        configManager.deviceName = deviceName
        configManager.serverUrl = serverUrl
    }
    
    func refreshPairingKey() {
        pairingKey = generatePairingKey()
    }
    
    func copyPairingKey() -> Bool {
        let fullKey = "al_\(deviceId)_\(pairingKey)"
        #if os(macOS)
        NSPasteboard.general.clearContents()
        NSPasteboard.general.setString(fullKey, forType: .string)
        return true
        #else
        return false
        #endif
    }
    
    func copyDeviceId() -> Bool {
        #if os(macOS)
        NSPasteboard.general.clearContents()
        NSPasteboard.general.setString(deviceId, forType: .string)
        return true
        #else
        return false
        #endif
    }
    
    private func generatePairingKey() -> String {
        let chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
        var key = ""
        for _ in 0..<4 {
            let index = Int.random(in: 0..<chars.count)
            key.append(chars[chars.index(chars.startIndex, offsetBy: index)])
        }
        return key
    }
}

// MARK: - Config Manager
class ConfigManager {
    private let defaults = UserDefaults.standard
    private let deviceIdKey = "device_id"
    private let deviceNameKey = "device_name"
    private let serverUrlKey = "server_url"
    
    var deviceId: String {
        get {
            if let id = defaults.string(forKey: deviceIdKey), !id.isEmpty {
                return id
            }
            let newId = generateDeviceId()
            defaults.set(newId, forKey: deviceIdKey)
            return newId
        }
        set {
            defaults.set(newValue, forKey: deviceIdKey)
        }
    }
    
    var deviceName: String {
        get {
            if let name = defaults.string(forKey: deviceNameKey), !name.isEmpty {
                return name
            }
            let newName = Host.current().localizedName()
            defaults.set(newName, forKey: deviceNameKey)
            return newName
        }
        set {
            defaults.set(newValue, forKey: deviceNameKey)
        }
    }
    
    var serverUrl: String {
        get {
            defaults.string(forKey: serverUrlKey) ?? "ws://127.0.0.1:8080/ws/client"
        }
        set {
            defaults.set(newValue, forKey: serverUrlKey)
        }
    }
    
    private func generateDeviceId() -> String {
        let prefix = "mac"
        let uuid = UUID().uuidString.replacingOccurrences(of: "-", with: "")
        return "\(prefix)_\(uuid.prefix(16))"
    }
}

// MARK: - Host helper
struct Host {
    static func current() -> Host {
        return Host()
    }
    
    func localizedName() -> String {
        let name = ProcessInfo.processInfo.hostName
        if !name.isEmpty {
            return name
        }
        return "Unknown Mac"
    }
}
