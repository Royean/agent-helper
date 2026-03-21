//
//  LoginView.swift
//  AgentLinker macOS
//

import SwiftUI

struct LoginView: View {
    @EnvironmentObject var authManager: AuthManager
    @EnvironmentObject var deviceManager: DeviceManager
    @EnvironmentObject var webSocketManager: WebSocketManager
    @State private var email = ""
    @State private var password = ""
    @State private var isLoading = false
    @State private var showingRegister = false
    
    var body: some View {
        VStack(spacing: 24) {
            // Logo and Title
            VStack(spacing: 12) {
                Image(systemName: "desktopcomputer.badge.checkmark")
                    .font(.system(size: 48))
                    .foregroundStyle(
                        LinearGradient(
                            colors: [.blue, .purple],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        )
                    )
                
                Text("AgentLinker")
                    .font(.title)
                    .fontWeight(.bold)
                
                Text("Connect your devices securely")
                    .font(.subheadline)
                    .foregroundColor(.secondary)
            }
            .padding(.top, 20)
            
            // Login Form
            VStack(spacing: 16) {
                TextField("Email", text: $email)
                    .textFieldStyle(.roundedBorder)
                    .disableAutocorrection(true)
                
                SecureField("Password", text: $password)
                    .textFieldStyle(.roundedBorder)
                
                if let error = authManager.lastError {
                    HStack {
                        Image(systemName: "exclamationmark.triangle.fill")
                            .foregroundColor(.red)
                        Text(error)
                            .font(.caption)
                            .foregroundColor(.red)
                    }
                    .frame(maxWidth: .infinity, alignment: .leading)
                }
                
                Button(action: handleLogin) {
                    HStack {
                        if isLoading {
                            ProgressView()
                                .progressViewStyle(.circular)
                                .tint(.white)
                        }
                        Text(isLoading ? "Signing In..." : "Sign In")
                            .fontWeight(.semibold)
                    }
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 12)
                }
                .buttonStyle(.borderedProminent)
                .controlSize(.large)
                .disabled(isLoading || email.isEmpty || password.isEmpty)
                
                HStack {
                    Text("Don't have an account?")
                        .foregroundColor(.secondary)
                    
                    Button("Sign Up") {
                        showingRegister = true
                    }
                    .buttonStyle(.plain)
                    .foregroundColor(.accentColor)
                }
                .font(.caption)
            }
            .padding(.horizontal)
            
            Spacer()
        }
        .frame(width: 400, height: 500)
        .background(Color(NSColor.windowBackgroundColor))
        .sheet(isPresented: $showingRegister) {
            RegisterView()
                .environmentObject(authManager)
        }
        .onAppear {
            authManager.lastError = nil
        }
    }
    
    private func handleLogin() {
        isLoading = true

        Task {
            let success = await authManager.login(email: email, password: password)

            await MainActor.run {
                isLoading = false

                if success {
                    // 登录成功，但不自动连接
                    // 用户将在 ConnectionView 中选择连接方式
                    print("✅ Login successful - waiting for user to choose connection mode")
                }
            }
        }
    }
}

#Preview {
    LoginView()
        .environmentObject(AuthManager())
        .environmentObject(DeviceManager())
        .environmentObject(WebSocketManager())
}
