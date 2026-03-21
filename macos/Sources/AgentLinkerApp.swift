//
//  AgentLinkerApp.swift
//  AgentLinker macOS
//

import SwiftUI

@main
struct AgentLinkerApp: App {
    @StateObject private var deviceManager = DeviceManager()
    @StateObject private var webSocketManager = WebSocketManager()
    @StateObject private var authManager = AuthManager.shared
    
    var body: some Scene {
        WindowGroup {
            Group {
                if authManager.isAuthenticated {
                    ConnectionView()
                        .environmentObject(deviceManager)
                        .environmentObject(webSocketManager)
                        .environmentObject(authManager)
                } else {
                    LoginView()
                        .environmentObject(deviceManager)
                        .environmentObject(webSocketManager)
                        .environmentObject(authManager)
                }
            }
        }
        .windowStyle(.hiddenTitleBar)
        .windowResizability(.contentSize)

        // Menu Bar Extra (optional)
        MenuBarExtra("AgentLinker", systemImage: "desktopcomputer") {
            MenuBarView()
                .environmentObject(deviceManager)
                .environmentObject(webSocketManager)
                .environmentObject(authManager)
        }
        .menuBarExtraStyle(.window)
    }
}
