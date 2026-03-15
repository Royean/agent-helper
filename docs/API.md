# Agent Helper API 文档

## 概述

Agent Helper 提供了一套 HTTP API，供 AI Agent 远程控制 Linux 主机。

- **基础 URL**: `http://your-server.com:8080`
- **认证方式**: Bearer Token
- **内容类型**: `application/json`

## 认证

所有 API 请求都需要在 Header 中包含 Token：

```
Authorization: Bearer SERVER_AGENT_TOKEN
```

## 接口列表

### 1. 发送指令

执行远程操作指令。

**POST** `/api/v1/agent/send`

#### 请求参数

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| device_id | string | 是 | 目标设备ID |
| action | string | 是 | 执行动作 |
| params | object | 否 | 动作参数 |
| req_id | string | 否 | 请求ID（自动生成） |

#### 支持的 Actions

##### system.info - 获取系统信息

获取 Linux 主机的系统信息。

**参数**: 无

**返回示例**:

```json
{
  "success": true,
  "data": {
    "hostname": "my-server",
    "system": "Linux",
    "release": "5.15.0",
    "version": "#1 SMP",
    "machine": "x86_64",
    "processor": "x86_64",
    "python_version": "3.10.0",
    "memory": {
      "total": "16384000 kB",
      "available": "8192000 kB"
    },
    "disk": {
      "total": 107374182400,
      "available": 53687091200
    },
    "load_avg": [0.5, 0.3, 0.2],
    "uptime": "10h 30m"
  }
}
```

##### shell.exec - 执行 Shell 命令

以 root 权限执行任意 shell 命令。

**参数**:

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| cmd | string | 是 | - | 要执行的命令 |
| timeout | int | 否 | 60 | 超时时间（秒） |
| cwd | string | 否 | - | 工作目录 |

**请求示例**:

```json
{
  "device_id": "linux-01",
  "action": "shell.exec",
  "params": {
    "cmd": "df -h",
    "timeout": 10
  }
}
```

**返回示例**:

```json
{
  "success": true,
  "returncode": 0,
  "stdout": "Filesystem Size Used Avail...",
  "stderr": ""
}
```

##### file.list - 列目录

列出指定目录的内容。

**参数**:

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| path | string | 是 | / | 目录路径 |

**返回示例**:

```json
{
  "success": true,
  "data": {
    "path": "/root",
    "entries": [
      {
        "name": "app",
        "path": "/root/app",
        "type": "directory",
        "size": 4096,
        "mode": "755",
        "mtime": 1700000000,
        "uid": 0,
        "gid": 0
      },
      {
        "name": "data.txt",
        "path": "/root/data.txt",
        "type": "file",
        "size": 1024,
        "mode": "644",
        "mtime": 1700000000,
        "uid": 0,
        "gid": 0
      }
    ]
  }
}
```

##### file.read - 读文件

读取文件内容。

**参数**:

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| path | string | 是 | - | 文件路径 |
| offset | int | 否 | 0 | 起始偏移 |
| limit | int | 否 | 100000 | 最大读取字节数 |

**返回示例** (文本文件):

```json
{
  "success": true,
  "data": {
    "path": "/etc/hostname",
    "content": "my-server\n",
    "encoding": "utf-8",
    "size": 10
  }
}
```

**返回示例** (二进制文件):

```json
{
  "success": true,
  "data": {
    "path": "/bin/ls",
    "content": "base64encoded...",
    "encoding": "base64",
    "size": 133784
  }
}
```

##### file.write - 写文件

写入文件内容。

**参数**:

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| path | string | 是 | - | 文件路径 |
| content | string | 是 | - | 文件内容 |
| encoding | string | 否 | utf-8 | 编码方式 (utf-8/base64) |
| append | bool | 否 | false | 是否追加模式 |
| create_dirs | bool | 否 | true | 自动创建目录 |

**请求示例**:

```json
{
  "device_id": "linux-01",
  "action": "file.write",
  "params": {
    "path": "/root/test.txt",
    "content": "Hello World",
    "append": false
  }
}
```

**返回示例**:

```json
{
  "success": true,
  "data": {
    "path": "/root/test.txt",
    "written": true
  }
}
```

##### file.delete - 删除文件/目录

删除文件或目录。

**参数**:

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| path | string | 是 | - | 路径 |
| recursive | bool | 否 | false | 递归删除目录 |

**返回示例**:

```json
{
  "success": true,
  "data": {
    "deleted": "/root/old_file.txt"
  }
}
```

##### process.list - 进程列表

获取系统进程列表。

**参数**: 无

**返回示例**:

```json
{
  "success": true,
  "data": {
    "processes": [
      {
        "user": "root",
        "pid": 1,
        "cpu": 0.1,
        "mem": 0.2,
        "vsz": "123456",
        "rss": "1234",
        "tty": "?",
        "stat": "Ss",
        "start": "10:00",
        "time": "0:01",
        "command": "/sbin/init"
      }
    ]
  }
}
```

##### process.kill - 杀死进程

终止指定进程。

**参数**:

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| pid | int | 是 | - | 进程ID |
| signal | int | 否 | 15 | 信号 (9=SIGKILL, 15=SIGTERM) |

**返回示例**:

```json
{
  "success": true,
  "data": {
    "killed": 12345,
    "signal": 15
  }
}
```

##### service.operate - 服务操作

管理 systemd 服务。

**参数**:

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| service | string | 是 | - | 服务名称 |
| operation | string | 是 | status | 操作类型 |

**operation 可选值**:

- `start` - 启动服务
- `stop` - 停止服务
- `restart` - 重启服务
- `reload` - 重载配置
- `status` - 查看状态
- `enable` - 开机自启
- `disable` - 禁用自启
- `is-active` - 检查是否运行
- `is-enabled` - 检查是否启用

**返回示例**:

```json
{
  "success": true,
  "returncode": 0,
  "stdout": "active\n",
  "stderr": "",
  "service": "sshd",
  "operation": "is-active"
}
```

#### 响应格式

**成功响应**:

```json
{
  "code": 0,
  "msg": "ok",
  "req_id": "uuid-xxx",
  "data": { ... }
}
```

**错误响应**:

```json
{
  "code": 404,
  "msg": "Device linux-01 not connected",
  "req_id": "uuid-xxx",
  "data": null
}
```

**状态码说明**:

| Code | 含义 |
|------|------|
| 0 | 成功 |
| 401 | Token 无效 |
| 404 | 设备不在线 |
| 408 | 请求超时 |
| 500 | 服务器错误 |

### 2. 获取设备列表

获取当前在线的设备列表。

**GET** `/api/v1/devices`

**响应示例**:

```json
{
  "code": 0,
  "devices": [
    {
      "device_id": "linux-01",
      "connected_at": 1700000000,
      "last_ping": 1700000100,
      "online_duration": 100
    },
    {
      "device_id": "linux-02",
      "connected_at": 1700000050,
      "last_ping": 1700000100,
      "online_duration": 50
    }
  ]
}
```

### 3. 健康检查

检查服务端运行状态。

**GET** `/health`

**响应示例**:

```json
{
  "status": "ok",
  "connected_devices": 2,
  "version": "1.0.0"
}
```

## WebSocket 协议（服务端 ↔ 客户端）

Linux 客户端通过 WebSocket 与服务端通信。

### 连接地址

```
wss://your-server.com/ws/linux
ws://your-server.com/ws/linux  (无加密)
```

### 消息类型

#### 客户端 → 服务端

**注册消息**:

```json
{
  "type": "register",
  "device_id": "linux-01",
  "token": "DEVICE_TOKEN"
}
```

**心跳消息**:

```json
{
  "type": "ping",
  "time": 1700000000
}
```

**结果消息**:

```json
{
  "type": "result",
  "req_id": "uuid-xxx",
  "success": true,
  "data": { ... }
}
```

#### 服务端 → 客户端

**注册响应**:

```json
{
  "type": "registered",
  "device_id": "linux-01",
  "msg": "Connected successfully"
}
```

**执行指令**:

```json
{
  "type": "exec",
  "req_id": "uuid-xxx",
  "action": "shell.exec",
  "params": {
    "cmd": "ls -l",
    "timeout": 10
  }
}
```

## 错误处理

### HTTP 错误码

| 状态码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 401 | Token 无效或缺失 |
| 404 | 设备不在线或接口不存在 |
| 408 | 请求超时 |
| 500 | 服务器内部错误 |

### 业务错误码

| Code | 说明 |
|------|------|
| 0 | 成功 |
| 1 | 未知错误 |
| 404 | 设备不在线 |
| 408 | 执行超时 |
| 500 | 执行错误 |

## 限流说明

MVP 版本暂未实现限流，建议：

- 单设备并发请求数：10
- 单 IP 并发连接数：100
- 全局最大连接数：10000

## 安全建议

1. **使用 HTTPS/WSS** 加密传输
2. **设置强 Token** 至少 32 位随机字符
3. **定期更换 Token**
4. **限制服务端访问 IP** 使用防火墙
5. **监控异常请求** 记录日志审计

## 完整调用示例

### Python

```python
import requests

url = "http://localhost:8080/api/v1/agent/send"
headers = {"Authorization": "Bearer your_token"}

data = {
    "device_id": "linux-01",
    "action": "shell.exec",
    "params": {"cmd": "uptime", "timeout": 10}
}

resp = requests.post(url, json=data, headers=headers)
print(resp.json())
```

### Curl

```bash
curl -X POST http://localhost:8080/api/v1/agent/send \
  -H "Authorization: Bearer your_token" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "linux-01",
    "action": "shell.exec",
    "params": {"cmd": "uptime"}
  }'
```

### JavaScript (Fetch)

```javascript
fetch('http://localhost:8080/api/v1/agent/send', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer your_token',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    device_id: 'linux-01',
    action: 'shell.exec',
    params: { cmd: 'uptime', timeout: 10 }
  })
})
.then(r => r.json())
.then(console.log);
```
