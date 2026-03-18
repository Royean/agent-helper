# AgentLinker 安装指南

🎯 **最简单的安装方式，3 步完成！**

---

## 🍎 macOS 用户（推荐）

### 方式一：一键安装（最简单）⭐

打开终端，复制粘贴：

```bash
curl -fsSL https://raw.githubusercontent.com/Royean/AgentLinker/master/install.sh | bash
```

**安装后：**
1. 打开 `~/Applications/AgentLinker.app`
2. 应用会自动启动
3. 显示设备 ID 和配对密钥 ✅
4. 点击"复制配对密钥"按钮

**就这么简单！不需要任何配置！**

---

### 方式二：Homebrew

```bash
# 安装
brew install https://raw.githubusercontent.com/Royean/AgentLinker/master/packaging/homebrew/agentlinker.rb

# 运行（图形界面）
agentlinker --gui

# 运行（后台）
agentlinker --mode client
```

---

### 方式三：手动安装

```bash
# 下载
git clone https://github.com/Royean/AgentLinker.git
cd AgentLinker

# 安装依赖
python3 -m venv venv
source venv/bin/activate
pip install -r client/requirements.txt

# 运行图形界面
python3 client/app.py
```

---

## 🐧 Linux 用户

### 一键安装

```bash
curl -fsSL https://raw.githubusercontent.com/Royean/AgentLinker/master/install.sh | sudo bash
```

### 手动安装

```bash
# 下载
cd /opt
git clone https://github.com/Royean/AgentLinker.git
cd AgentLinker

# 安装依赖
python3 -m venv venv
source venv/bin/activate
pip install -r client/requirements.txt

# 运行
python3 client/cli.py --mode client
```

---

## 🪟 Windows 用户

开发中，敬请期待！

临时方案：使用 WSL2 安装 Linux 版本

---

## 📋 安装后做什么？

### 1. 查看设备信息

打开应用后，会自动显示：
- **设备 ID**: 唯一标识你的设备
- **配对密钥**: 8 位动态码（每小时更新）

### 2. 复制配对密钥

点击"复制配对密钥"按钮，或手动记录

### 3. 在控制器端配对

```bash
# 在控制器机器上
agentlinker --mode controller --server ws://43.98.243.80:8080/ws/controller

# 配对
[controller]> pair <你的设备 ID> <配对密钥>
```

### 4. 开始控制

```bash
# 执行命令
[controller]> exec <设备 ID> uname -a

# 获取信息
[controller]> info <设备 ID>
```

---

## ⚙️ 自定义配置

### 修改设备 ID

1. 打开应用
2. 菜单：文件 → 修改设备 ID
3. 输入新的设备 ID
4. 保存

### 修改服务器

默认服务器：`ws://43.98.243.80:8080/ws/client`

如果要使用自己的服务器：
1. 菜单：文件 → 修改服务器
2. 输入新的服务器地址
3. 保存并重启

---

## 🔧 常见问题

### Q: 应用打不开？
**A:** macOS 可能会提示"无法验证开发者"
- 解决方法：系统设置 → 隐私与安全性 → 仍要打开

### Q: 连接失败？
**A:** 检查：
1. 服务器地址是否正确
2. 防火墙是否开放 8080 端口
3. 网络是否通畅

### Q: 配对密钥不显示？
**A:** 确保：
1. 应用已启动
2. 服务器正在运行
3. 网络连接正常

### Q: 如何开机自启？
**A:** 
- macOS: `系统设置 → 通用 → 登录项` 添加应用
- Linux: `systemctl enable agentlinker`

---

## 📞 需要帮助？

- 📖 文档：https://github.com/Royean/AgentLinker
- 💬 讨论：https://github.com/Royean/AgentLinker/discussions
- 🐛 问题：https://github.com/Royean/AgentLinker/issues

---

**🎉 享受跨设备控制的乐趣！**
