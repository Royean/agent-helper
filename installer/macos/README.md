# AgentLinker macOS 安装指南

🍎 在 macOS 上部署 AgentLinker 被控端

---

## 📋 系统要求

- **macOS 版本:** 10.15 (Catalina) 或更高
- **架构:** Intel 或 Apple Silicon (M1/M2/M3)
- **Python:** 3.8+ (会自动安装)
- **权限:** 需要管理员权限 (sudo)

---

## 🚀 快速安装

### 方法一：一键安装（推荐）

```bash
# 下载安装脚本并运行
curl -fsSL https://raw.githubusercontent.com/Royean/AgentLinker/master/installer/macos/install.sh | sudo bash
```

### 方法二：手动安装

```bash
# 1. 下载仓库
git clone https://github.com/Royean/AgentLinker.git
cd AgentLinker

# 2. 运行安装脚本
sudo bash installer/macos/install.sh
```

---

## ⚙️ 配置

安装完成后，编辑配置文件：

```bash
sudo nano /etc/agentlinker/config.json
```

修改以下内容：

```json
{
  "device_id": "mac-mini-001",
  "device_name": "我的 Mac",
  "token": "ah_device_token_change_in_production",
  "server_url": "ws://43.159.61.30:8080/ws/client"
}
```

**重要：**
- `server_url` 改为你的服务端地址
- `token` 需要与服务端配置一致

---

## 🎯 启动服务

### 启动 AgentLinker

```bash
# 启动服务
sudo launchctl start com.agentlinker.client

# 查看状态
sudo launchctl list | grep agentlinker

# 查看日志
tail -f /var/log/agentlinker/agentlinker.log
```

### 查看配对密钥

启动后，日志中会显示配对密钥：

```
==================================================
🔐 配对密钥已生成！
   设备 ID: mac-mini-001
   配对密钥：ABCD1234
   将此密钥提供给主控端进行配对
==================================================
```

---

## 🎮 主控端连接

在另一台机器上启动主控端：

```bash
agentlinker --mode controller --server ws://43.159.61.30:8080/ws/controller
```

配对设备：

```
[controller]> pair mac-mini-001 ABCD1234
```

---

## 🔧 常用命令

### 服务管理

```bash
# 启动服务
sudo launchctl start com.agentlinker.client

# 停止服务
sudo launchctl stop com.agentlinker.client

# 重启服务
sudo launchctl stop com.agentlinker.client
sudo launchctl start com.agentlinker.client

# 开机自启（已自动配置）
sudo launchctl load -w /Library/LaunchDaemons/com.agentlinker.client.plist

# 卸载服务
sudo launchctl unload -w /Library/LaunchDaemons/com.agentlinker.client.plist
```

### 日志查看

```bash
# 查看运行日志
tail -f /var/log/agentlinker/agentlinker.log

# 查看错误日志
tail -f /var/log/agentlinker/agentlinker.error.log

# 使用 Console.app 查看
# 打开 Console.app，搜索 "agentlinker"
```

---

## 🧪 本地测试

### 测试服务端连接

```bash
# 1. 确保服务端正在运行

# 2. 手动运行客户端测试
cd /opt/agentlinker
source venv/bin/activate
python3 client/cli.py --config /etc/agentlinker/config.json
```

### 测试指令执行

```bash
# 测试系统信息
python3 -c "
import sys
sys.path.insert(0, 'client/core')
from core import Executor
result = Executor.execute('system.info', {})
print(result)
"

# 测试 shell 命令
python3 -c "
import sys
sys.path.insert(0, 'client/core')
from core import Executor
result = Executor.execute('shell.exec', {'cmd': 'uname -a'})
print(result['data']['stdout'])
"
```

---

## 🍎 macOS 特定功能

### 获取应用程序列表

```python
import sys
sys.path.insert(0, '/opt/agentlinker/client')
from platform.macos import list_applications

apps = list_applications()
for app in apps[:10]:
    print(app['name'])
```

### 执行 AppleScript

```python
from platform.macos import execute_applescript

# 获取当前播放的音乐
result = execute_applescript('tell app "System Events" to get the name of every process')
print(result)
```

### 获取 WiFi 信息

```python
from platform.macos import get_wifi_info

wifi = get_wifi_info()
print(f"SSID: {wifi.get('ssid')}")
```

---

## ❓ 常见问题

### Q: 安装失败，提示权限错误
**A:** 确保使用 `sudo` 运行安装脚本

### Q: 服务无法启动
**A:** 检查日志文件：
```bash
cat /var/log/agentlinker/agentlinker.error.log
```

### Q: 配对密钥不显示
**A:** 确保服务端正在运行，并且网络连接正常

### Q: macOS 弹窗要求权限
**A:** macOS 可能会要求终端/自动化权限，在 系统设置 → 隐私与安全性 中授权

---

## 📦 卸载

```bash
# 1. 停止服务
sudo launchctl unload -w /Library/LaunchDaemons/com.agentlinker.client.plist

# 2. 删除文件
sudo rm -rf /opt/agentlinker
sudo rm -rf /etc/agentlinker
sudo rm -rf /var/log/agentlinker
sudo rm -f /Library/LaunchDaemons/com.agentlinker.client.plist
sudo rm -f /usr/local/bin/agentlinker

echo "AgentLinker 已卸载"
```

---

## 📝 下一步

1. ✅ 安装完成
2. ⏳ 配置服务端地址
3. ⏳ 启动服务
4. ⏳ 使用主控端配对
5. ⏳ 开始远程控制

---

## 🔗 相关文档

- [服务端部署指南](../../server/README.md)
- [Linux 安装指南](../linux/README.md)
- [Windows 安装指南](../windows/README.md) (开发中)
- [主控端使用指南](../../client/README.md)

---

**有问题？** 提交 Issue 或查看 [GitHub Discussions](https://github.com/Royean/AgentLinker/discussions)
