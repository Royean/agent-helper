# AgentLinker

🤖 **跨平台 AI Agent 远程控制系统**

一套轻量、高权限、内网穿透、跨平台的远程接入系统，让任何 AI Agent 可以跨网、安全、高权限控制 Linux、macOS、Windows 主机。

[![Version](https://img.shields.io/github/v/release/Royean/AgentLinker)](https://github.com/Royean/AgentLinker/releases)
[![License](https://img.shields.io/github/license/Royean/AgentLinker)](LICENSE)
[![Stars](https://img.shields.io/github/stars/Royean/AgentLinker)](https://github.com/Royean/AgentLinker/stargazers)

---

## ✨ 特性

- 🖥️ **跨平台支持** - Linux、macOS、Windows 全支持
- 📦 **一键安装** - DMG / EXE / Homebrew / 一键脚本
- 🎨 **现代化界面** - 深色模式 / 系统托盘 / 专业图标
- 🎮 **一对多控制** - 一台主机可控制多台远程设备
- 🔐 **安全配对** - 动态配对密钥，持久化绑定
- 🌐 **内网穿透** - 无需公网 IP，主动连接服务端
- 🔒 **实时状态** - 设备在线/离线状态实时同步

---

## 🚀 快速开始

### 方式一：Windows 一键安装（最简单）⭐

**打开 PowerShell（管理员），复制粘贴：**

```powershell
iwr https://raw.githubusercontent.com/Royean/AgentLinker/master/scripts/install.ps1 -useb | iex
```

**安装后：**
1. 双击桌面上的 `AgentLinker` 图标
2. 应用会自动启动并显示设备 ID 和配对密钥 ✅
3. 点击"📋 复制密钥"即可使用

**就这么简单！不需要任何配置！**

---

### 方式二：macOS 一键安装

打开终端，复制粘贴：

```bash
curl -fsSL https://raw.githubusercontent.com/Royean/AgentLinker/master/install.sh | bash
```

**安装后：**
1. 打开 `~/Applications/AgentLinker.app`
2. 应用会自动启动并显示设备 ID 和配对密钥 ✅
3. 点击"复制配对密钥"即可使用

**就这么简单！不需要任何配置！**

---

### 方式二：Homebrew

```bash
# 安装
brew install https://raw.githubusercontent.com/Royean/AgentLinker/master/packaging/homebrew/agentlinker.rb

# 运行（图形界面）
agentlinker --gui

# 运行（菜单栏应用）
agentlinker --menubar

# 运行（后台服务）
agentlinker --mode client
```

---

### 方式三：手动部署服务端

```bash
cd server

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 启动服务端
python main.py
```

服务端默认监听 `0.0.0.0:8080`

---

## 📱 客户端使用

### 🪟 Windows 用户

#### 图形界面应用

**安装后自动创建桌面快捷方式**

1. 双击桌面上的 `AgentLinker` 图标
2. 应用会自动显示设备 ID 和配对密钥
3. 点击"📋 复制密钥"即可使用

#### 系统托盘

- 应用会在系统托盘显示图标 🤖
- **右键点击图标**：
  - 复制配对密钥
  - 显示/隐藏窗口
  - 启动/停止服务
  - 退出程序

#### 开机自启

- 安装时可选择开机自动启动
- 或在设置中勾选"开机自动启动"

---

### 🍎 macOS 用户

#### 图形界面应用

```bash
# 打开应用
open ~/Applications/AgentLinker.app

# 或命令行启动
python3 client/app.py
```

#### 菜单栏应用（推荐）

```bash
# 安装依赖
pip install rumps

# 启动菜单栏应用
python3 client/menubar_app.py
```

菜单栏应用会显示在系统菜单栏，随时查看状态和复制配对密钥！

---

### 🐧 Linux 用户

```bash
# 图形界面
python3 client/app.py

# 命令行
python3 client/cli.py --mode client
```

---

## 🎮 控制器使用

```bash
# 启动控制器
python3 client/controller.py --server ws://43.98.243.80:8080/ws/controller

# 配对设备
[controller]> pair <device_id> <pairing_key>

# 执行命令
[controller]> exec <device_id> uname -a

# 获取信息
[controller]> info <device_id>

# 列出设备
[controller]> list
```

---

## 📋 支持的指令

| Action | 描述 | 参数 |
|--------|------|------|
| `system.info` | 获取系统信息 | - |
| `shell.exec` | 执行 shell 命令 | `cmd`, `timeout`, `cwd` |
| `file.list` | 列目录 | `path` |
| `file.read` | 读文件 | `path`, `offset`, `limit` |
| `file.write` | 写文件 | `path`, `content`, `encoding` |
| `file.delete` | 删除文件/目录 | `path`, `recursive` |
| `process.list` | 进程列表 | - |
| `process.kill` | 杀死进程 | `pid`, `signal` |
| `service.operate` | 系统服务操作 | `service`, `operation` |

---

## 🎨 v2.1.0 新功能

### 现代化界面
- ✨ 全新的卡片式布局
- 🌓 深色模式支持（自动检测系统主题）
- 🎨 专业的应用图标
- 📱 实时状态指示器

### 菜单栏应用（macOS）
- 📍 系统菜单栏图标
- ⚡ 快速复制配对密钥
- 🔔 通知支持
- ▶️ 一键启动/停止

### 用户体验优化
- 📋 配对密钥自动复制
- 🪟 窗口自动居中
- 🎯 改进的按钮和菜单
- ℹ️ 关于对话框

---

## 🏗️ 架构

```
┌─────────────────┐      WebSocket      ┌─────────────────┐
│  控制器         │ ◄─────────────────► │   云端服务端     │
│  (任何地方)     │    ws://server:8080    │  (中转 + 鉴权)   │
└─────────────────┘                     └─────────────────┘
                                               ▲
                                               │ WebSocket
                                               ▼
                                        ┌──────────────┐
                                        │  被控设备     │
                                        │ Linux/macOS  │
                                        └──────────────┘
```

---

## 🔐 安全配置

### Token 配置

服务端使用环境变量配置 Token：

```bash
export SERVER_AGENT_TOKEN="your_secure_token"
export LINUX_DEVICE_TOKEN="device_token"
```

### 生产环境建议

- 使用随机生成的长 Token（32 位以上）
- 使用 HTTPS/WSS 加密传输
- 配置防火墙限制服务端访问 IP
- 定期更换 Token

---

## 📁 项目结构

```
AgentLinker/
├── server/               # 服务端
│   ├── main.py          # FastAPI + WebSocket
│   └── requirements.txt
├── client/               # 客户端
│   ├── app.py           # 🎨 图形界面客户端
│   ├── menubar_app.py   # 📍 菜单栏应用 (macOS)
│   ├── controller.py    # 🎮 主控端
│   ├── cli.py           # 💻 命令行工具
│   └── core/            # 🔧 核心逻辑
├── packaging/            # 📦 打包工具
│   ├── macos/
│   └── homebrew/
├── assets/               # 🖼️ 资源文件
│   └── icon.png
├── install.sh            # 🚀 一键安装
├── README.md             # 📖 本文档
├── CHANGELOG.md          # 📝 更新日志
└── ROADMAP.md            # 🗺️ 路线图
```

---

## 🛣️ 路线图

### v2.1.0 ✅
- [x] 现代化界面
- [x] 深色模式
- [x] 菜单栏应用 (macOS)
- [x] 应用图标

### v2.2.0 ✅
- [x] Windows 完整支持
- [x] 一键安装脚本 (PowerShell)
- [x] 系统托盘 (Windows)
- [x] PyInstaller 打包
- [ ] 文件传输功能 (下一步)
- [ ] 批量命令执行 (下一步)

### v2.3.0 (计划)
- [ ] TLS/SSL 加密
- [ ] 设备证书认证
- [ ] 操作审计日志
- [ ] Web 控制台

---

## 📞 需要帮助？

- 📖 [安装指南](INSTALL_GUIDE.md)
- 📝 [更新日志](CHANGELOG.md)
- 🗺️ [路线图](ROADMAP.md)
- 🐛 [提交 Issue](https://github.com/Royean/AgentLinker/issues)
- 💬 [讨论区](https://github.com/Royean/AgentLinker/discussions)

---

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

---

## 🎉 致谢

感谢所有贡献者和用户！

**Made with ❤️ by AgentLinker Team**
