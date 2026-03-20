//
//  MenuBarView.swift
//  AgentLinker macOS
//

import SwiftUI

struct MenuBarView: View {
    @EnvironmentObject var deviceManager: DeviceManager
    @EnvironmentObject var webSocketManager: WebSocketManager
    @Environment(\.openWindow) var openWindow
    
    var body: some View {
        VStack(spacing: 12) {
            // Header
            HStack {
                Image(systemName: "desktopcomputer")
                    .foregroundColor(.blue)
                Text("AgentLinker")
                    .font(.headline)
            }
            .padding(.bottom, 8)
            
            Divider()
            
            // Status
            HStack {
                Circle()
                    .fill(webSocketManager.isConnected ? Color.green : Color.orange)
                    .frame(width: 8, height: 8)
                
                Text(webSocketManager.isConnected ? "Connected" : "Disconnected")
                    .font(.subheadline)
                
                Spacer()
            }
            
            // Device Info
            VStack(alignment: .leading, spacing: 4) {
                Text("Device: \(deviceManager.deviceName)")
                    .font(.caption)
                    .foregroundColor(.secondary)
                
                Text("ID: \(deviceManager.deviceId)")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            
            Divider()
            
            // Pairing Key
            VStack(alignment: .leading, spacing: 8) {
                Text("Pairing Key:")
                    .font(.caption)
                    .foregroundColor(.secondary)
                
                HStack {
                    Text(deviceManager.pairingKey)
                        .font(.system(.caption, design: .monospaced))
                        .fontWeight(.semibold)
                    
                    Spacer()
                    
                    Button(action: {
                        deviceManager.copyPairingKey()
                    }) {
                        Image(systemName: "doc.on.doc")
                            .font(.caption)
                    }
                    .buttonStyle(.plain)
                }
            }
            
            Divider()
            
            // Actions
            Button("Open Main Window") {
                openWindow(id: "main")
            }
            .buttonStyle(.bordered)
            .controlSize(.small)
            
            Button("Quit AgentLinker") {
                NSApp.terminate(nil)
            }
            .buttonStyle(.bordered)
            .controlSize(.small)
        }
        .padding()
        .frame(width: 250)
    }
}

#Preview {
    MenuBarView()
        .environmentObject(DeviceManager())
        .environmentObject(WebSocketManager())
}
