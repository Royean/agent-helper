//
//  AuthManager.swift
//  AgentLinker macOS
//

import Foundation
import Security
import Combine

class AuthManager: ObservableObject {
    @Published var isAuthenticated = false
    @Published var currentUser: User?
    @Published var lastError: String?
    
    private let keychainService = "com.agentlinker.macos"
    private let userDefaultsKey = "com.agentlinker.user"
    
    static let shared = AuthManager()
    
    init() {
        checkExistingSession()
    }
    
    // MARK: - Public Methods
    
    func login(email: String, password: String) async -> Bool {
        // Simulate login - replace with actual API call
        try? await Task.sleep(nanoseconds: 500_000_000) // 500ms delay
        
        // Validate credentials
        guard !email.isEmpty && !password.isEmpty else {
            lastError = "Email and password are required"
            return false
        }
        
        guard isValidEmail(email) else {
            lastError = "Invalid email format"
            return false
        }
        
        guard password.count >= 6 else {
            lastError = "Password must be at least 6 characters"
            return false
        }
        
        // Create user
        let user = User(
            id: UUID().uuidString,
            email: email,
            name: email.components(separatedBy: "@").first ?? "User",
            createdAt: Date()
        )
        
        // Store credentials in Keychain
        let success = storeCredentials(email: email, password: password)
        guard success else {
            lastError = "Failed to store credentials"
            return false
        }
        
        // Store user session
        storeUserSession(user: user)
        
        await MainActor.run {
            self.currentUser = user
            self.isAuthenticated = true
            self.lastError = nil
        }
        
        print("✅ User logged in: \(email)")
        return true
    }
    
    func register(email: String, password: String, name: String) async -> Bool {
        // Simulate registration - replace with actual API call
        try? await Task.sleep(nanoseconds: 500_000_000)
        
        guard !email.isEmpty && !password.isEmpty && !name.isEmpty else {
            lastError = "All fields are required"
            return false
        }
        
        guard isValidEmail(email) else {
            lastError = "Invalid email format"
            return false
        }
        
        guard password.count >= 6 else {
            lastError = "Password must be at least 6 characters"
            return false
        }
        
        // Create user
        let user = User(
            id: UUID().uuidString,
            email: email,
            name: name,
            createdAt: Date()
        )
        
        // Store credentials
        let success = storeCredentials(email: email, password: password)
        guard success else {
            lastError = "Failed to store credentials"
            return false
        }
        
        storeUserSession(user: user)
        
        await MainActor.run {
            self.currentUser = user
            self.isAuthenticated = true
            self.lastError = nil
        }
        
        print("✅ User registered: \(email)")
        return true
    }
    
    func logout() {
        // Clear Keychain
        deleteCredentials()
        
        // Clear session
        UserDefaults.standard.removeObject(forKey: userDefaultsKey)
        
        DispatchQueue.main.async {
            self.currentUser = nil
            self.isAuthenticated = false
            self.lastError = nil
        }
        
        print("👋 User logged out")
    }
    
    func checkExistingSession() {
        // Check if user session exists
        if let data = UserDefaults.standard.data(forKey: userDefaultsKey),
           let user = try? JSONDecoder().decode(User.self, from: data) {
            // Verify credentials still exist in Keychain
            if let _ = loadCredentials() {
                DispatchQueue.main.async {
                    self.currentUser = user
                    self.isAuthenticated = true
                }
                print("✅ Session restored for: \(user.email)")
                return
            }
        }
        
        // No valid session
        DispatchQueue.main.async {
            self.isAuthenticated = false
            self.currentUser = nil
        }
    }
    
    // MARK: - Keychain Operations
    
    private func storeCredentials(email: String, password: String) -> Bool {
        // Delete existing credentials first
        deleteCredentials()
        
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: keychainService,
            kSecAttrAccount as String: email,
            kSecValueData as String: password.data(using: .utf8) as Any,
            kSecAttrAccessible as String: kSecAttrAccessibleWhenUnlocked
        ]
        
        let status = SecItemAdd(query as CFDictionary, nil)
        return status == errSecSuccess
    }
    
    private func loadCredentials() -> (email: String, password: String)? {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: keychainService,
            kSecReturnAttributes as String: true,
            kSecReturnData as String: true,
            kSecMatchLimit as String: kSecMatchLimitOne
        ]
        
        var result: AnyObject?
        let status = SecItemCopyMatching(query as CFDictionary, &result)
        
        guard status == errSecSuccess,
              let dict = result as? [String: Any],
              let account = dict[kSecAttrAccount as String] as? String,
              let data = dict[kSecValueData as String] as? Data,
              let password = String(data: data, encoding: .utf8) else {
            return nil
        }
        
        return (email: account, password: password)
    }
    
    private func deleteCredentials() {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: keychainService
        ]
        
        SecItemDelete(query as CFDictionary)
    }
    
    // MARK: - Session Storage
    
    private func storeUserSession(user: User) {
        if let data = try? JSONEncoder().encode(user) {
            UserDefaults.standard.set(data, forKey: userDefaultsKey)
        }
    }
    
    // MARK: - Helpers
    
    private func isValidEmail(_ email: String) -> Bool {
        let emailRegex = #"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"#
        return NSPredicate(format: "SELF MATCHES %@", emailRegex).evaluate(with: email)
    }
}

// MARK: - User Model

struct User: Codable, Equatable {
    let id: String
    let email: String
    let name: String
    let createdAt: Date
}
