# Agent Helper Linux

一套轻量、高权限、内网穿透、无GUI、服务化的远程接入系统，让任何 AI Agent 可以跨网、安全、高权限控制 Linux 主机。

## 架构

```
AI Agent 端
     ↓（HTTP API 调用）
云端服务端（中转 + 鉴权）
     ↓（WebSocket 长连接）
Linux 客户端（root 权限、systemd 后台）
     ↓（执行系统操作）
Linux 主机
```

- Linux 客户端主动连服务端 → 内网穿透
- Agent 不直接连 Linux → 安全
- 全程 TLS 加密
- 指令异步执行、异步回包

## 快速开始

### 1. 启动服务端

```bash
cd server

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 启动
python main.py
```

服务端默认监听 `0.0.0.0:8080`。

### 2. 部署 Linux 客户端

在目标 Linux 主机上执行：

```bash
# 使用一键安装脚本
curl -fsSL https://your-server.com/install.sh | sudo bash

# 或者手动安装
sudo bash scripts/install.sh
```

安装完成后编辑配置文件：

```bash
sudo nano /etc/agent_helper/config.json
```

配置内容：

```json
{
  "device_id": "my-server-01",
  "token": "YOUR_DEVICE_TOKEN",
  "server_url": "wss://your-server.com/ws/linux",
  "reconnect_interval": 5,
  "heartbeat_interval": 30
}
```

启动服务：

```bash
sudo systemctl start agent_helper
sudo systemctl enable agent_helper
```

### 3. Agent 调用

```python
import requests

url = "http://localhost:8080/api/v1/agent/send"
headers = {"Authorization": "Bearer SERVER_AGENT_TOKEN"}

data = {
    "device_id": "my-server-01",
    "req_id": "req-001",
    "action": "shell.exec",
    "params": {
        "cmd": "df -h",
        "timeout": 10
    }
}

resp = requests.post(url, json=data, headers=headers)
print(resp.json())
```

## 支持的指令

| Action | 描述 | 参数 |
|--------|------|------|
| `system.info` | 获取系统信息 | - |
| `shell.exec` | 执行 shell 命令 | `cmd`, `timeout`, `cwd` |
| `file.list` | 列目录 | `path` |
| `file.read` | 读文件 | `path`, `offset`, `limit` |
| `file.write` | 写文件 | `path`, `content`, `encoding`, `append` |
| `file.delete` | 删除文件/目录 | `path`, `recursive` |
| `process.list` | 进程列表 | - |
| `process.kill` | 杀死进程 | `pid`, `signal` |
| `service.operate` | 系统服务操作 | `service`, `operation` |

## API 文档

### Agent → 服务端

**POST** `/api/v1/agent/send`

请求头：

```
Authorization: Bearer SERVER_AGENT_TOKEN
Content-Type: application/json
```

请求体：

```json
{
  "device_id": "linux-123456",
  "req_id": "uuid-xxxx",
  "action": "shell.exec",
  "params": {
    "cmd": "ls -l /root",
    "timeout": 10
  }
}
```

响应：

```json
{
  "code": 0,
  "msg": "ok",
  "req_id": "uuid-xxxx",
  "data": {
    "success": true,
    "returncode": 0,
    "stdout": "...",
    "stderr": ""
  }
}
```

### 获取在线设备列表

**GET** `/api/v1/devices`

### 健康检查

**GET** `/health`

## 目录结构

```
agent-helper/
├── server/               # 服务端
│   ├── main.py          # FastAPI 主程序
│   └── requirements.txt # Python 依赖
├── client/               # Linux 客户端
│   ├── agent_helper.py  # 客户端主程序
│   ├── requirements.txt # Python 依赖
│   └── config.json.example # 配置模板
├── scripts/              # 部署脚本
│   ├── install.sh       # 一键安装脚本
│   ├── agent_helper.service # systemd 配置
│   └── dev-run.sh       # 开发快速启动
├── examples/             # 调用示例
│   ├── python_example.py
│   ├── curl_example.sh
│   └── node_example.js
└── docs/                 # 文档
    └── API.md
```

## 安全配置

### Token 配置

服务端使用环境变量或修改代码配置 Token：

```bash
export SERVER_AGENT_TOKEN="your_secure_token"
export LINUX_DEVICE_TOKEN="device_token"
```

生产环境建议使用：
- 随机生成的长 Token（32位以上）
- HTTPS/WSS 加密传输
- 定期更换 Token

### 权限控制

- Linux 客户端以 root 运行，可执行任意系统操作
- 服务端通过 Token 鉴权，区分 Agent 调用和设备连接
- 建议配合防火墙限制服务端访问 IP

## 开发调试

```bash
# 快速启动（开发模式）
./scripts/dev-run.sh server   # 启动服务端
./scripts/dev-run.sh client   # 启动客户端（需要 sudo）

# 或使用手动方式
cd server
source venv/bin/activate
python main.py

# 客户端（另一个终端）
sudo python3 client/agent_helper.py
```

## 生产部署

### 服务端部署

1. 使用 systemd 管理服务
2. 配置 Nginx 反向代理（SSL）
3. 配置防火墙

```bash
# Nginx 配置示例
location / {
    proxy_pass http://127.0.0.1:8080;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

### 客户端部署

```bash
# 批量部署脚本
for host in server1 server2 server3; do
    ssh $host "curl -fsSL https://your-server.com/install.sh | sudo bash -s -- -t DEVICE_TOKEN -s wss://your-server.com/ws/linux"
done
```

## 日志

服务端日志：控制台输出（建议配置 systemd journal 或重定向到文件）

客户端日志：`/var/log/agent_helper/agent_helper.log`

查看日志：

```bash
# 服务端（如果使用 systemd）
journalctl -u agent-helper-server -f

# 客户端
sudo tail -f /var/log/agent_helper/agent_helper.log
```

## 许可证

MIT
