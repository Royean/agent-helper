# AgentLinker macOS 安装指南

🍎 在 macOS 上安装和使用 AgentLinker

---

## 📦 安装方式

### 方式一：一键安装脚本（推荐）

```bash
# 下载安装脚本
curl -fsSL https://github.com/Royean/AgentLinker/raw/master/installer/macos/install.sh -o install.sh

# 运行安装
sudo bash install.sh
```

### 方式二：DMG 安装包

1. 下载 DMG 文件：[AgentLinker_2.0.0_macOS.dmg](https://github.com/Royean/AgentLinker/releases/latest)
2. 双击打开 DMG
3. 将 AgentLinker.app 拖到 /Applications
4. 运行应用程序

### 方式三：Homebrew（待发布）

```bash
# 添加 tap
brew tap Royean/agentlinker

# 安装
brew install --cask agentlinker
```

---

## ⚙️ 配置

安装完成后，编辑配置文件：

```bash
sudo nano /etc/agentlinker/config.json
```

配置示例：

```json
{
  "device_id": "my-macbook-pro",
  "device_name": "我的 MacBook Pro",
  "token": "ah_device_token_change_in_production",
  "server_url": "wss://your-server.com/ws/client",
  "reconnect_interval": 5,
  "heartbeat_interval": 30
}
```

**重要配置项：**
- `device_id`: 设备唯一标识（可留空自动生成）
- `device_name`: 设备名称（用于显示）
- `token`: 设备认证 Token（需与服务端一致）
- `server_url`: 服务端 WebSocket 地址

---

## 🚀 启动服务

### 使用 launchd（系统服务）

```bash
# 启动服务
sudo launchctl start com.agentlinker.client

# 停止服务
sudo launchctl stop com.agentlinker.client

# 重启服务
sudo launchctl kickstart -k system/com.agentlinker.client

# 查看服务状态
launchctl list | grep agentlinker

# 查看日志
tail -f /var/log/agentlinker/agentlinker.log
```

### 使用命令行

```bash
# 被控端模式
agentlinker --mode client

# 主控端模式
agentlinker --mode controller

# 显示配对二维码
agentlinker-show-qr
```

---

## 📱 配对设备

### 方式一：二维码配对

1. 在被控端显示二维码：
   ```bash
   agentlinker-show-qr
   ```

2. 在主控端扫描：
   ```bash
   agentlinker --mode controller
   [controller]> qr-pair
   ```

### 方式二：手动配对

```bash
agentlinker --mode controller
[controller]> pair <device_id> <pairing_key>
```

### 方式三：局域网发现

```bash
agentlinker --mode controller
[controller]> discover
```

---

## 🔧 故障排除

### 服务无法启动

```bash
# 检查配置文件
sudo cat /etc/agentlinker/config.json

# 检查日志
sudo tail -f /var/log/agentlinker/agentlinker.log

# 重新加载服务
sudo launchctl unload -w /Library/LaunchDaemons/com.agentlinker.client.plist
sudo launchctl load -w /Library/LaunchDaemons/com.agentlinker.client.plist
```

### 权限问题

```bash
# 修复权限
sudo chown -R root:wheel /opt/agentlinker
sudo chmod -R 755 /opt/agentlinker
sudo chown root:wheel /Library/LaunchDaemons/com.agentlinker.client.plist
sudo chmod 644 /Library/LaunchDaemons/com.agentlinker.client.plist
```

### Python 环境问题

```bash
# 重新创建虚拟环境
cd /opt/agentlinker
sudo rm -rf venv
sudo python3 -m venv venv
source venv/bin/activate
sudo pip install -r client/requirements.txt
```

### 网络连接问题

```bash
# 检查防火墙
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate

# 添加 Python 到防火墙白名单
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /opt/agentlinker/venv/bin/python3

# 测试连接
curl -v https://your-server.com/health
```

---

## 📊 系统要求

- **操作系统**: macOS 10.15 (Catalina) 或更高版本
- **架构**: Intel 或 Apple Silicon (M1/M2/M3)
- **Python**: 3.8 或更高版本
- **磁盘空间**: 至少 500MB
- **网络**: 需要访问服务端

---

## 🗑️ 卸载

```bash
# 停止服务
sudo launchctl bootout system/com.agentlinker.client

# 卸载服务文件
sudo rm /Library/LaunchDaemons/com.agentlinker.client.plist

# 删除安装目录
sudo rm -rf /opt/agentlinker

# 删除配置和日志
sudo rm -rf /etc/agentlinker
sudo rm -rf /var/log/agentlinker

# 删除命令行工具
sudo rm /usr/local/bin/agentlinker
sudo rm /usr/local/bin/agentlinker-show-qr

echo "✅ AgentLinker 已卸载"
```

---

## 📚 更多信息

- **GitHub**: https://github.com/Royean/AgentLinker
- **文档**: https://github.com/Royean/AgentLinker/tree/master/docs
- **问题反馈**: https://github.com/Royean/AgentLinker/issues

---

## 🔐 安全提示

1. **保护配置文件** - 包含敏感 Token 信息
2. **使用 HTTPS/WSS** - 生产环境务必使用加密连接
3. **定期更新 Token** - 建议定期更换认证 Token
4. **防火墙配置** - 仅开放必要的端口
5. **日志审计** - 定期检查日志文件

---

**版本**: 2.0.0  
**更新日期**: 2026-03-19  
**支持**: macOS 10.15+
