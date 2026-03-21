//
//  DeviceListView.swift
//  AgentLinker macOS
//

import SwiftUI

struct DeviceListView: View {
    @EnvironmentObject var deviceManager: DeviceManager
    @EnvironmentObject var webSocketManager: WebSocketManager
    @State private var showingAddDevice = false
    @State private var selectedDevice: Device?
    
    // Mock devices for demo - replace with actual API calls
    @State private var devices: [Device] = [
        Device(
            id: "device_001",
            name: "MacBook Pro",
            type: .mac,
            os: "macOS 14.0",
            status: .online,
            lastSeen: Date(),
            ipAddress: "192.168.1.100",
            pairingKey: "AL-MAC1-PRO1-2024"
        ),
        Device(
            id: "device_002",
            name: "iPhone 15",
            type: .mac, // Using mac as placeholder for mobile
            os: "iOS 17.0",
            status: .online,
            lastSeen: Date(),
            ipAddress: "192.168.1.101",
            pairingKey: "AL-IPHN-15PR-2024"
        ),
        Device(
            id: "device_003",
            name: "Home Server",
            type: .linux,
            os: "Ubuntu 22.04",
            status: .offline,
            lastSeen: Date().addingTimeInterval(-3600),
            ipAddress: "192.168.1.50",
            pairingKey: "AL-SRVR-HOME-2024"
        )
    ]
    
    var body: some View {
        VStack(spacing: 0) {
            // Header
            HStack {
                Text("My Devices")
                    .font(.title2)
                    .fontWeight(.bold)
                
                Spacer()
                
                Button(action: { showingAddDevice = true }) {
                    Label("Add Device", systemImage: "plus")
                }
            }
            .padding()
            
            Divider()
            
            // Device List
            if devices.isEmpty {
                VStack(spacing: 16) {
                    Image(systemName: "desktopcomputer")
                        .font(.system(size: 48))
                        .foregroundColor(.secondary)
                    
                    Text("No devices yet")
                        .font(.headline)
                    
                    Text("Add your first device to get started")
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                    
                    Button("Add Device") {
                        showingAddDevice = true
                    }
                    .buttonStyle(.borderedProminent)
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
                .padding()
            } else {
                List(devices, selection: $selectedDevice) { device in
                    DeviceRowView(device: device)
                        .tag(device)
                        .contextMenu {
                            Button("View Details") {
                                selectedDevice = device
                            }
                            
                            Button("Copy Pairing Key") {
                                copyPairingKey(device.pairingKey ?? "")
                            }
                            
                            Divider()
                            
                            Button("Remove Device", role: .destructive) {
                                removeDevice(device)
                            }
                        }
                }
                .listStyle(.inset)
            }
        }
        .frame(minWidth: 400, minHeight: 500)
        .sheet(item: $selectedDevice) { device in
            DeviceDetailView(device: device)
                .environmentObject(deviceManager)
                .environmentObject(webSocketManager)
        }
        .sheet(isPresented: $showingAddDevice) {
            AddDeviceView()
                .environmentObject(deviceManager)
                .environmentObject(webSocketManager)
        }
    }
    
    private func copyPairingKey(_ key: String) {
        #if os(macOS)
        NSPasteboard.general.clearContents()
        NSPasteboard.general.setString(key, forType: .string)
        #endif
    }
    
    private func removeDevice(_ device: Device) {
        withAnimation {
            devices.removeAll { $0.id == device.id }
        }
    }
}

// MARK: - Device Row View

struct DeviceRowView: View {
    let device: Device
    
    var body: some View {
        HStack(spacing: 12) {
            // Device Icon
            Image(systemName: device.type.icon)
                .font(.title2)
                .foregroundColor(.accentColor)
                .frame(width: 40, height: 40)
                .background(
                    Circle()
                        .fill(Color.accentColor.opacity(0.1))
                )
            
            // Device Info
            VStack(alignment: .leading, spacing: 4) {
                HStack {
                    Text(device.name)
                        .font(.headline)
                    
                    Circle()
                        .fill(colorForStatus(device.status))
                        .frame(width: 8, height: 8)
                }
                
                Text(device.os)
                    .font(.caption)
                    .foregroundColor(.secondary)
                
                Text(device.ipAddress ?? "Unknown IP")
                    .font(.caption2)
                    .foregroundColor(.secondary)
            }
            
            Spacer()
            
            // Status
            VStack(alignment: .trailing, spacing: 4) {
                Text(device.status.rawValue)
                    .font(.caption)
                    .fontWeight(.medium)
                    .foregroundColor(colorForStatus(device.status))
                
                Text(formatLastSeen(device.lastSeen))
                    .font(.caption2)
                    .foregroundColor(.secondary)
            }
        }
        .padding(.vertical, 8)
    }
    
    private func colorForStatus(_ status: DeviceStatus) -> Color {
        switch status {
        case .online: return .green
        case .offline: return .gray
        case .pairing: return .orange
        }
    }
    
    private func formatLastSeen(_ date: Date) -> String {
        let formatter = RelativeDateTimeFormatter()
        formatter.unitsStyle = .abbreviated
        return formatter.localizedString(for: date, relativeTo: Date())
    }
}

// MARK: - Add Device View

struct AddDeviceView: View {
    @EnvironmentObject var deviceManager: DeviceManager
    @EnvironmentObject var webSocketManager: WebSocketManager
    @Environment(\.dismiss) var dismiss
    
    @State private var deviceName = ""
    @State private var deviceType: DeviceType = .mac
    @State private var pairingKey = ""
    @State private var isLoading = false
    @State private var showSuccess = false
    
    var body: some View {
        VStack(spacing: 24) {
            Text("Add New Device")
                .font(.title2)
                .fontWeight(.bold)
            
            Form {
                TextField("Device Name", text: $deviceName)
                
                Picker("Device Type", selection: $deviceType) {
                    ForEach(DeviceType.allCases, id: \.self) { type in
                        Text(type.rawValue).tag(type)
                    }
                }
                
                TextField("Pairing Key (Optional)", text: $pairingKey)
                    .help("Enter pairing key if you have one")
            }
            .formStyle(.grouped)
            
            HStack {
                Button("Cancel") {
                    dismiss()
                }
                .keyboardShortcut(.cancelAction)
                
                Spacer()
                
                Button(action: handleAddDevice) {
                    if isLoading {
                        ProgressView()
                            .progressViewStyle(.circular)
                            .tint(.white)
                    }
                    Text(isLoading ? "Adding..." : "Add Device")
                        .fontWeight(.semibold)
                }
                .buttonStyle(.borderedProminent)
                .disabled(isLoading || deviceName.isEmpty)
            }
        }
        .padding()
        .frame(width: 400)
        .alert("Device Added!", isPresented: $showSuccess) {
            Button("Done") {
                dismiss()
            }
        } message: {
            Text("\"\(deviceName)\" has been added successfully.")
        }
    }
    
    private func handleAddDevice() {
        isLoading = true
        
        // Simulate adding device
        DispatchQueue.main.asyncAfter(deadline: .now() + 1) {
            isLoading = false
            showSuccess = true
        }
    }
}

// MARK: - Device Detail View

struct DeviceDetailView: View {
    @EnvironmentObject var deviceManager: DeviceManager
    @EnvironmentObject var webSocketManager: WebSocketManager
    @Environment(\.dismiss) var dismiss
    
    let device: Device
    
    var body: some View {
        VStack(spacing: 0) {
            // Header
            HStack {
                Text("Device Details")
                    .font(.title2)
                    .fontWeight(.bold)
                
                Spacer()
                
                Button("Done") {
                    dismiss()
                }
            }
            .padding()
            
            Divider()
            
            ScrollView {
                VStack(spacing: 24) {
                    // Device Icon and Name
                    VStack(spacing: 12) {
                        Image(systemName: device.type.icon)
                            .font(.system(size: 64))
                            .foregroundColor(.accentColor)
                        
                        Text(device.name)
                            .font(.title)
                            .fontWeight(.bold)
                        
                        StatusBadge(status: device.status)
                    }
                    .padding()
                    
                    // Info Grid
                    VStack(alignment: .leading, spacing: 16) {
                        DetailRow(label: "Device ID", value: device.id, isMonospace: true)
                        DetailRow(label: "Type", value: device.type.rawValue)
                        DetailRow(label: "OS", value: device.os)
                        DetailRow(label: "IP Address", value: device.ipAddress ?? "N/A")
                        DetailRow(label: "Last Seen", value: formatLastSeen(device.lastSeen))
                        DetailRow(label: "Pairing Key", value: device.pairingKey ?? "N/A", isMonospace: true)
                    }
                    .padding(.horizontal)
                    
                    // Actions
                    VStack(spacing: 12) {
                        Button("Test Connection") {
                            // Test connection logic
                        }
                        .buttonStyle(.bordered)
                        .frame(maxWidth: .infinity)
                        
                        Button("Remove Device", role: .destructive) {
                            // Remove logic
                        }
                        .buttonStyle(.bordered)
                        .frame(maxWidth: .infinity)
                    }
                    .padding(.horizontal)
                }
                .padding(.vertical)
            }
        }
        .frame(width: 450, height: 600)
    }
    
    private func formatLastSeen(_ date: Date) -> String {
        let formatter = RelativeDateTimeFormatter()
        formatter.unitsStyle = .full
        return formatter.localizedString(for: date, relativeTo: Date())
    }
}

struct DetailRow: View {
    let label: String
    let value: String
    var isMonospace: Bool = false
    
    var body: some View {
        HStack {
            Text(label)
                .foregroundColor(.secondary)
                .frame(width: 120, alignment: .leading)
            
            Text(value)
                .font(isMonospace ? .system(.body, design: .monospaced) : .body)
                .fontWeight(isMonospace ? .medium : .regular)
            
            Spacer()
        }
    }
}

struct StatusBadge: View {
    let status: DeviceStatus
    
    var body: some View {
        HStack(spacing: 6) {
            Circle()
                .fill(colorForStatus(status))
                .frame(width: 8, height: 8)
            
            Text(status.rawValue)
                .font(.caption)
                .fontWeight(.medium)
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 6)
        .background(
            Capsule()
                .fill(colorForStatus(status).opacity(0.1))
        )
    }
    
    private func colorForStatus(_ status: DeviceStatus) -> Color {
        switch status {
        case .online: return .green
        case .offline: return .gray
        case .pairing: return .orange
        }
    }
}

#Preview {
    DeviceListView()
        .environmentObject(DeviceManager())
        .environmentObject(WebSocketManager())
}
