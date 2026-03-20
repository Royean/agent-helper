//
//  AgentLinkerApp.swift
//  AgentLinker macOS
//

import SwiftUI

@main
struct AgentLinkerApp: App {
    @StateObject private var deviceManager = DeviceManager()
    @StateObject private var webSocketManager = WebSocketManager()
    
    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(deviceManager)
                .environmentObject(webSocketManager)
                .onAppear {
                    // Auto-connect on launch
                    webSocketManager.connect(
                        deviceId: deviceManager.deviceId,
                        deviceName: deviceManager.deviceName,
                        token: "ah_device_token_change_in_production"
                    )
                }
        }
        .windowStyle(.hiddenTitleBar)
        .windowResizability(.contentSize)
        
        // Menu Bar Extra (optional)
        MenuBarExtra("AgentLinker", systemImage: "desktopcomputer") {
            MenuBarView()
                .environmentObject(deviceManager)
                .environmentObject(webSocketManager)
        }
        .menuBarExtraStyle(.window)
    }
}
