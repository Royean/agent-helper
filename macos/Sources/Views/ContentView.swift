//
//  ContentView.swift
//  AgentLinker macOS
//

import SwiftUI

struct ContentView: View {
    @EnvironmentObject var deviceManager: DeviceManager
    @EnvironmentObject var webSocketManager: WebSocketManager
    @State private var showingSettings = false
    
    var body: some View {
        VStack(spacing: 0) {
            // Header
            headerView
                .padding()
            
            Divider()
            
            // Main Content
            ScrollView {
                VStack(spacing: 24) {
                    // Status Card
                    statusCard
                    
                    // Device Info Card
                    deviceInfoCard
                    
                    // Pairing Card
                    pairingCard
                    
                    // Quick Actions
                    quickActions
                }
                .padding()
            }
        }
        .frame(width: 500, height: 600)
        .background(Color(NSColor.windowBackgroundColor))
        .sheet(isPresented: $showingSettings) {
            SettingsView()
                .environmentObject(deviceManager)
                .environmentObject(webSocketManager)
        }
    }
    
    // MARK: - Header
    private var headerView: some View {
        HStack {
            HStack(spacing: 12) {
                Image(systemName: "desktopcomputer.badge.checkmark")
                    .font(.system(size: 32))
                    .foregroundStyle(
                        LinearGradient(
                            colors: [.blue, .purple],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        )
                    )
                
                VStack(alignment: .leading, spacing: 4) {
                    Text("AgentLinker")
                        .font(.title2)
                        .fontWeight(.bold)
                    
                    HStack(spacing: 6) {
                        Circle()
                            .fill(webSocketManager.isConnected ? Color.green : Color.orange)
                            .frame(width: 8, height: 8)
                        
                        Text(webSocketManager.isConnected ? "Connected" : "Connecting...")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                }
            }
            
            Spacer()
            
            Button(action: { showingSettings = true }) {
                Image(systemName: "gearshape")
                    .font(.title3)
            }
            .buttonStyle(.plain)
        }
    }
    
    // MARK: - Status Card
    private var statusCard: some View {
        VStack(alignment: .leading, spacing: 16) {
            HStack {
                Image(systemName: "info.circle")
                    .foregroundColor(.blue)
                Text("Device Status")
                    .font(.headline)
            }
            
            HStack(spacing: 20) {
                StatusIndicator(
                    title: "Connection",
                    status: webSocketManager.isConnected ? "Online" : "Offline",
                    icon: "wifi",
                    color: webSocketManager.isConnected ? "green" : "gray"
                )
                
                StatusIndicator(
                    title: "Service",
                    status: "Running",
                    icon: "play.circle",
                    color: "green"
                )
                
                StatusIndicator(
                    title: "Agent",
                    status: "Ready",
                    icon: "robot",
                    color: "blue"
                )
            }
        }
        .padding()
        .background(
            RoundedRectangle(cornerRadius: 12)
                .fill(Color(NSColor.controlBackgroundColor))
        )
    }
    
    // MARK: - Device Info Card
    private var deviceInfoCard: some View {
        VStack(alignment: .leading, spacing: 16) {
            HStack {
                Image(systemName: "macbook")
                    .foregroundColor(.purple)
                Text("Device Information")
                    .font(.headline)
            }
            
            VStack(alignment: .leading, spacing: 12) {
                InfoRow(label: "Device Name", value: deviceManager.deviceName)
                InfoRow(label: "Device ID", value: deviceManager.deviceId, isMonospace: true)
                InfoRow(label: "Platform", value: "macOS \(ProcessInfo.processInfo.operatingSystemVersionString)")
                InfoRow(label: "Server", value: deviceManager.serverUrl)
            }
        }
        .padding()
        .background(
            RoundedRectangle(cornerRadius: 12)
                .fill(Color(NSColor.controlBackgroundColor))
        )
    }
    
    // MARK: - Pairing Card
    private var pairingCard: some View {
        VStack(alignment: .leading, spacing: 16) {
            HStack {
                Image(systemName: "link.badge.plus")
                    .foregroundColor(.green)
                Text("Pairing")
                    .font(.headline)
            }
            
            VStack(alignment: .leading, spacing: 12) {
                HStack {
                    Text("Pairing Key:")
                        .foregroundColor(.secondary)
                    
                    Spacer()
                    
                    Text(deviceManager.pairingKey)
                        .font(.system(.body, design: .monospaced))
                        .fontWeight(.semibold)
                        .foregroundColor(.accentColor)
                }
                
                HStack(spacing: 12) {
                    Button(action: {
                        deviceManager.copyPairingKey()
                    }) {
                        Label("Copy Key", systemImage: "doc.on.doc")
                            .frame(maxWidth: .infinity)
                    }
                    .buttonStyle(.bordered)
                    
                    Button(action: {
                        deviceManager.refreshPairingKey()
                    }) {
                        Label("Refresh", systemImage: "arrow.clockwise")
                            .frame(maxWidth: .infinity)
                    }
                    .buttonStyle(.bordered)
                }
            }
        }
        .padding()
        .background(
            RoundedRectangle(cornerRadius: 12)
                .fill(Color(NSColor.controlBackgroundColor))
        )
    }
    
    // MARK: - Quick Actions
    private var quickActions: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Quick Actions")
                .font(.headline)
            
            HStack(spacing: 12) {
                ActionButton(title: "Copy Device ID", icon: "doc.on.clipboard") {
                    deviceManager.copyDeviceId()
                }
                
                ActionButton(title: "Test Connection", icon: "antenna.radiowaves.left.and.right") {
                    // Test connection logic
                }
                
                ActionButton(title: "View Logs", icon: "list.bullet") {
                    // View logs
                }
            }
        }
        .padding()
        .background(
            RoundedRectangle(cornerRadius: 12)
                .fill(Color(NSColor.controlBackgroundColor))
        )
    }
}

// MARK: - Subviews
struct StatusIndicator: View {
    let title: String
    let status: String
    let icon: String
    let color: String
    
    var body: some View {
        VStack(spacing: 8) {
            Image(systemName: icon)
                .font(.title2)
                .foregroundColor(Color(color))
            
            Text(status)
                .font(.caption)
                .fontWeight(.medium)
            
            Text(title)
                .font(.caption2)
                .foregroundColor(.secondary)
        }
        .frame(maxWidth: .infinity)
    }
}

struct InfoRow: View {
    let label: String
    let value: String
    var isMonospace: Bool = false
    
    var body: some View {
        HStack {
            Text(label)
                .foregroundColor(.secondary)
                .frame(width: 100, alignment: .leading)
            
            Text(value)
                .font(isMonospace ? .system(.body, design: .monospaced) : .body)
                .fontWeight(isMonospace ? .medium : .regular)
                .lineLimit(1)
            
            Spacer()
        }
    }
}

struct ActionButton: View {
    let title: String
    let icon: String
    let action: () -> Void
    
    var body: some View {
        Button(action: action) {
            VStack(spacing: 8) {
                Image(systemName: icon)
                    .font(.title2)
                Text(title)
                    .font(.caption)
            }
            .frame(maxWidth: .infinity)
            .padding(.vertical, 12)
        }
        .buttonStyle(.bordered)
    }
}

#Preview {
    ContentView()
        .environmentObject(DeviceManager())
        .environmentObject(WebSocketManager())
}
