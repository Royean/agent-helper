#!/bin/bash
#
# Agent Helper Curl 调用示例
#

SERVER_URL="http://localhost:8080"
SERVER_TOKEN="ah_server_token_change_in_production"
DEVICE_ID="my-linux-server"

echo "========================================"
echo "Agent Helper Curl 调用示例"
echo "========================================"

# 1. 健康检查
echo -e "\n1. 健康检查:"
curl -s "${SERVER_URL}/health" | jq .

# 2. 获取系统信息
echo -e "\n2. 获取系统信息:"
curl -s -X POST "${SERVER_URL}/api/v1/agent/send" \
  -H "Authorization: Bearer ${SERVER_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "'"${DEVICE_ID}"'",
    "action": "system.info",
    "params": {}
  }' | jq .

# 3. 执行 shell 命令
echo -e "\n3. 执行命令 (uname -a):"
curl -s -X POST "${SERVER_URL}/api/v1/agent/send" \
  -H "Authorization: Bearer ${SERVER_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "'"${DEVICE_ID}"'",
    "action": "shell.exec",
    "params": {"cmd": "uname -a", "timeout": 10}
  }' | jq .

# 4. 列目录
echo -e "\n4. 列目录 (/etc):"
curl -s -X POST "${SERVER_URL}/api/v1/agent/send" \
  -H "Authorization: Bearer ${SERVER_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "'"${DEVICE_ID}"'",
    "action": "file.list",
    "params": {"path": "/etc"}
  }' | jq '.data.data.entries[:3]'

# 5. 读文件
echo -e "\n5. 读文件 (/etc/hostname):"
curl -s -X POST "${SERVER_URL}/api/v1/agent/send" \
  -H "Authorization: Bearer ${SERVER_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "'"${DEVICE_ID}"'",
    "action": "file.read",
    "params": {"path": "/etc/hostname"}
  }' | jq '.data.data.content'

# 6. 进程列表
echo -e "\n6. 进程列表 (前3个):"
curl -s -X POST "${SERVER_URL}/api/v1/agent/send" \
  -H "Authorization: Bearer ${SERVER_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "'"${DEVICE_ID}"'",
    "action": "process.list",
    "params": {}
  }' | jq '.data.data.processes[:3]'

# 7. 服务状态
echo -e "\n7. 服务状态 (cron):"
curl -s -X POST "${SERVER_URL}/api/v1/agent/send" \
  -H "Authorization: Bearer ${SERVER_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "'"${DEVICE_ID}"'",
    "action": "service.operate",
    "params": {"service": "cron", "operation": "is-active"}
  }' | jq .

# 8. 在线设备列表
echo -e "\n8. 在线设备列表:"
curl -s "${SERVER_URL}/api/v1/devices" \
  -H "Authorization: Bearer ${SERVER_TOKEN}" | jq .

echo -e "\n========================================"
echo "示例完成"
echo "========================================"
