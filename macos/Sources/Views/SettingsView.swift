//
//  SettingsView.swift
//  AgentLinker macOS
//

import SwiftUI

struct SettingsView: View {
    @EnvironmentObject var deviceManager: DeviceManager
    @EnvironmentObject var webSocketManager: WebSocketManager
    @Environment(\.dismiss) var dismiss
    
    @State private var deviceName: String = ""
    @State private var serverUrl: String = ""
    @State private var autoStart: Bool = true
    @State private var launchAtLogin: Bool = false
    
    var body: some View {
        NavigationStack {
            Form {
                Section("Device") {
                    TextField("Device Name", text: $deviceName)
                    
                    TextField("Server URL", text: $serverUrl)
                    
                    Toggle("Auto-start on launch", isOn: $autoStart)
                    
                    Toggle("Launch at login", isOn: $launchAtLogin)
                }
                
                Section("Connection") {
                    HStack {
                        Text("Status")
                        Spacer()
                        HStack(spacing: 6) {
                            Circle()
                                .fill(webSocketManager.isConnected ? Color.green : Color.orange)
                                .frame(width: 8, height: 8)
                            
                            Text(webSocketManager.isConnected ? "Connected" : "Disconnected")
                                .foregroundColor(.secondary)
                        }
                    }
                    
                    if let error = webSocketManager.lastError {
                        HStack {
                            Image(systemName: "exclamationmark.triangle")
                                .foregroundColor(.orange)
                            Text(error)
                                .foregroundColor(.secondary)
                                .font(.caption)
                        }
                    }
                    
                    Button(action: reconnect) {
                        HStack {
                            Image(systemName: "arrow.clockwise")
                            Text("Reconnect")
                        }
                    }
                    .disabled(webSocketManager.isConnected)
                }
                
                Section("About") {
                    HStack {
                        Text("Version")
                        Spacer()
                        Text("1.0.0")
                            .foregroundColor(.secondary)
                    }
                    
                    HStack {
                        Text("Build")
                        Spacer()
                        Text("2026.03.20")
                            .foregroundColor(.secondary)
                    }
                    
                    Link("GitHub Repository", destination: URL(string: "https://github.com/Royean/AgentLinker")!)
                }
            }
            .formStyle(.grouped)
            .navigationTitle("Settings")
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button("Save") {
                        saveSettings()
                        dismiss()
                    }
                }
                
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") {
                        dismiss()
                    }
                }
            }
            .onAppear {
                deviceName = deviceManager.deviceName
                serverUrl = deviceManager.serverUrl
            }
        }
        .frame(width: 450, height: 400)
    }
    
    private func saveSettings() {
        deviceManager.deviceName = deviceName
        deviceManager.serverUrl = serverUrl
        deviceManager.saveConfig()
        
        // Reconnect with new settings if connected
        if webSocketManager.isConnected {
            webSocketManager.disconnect()
            webSocketManager.connect(
                deviceId: deviceManager.deviceId,
                deviceName: deviceName,
                token: "ah_device_token_change_in_production"
            )
        }
    }
    
    private func reconnect() {
        webSocketManager.disconnect()
        webSocketManager.connect(
            deviceId: deviceManager.deviceId,
            deviceName: deviceManager.deviceName,
            token: "ah_device_token_change_in_production"
        )
    }
}

#Preview {
    SettingsView()
        .environmentObject(DeviceManager())
        .environmentObject(WebSocketManager())
}
