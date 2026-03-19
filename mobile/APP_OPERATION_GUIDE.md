# AgentLinker 手机 APP 操作指南

📱 **通过命令行控制和操作手机 APP**

---

## 🎯 能力说明

### ✅ 可以做到的

| 操作 | 实现方式 | 难度 |
|------|----------|------|
| **打开 APP** | URL Scheme | ⭐ 简单 |
| **传递数据** | URL 参数 | ⭐⭐ 中等 |
| **触发快捷指令** | 文件监控 | ⭐⭐ 中等 |
| **发送消息** | 快捷指令 + 辅助 | ⭐⭐⭐ 较难 |

### ❌ 做不到的（系统限制）

| 操作 | 原因 |
|------|------|
| 模拟点击/滑动 | iOS 安全限制 |
| 读取 APP 内容 | 沙盒隔离 |
| 后台自动操作 | 需要越狱 |
| 完全自动化 | 需要辅助功能权限 |

---

## 📋 方案对比

### 方案 1: URL Scheme（最简单）⭐

**原理**: 通过特殊 URL 打开 APP

**优点**:
- ✅ 简单，一行命令
- ✅ 无需额外配置
- ✅ 支持大部分 APP

**缺点**:
- ❌ 只能打开 APP
- ❌ 无法操作 APP 内部

**示例**:
```bash
# 打开微信
exec iPhone-001 app.open "weixin://"

# 打开支付宝
exec iPhone-001 app.open "alipay://"

# 打开淘宝商品
exec iPhone-001 app.open "taobao://item.taobao.com/item.htm?id=123456"
```

---

### 方案 2: 快捷指令 + 文件监控（推荐）⭐⭐⭐

**原理**: AgentLinker 创建触发文件 → 快捷指令监控 → 执行操作

**优点**:
- ✅ 可以执行复杂操作
- ✅ 支持多个 APP
- ✅ 可以传递参数

**缺点**:
- ❌ 需要配置快捷指令
- ❌ 部分操作需要用户确认

**架构**:
```
AgentLinker (云端)
    ↓
创建触发文件 (/tmp/triggers/xxx.txt)
    ↓
iOS 快捷指令 (监控文件)
    ↓
执行操作 (打开 APP/发送消息等)
```

---

## 🔧 完整实现

### 步骤 1: 在 iPhone 上创建快捷指令

#### 快捷指令 1: 打开 APP

```yaml
名称：AgentLinker - 打开 APP
隐私：家庭
图标：📱

快捷指令流程:
1. 获取文件 [/tmp/agentlinker_triggers/open_app.txt]
2. 如果文件存在
   - 读取文件内容
   - 打开 URL [文件内容]
   - 删除文件
3. 显示通知 ["已打开 APP"]
```

#### 快捷指令 2: 发送微信

```yaml
名称：AgentLinker - 发送微信
隐私：家庭
图标：💬

快捷指令流程:
1. 获取文件 [/tmp/agentlinker_triggers/send_wechat.json]
2. 如果文件存在
   - 读取文件内容 (JSON)
   - 解析 contact 和 message
   - 打开 URL [weixin://]
   - 等待 1 秒
   - 显示文本 ["联系人：{contact}\n消息：{message}"]
   - 删除文件
3. 显示通知 ["已打开微信，请手动发送"]
```

#### 快捷指令 3: 运行任意快捷指令

```yaml
名称：AgentLinker - 运行快捷指令
隐私：家庭
图标：⚡

快捷指令流程:
1. 获取文件 [/tmp/agentlinker_triggers/shortcut_*.json]
2. 如果文件存在
   - 从文件名提取快捷指令名称
   - 运行快捷指令 [名称]
   - 删除文件
```

---

### 步骤 2: 通过 AgentLinker 触发

#### Python 代码

```python
from ios_app_automation import iOSAppAutomation

automation = iOSAppAutomation()

# 打开 APP
await automation.open_app("weixin://")

# 发送邮件
await automation.send_email(
    to="test@example.com",
    subject="测试",
    body="这是一封测试邮件"
)

# 打开地图导航
await automation.open_map("北京市")

# 运行快捷指令
await automation.run_shortcut(
    shortcut_name="我的快捷指令",
    input_data={"key": "value"}
)
```

#### 通过 AgentLinker 远程调用

```bash
# 打开微信
exec iPhone-001 file.write "/tmp/agentlinker_triggers/open_app.txt" "weixin://"

# 发送邮件
exec iPhone-001 file.write "/tmp/agentlinker_triggers/send_email.txt" "mailto:test@example.com"

# 打开淘宝
exec iPhone-001 file.write "/tmp/agentlinker_triggers/open_app.txt" "taobao://item.taobao.com/item.htm?id=123456"
```

---

## 📱 常用 APP URL Scheme

### 社交类

| APP | URL Scheme | 示例 |
|-----|-----------|------|
| 微信 | `weixin://` | `weixin://` |
| QQ | `mqq://` | `mqq://` |
| 微博 | `weibo://` | `weibo://userinfo?uid=123` |
| 抖音 | `snssdk1128://` | `snssdk1128://user/profile/xxx` |
| 快手 | `kwai://` | `kwai://` |
| 小红书 | `xhsdiscover://` | `xhsdiscover://` |
| B 站 | `bilibili://` | `bilibili://video/xxx` |

### 购物类

| APP | URL Scheme | 示例 |
|-----|-----------|------|
| 淘宝 | `taobao://` | `taobao://item.taobao.com/item.htm?id=xxx` |
| 天猫 | `tmall://` | `tmall://` |
| 京东 | `openapp.jdmobile://` | `openapp.jdmobile://virtual?params={"category":"jump"}&url=xxx` |
| 拼多多 | `pinduoduo://` | `pinduoduo://` |

### 支付类

| APP | URL Scheme | 示例 |
|-----|-----------|------|
| 支付宝 | `alipay://` | `alipay://alipayclient/?xxx` |
| 云闪付 | `unionpay://` | `unionpay://` |

### 工具类

| APP | URL Scheme | 示例 |
|-----|-----------|------|
| Safari | `https://` | `https://example.com` |
| 邮件 | `mailto:` | `mailto:test@example.com` |
| 电话 | `tel:` | `tel:1234567890` |
| 短信 | `sms:` | `sms:1234567890` |
| 地图 | `comgooglemaps://` | `comgooglemaps://?daddr=Beijing` |
| 相机 | `camera://` | `camera://` |
| 照片 | `photos-redirect://` | `photos-redirect://` |
| 设置 | `App-Prefs:root=` | `App-Prefs:root=WIFI` |

---

## 🎯 实际使用案例

### 案例 1: 早上自动打开新闻 APP

```python
# 定时任务（早上 8 点）
await automation.open_app("snssdk1128://")  # 抖音
await asyncio.sleep(2)
await automation.open_app("weibo://")  # 微博
```

### 案例 2: 自动发送邮件报告

```python
# 发送日报
await automation.send_email(
    to="boss@company.com",
    subject="今日工作报告",
    body="今日完成工作：\n1. ...\n2. ..."
)
```

### 案例 3: 自动导航到公司

```python
# 导航
await automation.open_map(
    address="北京市朝阳区 xxx 公司",
    latitude=39.9042,
    longitude=116.4074
)
```

### 案例 4: 打开淘宝商品并购买

```python
# 打开商品
await automation.taobao_open_item("123456789")

# 注意：购买需要手动操作
# 可以配合快捷指令实现部分自动化
```

---

## 🔐 安全和限制

### iOS 限制

1. **沙盒隔离** - APP 之间不能直接访问
2. **后台限制** - 后台运行有限制
3. **辅助功能** - 需要用户授权
4. **URL Scheme** - 部分 APP 不公开

### 最佳实践

1. **用户确认** - 重要操作需要用户确认
2. **错误处理** - 处理 APP 未安装的情况
3. **超时处理** - 设置合理的超时时间
4. **日志记录** - 记录所有操作

---

## 🐛 故障排查

### 问题 1: APP 无法打开

**原因**: URL Scheme 错误或 APP 未安装

**解决**:
```python
# 检查 APP 是否安装
try:
    await automation.open_app("weixin://")
except:
    print("微信未安装")
```

### 问题 2: 快捷指令不执行

**原因**: 文件监控未设置

**解决**:
- 检查快捷指令的触发条件
- 确保文件路径正确
- 检查权限设置

### 问题 3: 参数传递失败

**原因**: URL 编码问题

**解决**:
```python
import urllib.parse

# 正确编码
message = urllib.parse.quote("Hello 世界")
url = f"sms:1234567890?body={message}"
```

---

## 📚 参考资料

- [iOS URL Scheme 大全](https://github.com/forkinggreat/URL-Schemes)
- [快捷指令官方文档](https://support.apple.com/zh-cn/guide/shortcuts/welcome/ios)
- [常用 APP URL Scheme](https://www.jianshu.com/p/xxx)

---

**版本**: 1.0.0  
**更新日期**: 2026-03-20  
**维护者**: AgentLinker Team
