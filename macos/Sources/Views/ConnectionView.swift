//
//  ConnectionView.swift
//  AgentLinker macOS
//

import SwiftUI

struct ConnectionView: View {
    @EnvironmentObject var deviceManager: DeviceManager
    @EnvironmentObject var webSocketManager: WebSocketManager
    @EnvironmentObject var authManager: AuthManager
    @State private var showingRequestAlert = false
    @State private var pendingRequest: ConnectionRequest?

    var body: some View {
        VStack(spacing: 24) {
            // Header
            headerView

            Divider()

            // Connection Status
            statusCard

            // Connection Options
            connectionOptions

            // Device Info
            deviceInfoCard

            Spacer()
        }
        .padding()
        .frame(width: 500, height: 600)
        .onAppear {
            setupConnectionHandler()
        }
        .alert("连接请求", isPresented: $showingRequestAlert, presenting: pendingRequest) { request in
            Button("拒绝", role: .cancel) {
                rejectConnection(request: request)
            }
            Button("允许") {
                acceptConnection(request: request)
            }
        } message: { request in
            Text("控制器 \(request.controllerName) 请求连接到你的设备\n\n允许此连接吗？")
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

                    Text("选择连接方式")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }

            Spacer()

            Button(action: { authManager.logout() }) {
                Image(systemName: "rectangle.portrait.and.arrow.right")
                    .font(.title3)
            }
            .buttonStyle(.plain)
            .help("退出登录")
        }
    }

    // MARK: - Status Card
    private var statusCard: some View {
        VStack(alignment: .leading, spacing: 16) {
            HStack {
                Image(systemName: "info.circle")
                    .foregroundColor(.blue)
                Text("连接状态")
                    .font(.headline)
            }

            HStack(spacing: 12) {
                StatusIndicator(
                    title: "服务器",
                    status: webSocketManager.isConnected ? "已连接" : "未连接",
                    icon: "wifi",
                    color: webSocketManager.isConnected ? "green" : "gray"
                )

                StatusIndicator(
                    title: "控制器",
                    status: webSocketManager.isControllerConnected ? "已连接" : "等待中",
                    icon: "person.2",
                    color: webSocketManager.isControllerConnected ? "green" : "orange"
                )

                StatusIndicator(
                    title: "访问权限",
                    status: webSocketManager.accessGranted ? "已授权" : "未授权",
                    icon: "lock.open",
                    color: webSocketManager.accessGranted ? "green" : "red"
                )
            }
        }
        .padding()
        .background(
            RoundedRectangle(cornerRadius: 12)
                .fill(Color(NSColor.controlBackgroundColor))
        )
    }

    // MARK: - Connection Options
    private var connectionOptions: some View {
        VStack(alignment: .leading, spacing: 16) {
            HStack {
                Image(systemName: "link.circle")
                    .foregroundColor(.green)
                Text("连接方式")
                    .font(.headline)
            }

            VStack(spacing: 12) {
                // 主动连接 - 客户端发起
                ConnectionOptionCard(
                    title: "主动连接",
                    description: "立即连接到服务端，无需配对密钥",
                    icon: "arrow.up.right.circle.fill",
                    color: .blue,
                    isEnabled: !webSocketManager.isConnected,
                    action: {
                        webSocketManager.connect(
                            deviceId: deviceManager.deviceId,
                            deviceName: deviceManager.deviceName,
                            token: "ah_device_token_change_in_production",
                            mode: .active
                        )
                    }
                )

                // 被动连接 - 等待服务端
                ConnectionOptionCard(
                    title: "等待连接",
                    description: "等待服务端发起连接请求",
                    icon: "arrow.down.left.circle.fill",
                    color: .orange,
                    isEnabled: !webSocketManager.isListening,
                    action: {
                        webSocketManager.startListening(
                            deviceId: deviceManager.deviceId,
                            token: "ah_device_token_change_in_production"
                        )
                    }
                )

                // 断开连接
                if webSocketManager.isConnected || webSocketManager.isListening {
                    Button(action: { webSocketManager.disconnect() }) {
                        HStack {
                            Image(systemName: "xmark.circle.fill")
                            Text("断开连接")
                        }
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 10)
                    }
                    .buttonStyle(.bordered)
                    .tint(.red)
                }
            }
        }
        .padding()
        .background(
            RoundedRectangle(cornerRadius: 12)
                .fill(Color(NSColor.controlBackgroundColor))
        )
    }

    // MARK: - Device Info
    private var deviceInfoCard: some View {
        VStack(alignment: .leading, spacing: 16) {
            HStack {
                Image(systemName: "macbook")
                    .foregroundColor(.purple)
                Text("设备信息")
                    .font(.headline)
            }

            VStack(alignment: .leading, spacing: 12) {
                InfoRow(label: "设备名称", value: deviceManager.deviceName)
                InfoRow(label: "设备 ID", value: deviceManager.deviceId, isMonospace: true)
                InfoRow(label: "用户", value: authManager.currentUser?.name ?? "Unknown")
            }
        }
        .padding()
        .background(
            RoundedRectangle(cornerRadius: 12)
                .fill(Color(NSColor.controlBackgroundColor))
        )
    }

    // MARK: - Connection Handler
    private func setupConnectionHandler() {
        webSocketManager.setConnectionRequestHandler { request in
            DispatchQueue.main.async {
                self.pendingRequest = request
                self.showingRequestAlert = true
            }
        }
    }

    private func acceptConnection(request: ConnectionRequest) {
        webSocketManager.acceptConnection(request: request)
    }

    private func rejectConnection(request: ConnectionRequest) {
        webSocketManager.rejectConnection(request: request)
    }
}

// MARK: - Connection Option Card
struct ConnectionOptionCard: View {
    let title: String
    let description: String
    let icon: String
    let color: Color
    let isEnabled: Bool
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            HStack(spacing: 16) {
                Image(systemName: icon)
                    .font(.system(size: 32))
                    .foregroundColor(color)
                    .frame(width: 40)

                VStack(alignment: .leading, spacing: 4) {
                    Text(title)
                        .font(.headline)
                    Text(description)
                        .font(.caption)
                        .foregroundColor(.secondary)
                }

                Spacer()

                Image(systemName: "chevron.right")
                    .foregroundColor(.secondary)
            }
            .padding()
            .background(
                RoundedRectangle(cornerRadius: 8)
                    .fill(Color(NSColor.controlBackgroundColor))
            )
            .overlay(
                RoundedRectangle(cornerRadius: 8)
                    .stroke(color.opacity(0.3), lineWidth: 1)
            )
        }
        .buttonStyle(.plain)
        .disabled(!isEnabled)
        .opacity(isEnabled ? 1.0 : 0.6)
    }
}

#Preview {
    ConnectionView()
        .environmentObject(DeviceManager())
        .environmentObject(WebSocketManager())
        .environmentObject(AuthManager())
}
