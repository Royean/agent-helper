#!/bin/bash
# 本地部署 AgentLinker 服务端和客户端

set -e

echo "🚀 AgentLinker 本地部署脚本"
echo "=============================="

# 配置
SERVER_PORT=8080
SERVER_HOST="127.0.0.1"
PROJECT_DIR="/Users/jiewei/Desktop/AgentLinker"

cd "$PROJECT_DIR"

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 需要安装 Python3"
    exit 1
fi

# 安装依赖（如果需要）
echo "📦 检查依赖..."
pip3 list | grep -q "fastapi" || pip3 install fastapi uvicorn websockets pydantic starlette -q

# 停止旧服务
echo "🛑 停止旧服务..."
pkill -f "python.*server/main.py" 2>/dev/null || true
pkill -f "python.*server/main_v2.py" 2>/dev/null || true
sleep 2

# 启动服务端
echo ""
echo "🌐 启动服务端..."
cd "$PROJECT_DIR/server"
python3 main.py > /tmp/agentlinker_server.log 2>&1 &
SERVER_PID=$!

echo "   服务端 PID: $SERVER_PID"
echo "   日志: /tmp/agentlinker_server.log"

# 等待服务端启动
sleep 3

# 检查服务是否启动
if ps -p $SERVER_PID > /dev/null; then
    echo "✅ 服务端已启动"
    echo "   地址: ws://$SERVER_HOST:$SERVER_PORT"
else
    echo "❌ 服务端启动失败"
    echo "   日志:"
    tail -20 /tmp/agentlinker_server.log
    exit 1
fi

echo ""
echo "=============================="
echo "✅ 本地部署完成！"
echo ""
echo "服务端信息:"
echo "  - WebSocket: ws://$SERVER_HOST:$SERVER_PORT/ws/client"
echo "  - HTTP API:  http://$SERVER_HOST:$SERVER_PORT"
echo "  - 日志:      /tmp/agentlinker_server.log"
echo ""
echo "客户端配置:"
echo "  修改 macOS/Sources/Services/WebSocketManager.swift:"
echo "  serverUrl: \"ws://$SERVER_HOST:$SERVER_PORT/ws/client\""
echo ""
echo "启动 macOS 客户端:"
echo "  open $PROJECT_DIR/macos/releases/AgentLinker.app"
echo ""
echo "查看日志:"
echo "  tail -f /tmp/agentlinker_server.log"

# 保存 PID
echo $SERVER_PID > /tmp/agentlinker_server.pid
