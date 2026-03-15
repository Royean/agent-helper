#!/bin/bash
#
# Agent Helper 快速启动脚本（开发测试用）
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 颜色
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# 启动服务端
start_server() {
    info "启动服务端..."
    cd "$SCRIPT_DIR/../server"

    # 检查虚拟环境
    if [[ ! -d "venv" ]]; then
        info "创建 Python 虚拟环境..."
        python3 -m venv venv
    fi

    source venv/bin/activate
    pip install -q -r requirements.txt

    # 设置环境变量（开发用默认值）
    export SERVER_AGENT_TOKEN="dev_server_token"
    export LINUX_DEVICE_TOKEN="dev_device_token"

    info "服务端启动在 http://localhost:8080"
    info "API Token: $SERVER_AGENT_TOKEN"
    info "按 Ctrl+C 停止"
    echo ""

    python main.py
}

# 启动客户端（需要 root）
start_client() {
    if [[ $EUID -ne 0 ]]; then
        warn "客户端需要 root 权限，使用 sudo 运行"
        exit 1
    fi

    info "启动客户端..."
    cd "$SCRIPT_DIR/../client"

    # 检查配置
    if [[ ! -f "/etc/agent_helper/config.json" ]]; then
        mkdir -p /etc/agent_helper
        cat > /etc/agent_helper/config.json << EOF
{
  "device_id": "dev-$(hostname)-$(date +%s)",
  "token": "dev_device_token",
  "server_url": "ws://localhost:8080/ws/linux",
  "reconnect_interval": 5,
  "heartbeat_interval": 30
}
EOF
        info "已创建开发配置: /etc/agent_helper/config.json"
    fi

    pip3 install -q websockets 2>/dev/null || true

    info "客户端启动，连接到 ws://localhost:8080/ws/linux"
    info "按 Ctrl+C 停止"
    echo ""

    python3 agent_helper.py
}

# 使用说明
usage() {
    echo "用法: $0 [server|client]"
    echo ""
    echo "命令:"
    echo "  server  - 启动服务端（开发模式）"
    echo "  client  - 启动客户端（需要 root）"
    echo ""
}

# 主逻辑
case "${1:-}" in
    server)
        start_server
        ;;
    client)
        start_client
        ;;
    *)
        usage
        exit 1
        ;;
esac
