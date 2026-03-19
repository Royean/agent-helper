# AgentLinker iOS 快捷指令

🍎 **一键启动 AgentLinker（无需打开 App）**

---

## 📱 创建快捷指令

### 步骤 1: 打开快捷指令 App

在 iPhone 上打开 **快捷指令** App

### 步骤 2: 创建新快捷指令

1. 点击右上角 **+** 号
2. 点击 **添加操作**
3. 搜索 **URL** 并添加
4. 搜索 **运行快捷指令** 或 **打开 App**

### 步骤 3: 配置快捷指令

**方案 A: 打开 Pythonista**

```
1. 添加操作：打开 App
2. 选择：Pythonista 3
3. 添加操作：运行快捷指令
4. 输入：运行 mobile_client.py
```

**方案 B: 使用 a-Shell**

```
1. 添加操作：打开 App
2. 选择：a-Shell
3. 添加文本操作
4. 输入：python mobile_client.py
```

---

## 🎯 快捷指令配置

### 基础版

```yaml
名称：启动 AgentLinker
图标：📱
颜色：蓝色

操作:
1. 打开 App → Pythonista 3
2. 等待 1 秒
3. 显示通知 → "AgentLinker 已启动"
```

### 高级版（带状态检查）

```yaml
名称：AgentLinker 控制
图标：🤖
颜色：紫色

操作:
1. 获取当前 WiFi 名称
2. 如果 WiFi 名称 包含 "Home"
   - 运行快捷指令 → 启动 AgentLinker
   - 显示通知 → "已连接家庭网络，启动 AgentLinker"
3. 否则
   - 显示通知 → "不在家庭网络，跳过启动"
```

---

## 📋 快捷指令代码

### 启动脚本

```python
# shortcut_launcher.py
import mobile_client
import asyncio
import console

# 显示启动画面
console.show_activity("正在启动 AgentLinker...")

# 配置服务端
SERVER_URL = "ws://43.98.243.80:8080/ws/client"

# 启动
async def start():
    client = mobile_client.MobileClient(SERVER_URL)
    
    if await client.connect():
        console.hide_activity()
        print("✅ AgentLinker 已启动")
        
        # 在后台运行
        await client.run()
    else:
        console.hide_activity()
        print("❌ 启动失败")

# 运行
asyncio.run(start())
```

---

## 🔔 添加自动化

### 自动化 1: 连接 WiFi 时启动

1. 打开 **自动化** 标签
2. 点击 **创建个人自动化**
3. 选择 **无线局域网**
4. 选择你的家庭 WiFi
5. 点击 **下一步**
6. 添加操作 → 运行快捷指令 → 启动 AgentLinker
7. 关闭 **运行前询问**

### 自动化 2: 打开特定 App 时启动

1. 创建个人自动化
2. 选择 **App**
3. 选择要触发的 App
4. 添加操作 → 运行快捷指令
5. 选择 AgentLinker 快捷指令

### 自动化 3: 定时启动

1. 创建个人自动化
2. 选择 **特定时间**
3. 设置时间（如每天早上 8 点）
4. 添加操作 → 运行快捷指令

---

## 🎨 自定义图标

### 更改快捷指令图标

1. 长按快捷指令
2. 选择 **详情**
3. 点击 **图标**
4. 选择喜欢的图标和颜色

### 推荐图标

| 功能 | 图标 | 颜色 |
|------|------|------|
| 启动 | 📱 | 蓝色 |
| 控制 | 🤖 | 紫色 |
| 状态 | 📊 | 绿色 |
| 停止 | ⏹️ | 红色 |

---

## 🔗 分享快捷指令

### 导出快捷指令

1. 长按快捷指令
2. 选择 **分享**
3. 选择 **导出文件**
4. 保存为 `.shortcut` 文件

### 导入快捷指令

1. 接收 `.shortcut` 文件
2. 点击文件
3. 点击 **获取快捷指令**
4. 添加到库

---

## 📊 使用场景

### 场景 1: 回家自动启动

```
触发条件：连接家庭 WiFi
动作：启动 AgentLinker
通知：显示"欢迎回家，AgentLinker 已启动"
```

### 场景 2: 睡前关闭

```
触发条件：晚上 11 点
动作：停止 AgentLinker
通知：显示"晚安，AgentLinker 已停止"
```

### 场景 3: Siri 语音控制

```
"Hey Siri, 启动 AgentLinker"
→ 运行快捷指令
→ 启动 AgentLinker
```

---

## 🐛 故障排查

### 问题 1: 快捷指令无法运行

**解决**:
- 检查权限设置
- 确保 Pythonista/a-Shell 已安装
- 重启快捷指令 App

### 问题 2: 后台被杀死

**解决**:
- 关闭后台 App 刷新限制
- 在设置中允许后台运行
- 使用前台服务

### 问题 3: 网络问题

**解决**:
- 检查 WiFi 连接
- 确认服务端地址正确
- 测试网络连接

---

## 💡 高级技巧

### 1. 组合快捷指令

```
启动 AgentLinker
↓
检查连接状态
↓
如果在线 → 显示成功通知
↓
如果离线 → 尝试重连
```

### 2. 条件启动

```python
import requests

# 检查是否在家
def is_home():
    # 检查 IP 地址
    response = requests.get('http://ip-api.com/json')
    data = response.json()
    return data['city'] == 'Your City'

# 只有在家时才启动
if is_home():
    start_agentlinker()
```

### 3. 状态监控

```python
# 定期检查 AgentLinker 状态
import time

while True:
    status = check_agentlinker_status()
    if not status:
        restart_agentlinker()
    time.sleep(300)  # 每 5 分钟检查一次
```

---

## 📚 参考资料

- [iOS 快捷指令官方文档](https://support.apple.com/zh-cn/guide/shortcuts/welcome/ios)
- [Pythonista 文档](http://omz-software.com/pythonista3/docs/)
- [a-Shell 文档](https://holzschu.github.io/a-Shell_iOS/)

---

**创建时间**: 2026-03-20  
**版本**: 1.0.0  
**适用**: iOS 13+
