# AgentLinker for macOS

🍎 **Native macOS SwiftUI Application**

A modern, native macOS client for AgentLinker - AI Agent remote control system.

## ✨ Features

- 🎨 **Native SwiftUI UI** - Beautiful, modern interface following macOS design guidelines
- 🌓 **Dark Mode Support** - Automatically adapts to system appearance
- 📍 **Menu Bar App** - Quick access from your menu bar
- 🔗 **Easy Pairing** - One-click copy pairing key
- 📊 **Real-time Status** - Live connection and device status
- ⚡ **Auto-reconnect** - Automatically reconnects on connection loss

## 🚀 Quick Start

### Prerequisites

- macOS 13.0 or later
- Xcode 15.0 or later
- Swift 5.9 or later

### Build & Run

```bash
# Navigate to macOS app directory
cd macos

# Build with Swift Package Manager
swift build

# Run the app
swift run AgentLinker
```

### Open in Xcode

```bash
# Generate Xcode project
swift package generate-xcodeproj

# Or open Package.swift directly in Xcode 15+
open Package.swift
```

## 📦 Installation

### Option 1: Build from Source

```bash
cd macos
swift build -c release

# The app will be in .build/release/AgentLinker
```

### Option 2: Create DMG (Coming Soon)

```bash
# This will be added in packaging/macos/
./create-dmg.sh
```

### Option 3: Homebrew (Coming Soon)

```bash
brew install --cask agentlinker
```

## 🎯 Usage

### Main Window

1. Launch AgentLinker from Applications or command line
2. Your device ID and pairing key are automatically generated
3. Click "Copy Key" to copy the full pairing string
4. Share the pairing key with your controller to pair devices

### Menu Bar

- AgentLinker lives in your menu bar for quick access
- Click the icon to see status and copy pairing key
- Right-click for quick actions

### Pairing with Controller

```bash
# On your controller device
python3 client/controller.py --server ws://43.98.243.80:8080/ws/controller

# Pair with this device
[controller]> pair <device_id> <pairing_key>
```

## 🏗️ Architecture

```
macos/
├── Sources/
│   ├── AgentLinkerApp.swift    # App entry point
│   ├── Models/
│   │   ├── Device.swift        # Device data models
│   │   └── Messages.swift      # WebSocket message types
│   ├── Services/
│   │   ├── WebSocketManager.swift  # WebSocket connection
│   │   └── DeviceManager.swift     # Device state management
│   ├── Views/
│   │   ├── ContentView.swift       # Main window
│   │   ├── MenuBarView.swift       # Menu bar interface
│   │   └── SettingsView.swift      # Settings panel
│   └── Resources/
├── Package.swift               # Swift Package Manager config
└── README.md                   # This file
```

## 🔧 Configuration

The app uses standard macOS UserDefaults for configuration:

- `device_id` - Unique device identifier
- `device_name` - Human-readable device name
- `server_url` - WebSocket server URL

## 🛣️ Roadmap

- [ ] Native notifications for controller commands
- [ ] System service integration (launchd)
- [ ] Notarization for Gatekeeper
- [ ] Sparkle auto-updates
- [ ] Touch Bar support
- [ ] Apple Silicon native optimization

## 📝 Requirements

- **Minimum OS:** macOS 13.0
- **Recommended OS:** macOS 14.0+
- **Dependencies:** Starscream (WebSocket library)

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

MIT License - same as the main AgentLinker project.

## 🔗 Links

- [Main Repository](https://github.com/Royean/AgentLinker)
- [Documentation](https://github.com/Royean/AgentLinker/tree/master/docs)
- [Issues](https://github.com/Royean/AgentLinker/issues)

---

**Made with ❤️ for macOS**
