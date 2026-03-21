//
//  RegisterView.swift
//  AgentLinker macOS
//

import SwiftUI

struct RegisterView: View {
    @EnvironmentObject var authManager: AuthManager
    @Environment(\.dismiss) var dismiss
    
    @State private var name = ""
    @State private var email = ""
    @State private var password = ""
    @State private var confirmPassword = ""
    @State private var isLoading = false
    @State private var showSuccess = false
    
    var body: some View {
        VStack(spacing: 24) {
            // Title
            VStack(spacing: 8) {
                Text("Create Account")
                    .font(.title2)
                    .fontWeight(.bold)
                
                Text("Join AgentLinker to connect your devices")
                    .font(.subheadline)
                    .foregroundColor(.secondary)
            }
            
            // Registration Form
            VStack(spacing: 16) {
                TextField("Full Name", text: $name)
                    .textFieldStyle(.roundedBorder)

                TextField("Email", text: $email)
                    .textFieldStyle(.roundedBorder)
                    .disableAutocorrection(true)
                
                SecureField("Password", text: $password)
                    .textFieldStyle(.roundedBorder)
                
                SecureField("Confirm Password", text: $confirmPassword)
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
                
                // Password requirements
                VStack(alignment: .leading, spacing: 4) {
                    PasswordRequirement(
                        text: "At least 6 characters",
                        isMet: password.count >= 6
                    )
                }
                .font(.caption2)
                .foregroundColor(.secondary)
                .frame(maxWidth: .infinity, alignment: .leading)
                
                Button(action: handleRegister) {
                    HStack {
                        if isLoading {
                            ProgressView()
                                .progressViewStyle(.circular)
                                .tint(.white)
                        }
                        Text(isLoading ? "Creating Account..." : "Create Account")
                            .fontWeight(.semibold)
                    }
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 12)
                }
                .buttonStyle(.borderedProminent)
                .controlSize(.large)
                .disabled(isLoading || !isFormValid)
                
                Button("Already have an account? Sign In") {
                    dismiss()
                }
                .buttonStyle(.plain)
                .foregroundColor(.accentColor)
                .font(.caption)
            }
            .padding(.horizontal)
            
            Spacer()
        }
        .frame(width: 400, height: 550)
        .background(Color(NSColor.windowBackgroundColor))
        .alert("Account Created!", isPresented: $showSuccess) {
            Button("Continue") {
                dismiss()
            }
        } message: {
            Text("Welcome to AgentLinker! You can now connect your devices.")
        }
        .onAppear {
            authManager.lastError = nil
        }
    }
    
    private var isFormValid: Bool {
        !name.isEmpty &&
        !email.isEmpty &&
        !password.isEmpty &&
        password == confirmPassword &&
        password.count >= 6
    }
    
    private func handleRegister() {
        guard password == confirmPassword else {
            authManager.lastError = "Passwords do not match"
            return
        }
        
        isLoading = true
        
        Task {
            let success = await authManager.register(
                email: email,
                password: password,
                name: name
            )
            
            await MainActor.run {
                isLoading = false
                
                if success {
                    showSuccess = true
                }
            }
        }
    }
}

// MARK: - Password Requirement Helper

struct PasswordRequirement: View {
    let text: String
    let isMet: Bool
    
    var body: some View {
        HStack(spacing: 6) {
            Image(systemName: isMet ? "checkmark.circle.fill" : "circle")
                .foregroundColor(isMet ? .green : .gray)
            
            Text(text)
        }
    }
}

#Preview {
    RegisterView()
        .environmentObject(AuthManager())
}
