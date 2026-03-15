#!/bin/bash
#
# Agent Helper Linux Client 一键安装脚本
# 支持 Ubuntu/Debian/CentOS/RHEL
#

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 配置
INSTALL_DIR="/opt/agent_helper"
CONFIG_DIR="/etc/agent_helper"
LOG_DIR="/var/log/agent_helper"
SERVICE_NAME="agent_helper"

# 默认参数（可通过环境变量覆盖）
SERVER_URL="${SERVER_URL:-wss://your-server.com/ws/linux}"
DEVICE_TOKEN="${DEVICE_TOKEN:-}"

# 打印信息
info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

# 检查 root 权限
check_root() {
    if [[ $EUID -ne 0 ]]; then
        error "请使用 sudo 或以 root 用户运行此脚本"
    fi
}

# 检测系统类型
detect_os() {
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        OS=$ID
        VERSION=$VERSION_ID
    elif [[ -f /etc/redhat-release ]]; then
        OS="centos"
    elif [[ -f /etc/debian_version ]]; then
        OS="debian"
    else
        error "无法检测操作系统类型"
    fi

    info "检测到操作系统: $OS $VERSION"
}

# 安装依赖
install_deps() {
    info "安装依赖..."

    case $OS in
        ubuntu|debian)
            apt-get update
            apt-get install -y python3 python3-pip python3-venv curl
            ;;
        centos|rhel|fedora|rocky|almalinux)
            yum install -y python3 python3-pip curl || dnf install -y python3 python3-pip curl
            ;;
        *)
            warn "未知系统，尝试通用安装方式"
            ;;
    esac
}

# 创建目录
create_dirs() {
    info "创建目录..."
    mkdir -p "$INSTALL_DIR"
    mkdir -p "$CONFIG_DIR"
    mkdir -p "$LOG_DIR"
}

# 下载客户端代码
download_client() {
    info "下载客户端..."

    # 如果没有指定下载源，提示手动放置
    if [[ ! -f "agent_helper.py" ]]; then
        # 尝试从 GitHub 下载
        CLIENT_URL="${CLIENT_URL:-https://raw.githubusercontent.com/yourorg/agent-helper/main/client/agent_helper.py}"
        info "尝试从 $CLIENT_URL 下载..."

        if command -v curl &> /dev/null; then
            curl -fsSL "$CLIENT_URL" -o "$INSTALL_DIR/agent_helper.py" || {
                warn "自动下载失败，请手动放置 agent_helper.py 到 $INSTALL_DIR/"
                cat > "$INSTALL_DIR/agent_helper.py" << 'PYTHON_EOF'
# 请在此处放置 agent_helper.py 内容
# 或者手动复制: cp agent_helper.py $INSTALL_DIR/
print("请先放置 agent_helper.py")
PYTHON_EOF
            }
        else
            warn "未找到 curl，请手动放置 agent_helper.py 到 $INSTALL_DIR/"
        fi
    else
        cp agent_helper.py "$INSTALL_DIR/"
    fi

    chmod +x "$INSTALL_DIR/agent_helper.py"

    # 安装依赖
    pip3 install --no-cache-dir websockets
}

# 创建配置文件
create_config() {
    info "创建配置文件..."

    if [[ -f "$CONFIG_DIR/config.json" ]]; then
        warn "配置文件已存在，保留现有配置"
        return
    fi

    # 生成设备ID
    DEVICE_ID="${DEVICE_ID:-$(hostname)-$(cat /dev/urandom | tr -dc 'a-z0-9' | fold -w 8 | head -n 1)}"

    # 如果没有提供 token，提示用户
    if [[ -z "$DEVICE_TOKEN" ]]; then
        DEVICE_TOKEN="CHANGE_THIS_TOKEN"
        warn "未设置 DEVICE_TOKEN，请编辑 $CONFIG_DIR/config.json 修改"
    fi

    cat > "$CONFIG_DIR/config.json" << EOF
{
  "device_id": "$DEVICE_ID",
  "token": "$DEVICE_TOKEN",
  "server_url": "$SERVER_URL",
  "reconnect_interval": 5,
  "heartbeat_interval": 30
}
EOF

    chmod 600 "$CONFIG_DIR/config.json"
    info "设备ID: $DEVICE_ID"
}

# 创建 systemd 服务
create_service() {
    info "创建 systemd 服务..."

    cat > "/etc/systemd/system/${SERVICE_NAME}.service" << EOF
[Unit]
Description=Agent Helper Linux Client
After=network.target
Wants=network.target

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=$INSTALL_DIR
Environment=PYTHONUNBUFFERED=1
Environment=PYTHONIOENCODING=utf-8
ExecStart=/usr/bin/python3 $INSTALL_DIR/agent_helper.py
Restart=always
RestartSec=5
StartLimitInterval=60s
StartLimitBurst=3
StandardOutput=append:$LOG_DIR/agent_helper.log
StandardError=append:$LOG_DIR/agent_helper.log

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
}

# 启动服务
start_service() {
    info "启动服务..."

    systemctl enable "$SERVICE_NAME"

    # 检查配置是否完整
    if ! grep -q "CHANGE_THIS_TOKEN" "$CONFIG_DIR/config.json" 2>/dev/null; then
        systemctl start "$SERVICE_NAME"
        sleep 2

        if systemctl is-active --quiet "$SERVICE_NAME"; then
            info "服务启动成功！"
            systemctl status "$SERVICE_NAME" --no-pager
        else
            warn "服务启动可能失败，请检查状态"
            systemctl status "$SERVICE_NAME" --no-pager || true
        fi
    else
        warn "请先配置 token 后再启动服务"
        info "编辑配置文件: $CONFIG_DIR/config.json"
    fi
}

# 显示信息
show_info() {
    echo ""
    echo "========================================"
    info "Agent Helper 安装完成！"
    echo "========================================"
    echo ""
    echo "配置信息:"
    echo "  设备ID:   $(grep device_id $CONFIG_DIR/config.json | cut -d'"' -f4)"
    echo "  配置文件: $CONFIG_DIR/config.json"
    echo "  日志文件: $LOG_DIR/agent_helper.log"
    echo ""
    echo "常用命令:"
    echo "  查看状态: systemctl status $SERVICE_NAME"
    echo "  启动服务: systemctl start $SERVICE_NAME"
    echo "  停止服务: systemctl stop $SERVICE_NAME"
    echo "  重启服务: systemctl restart $SERVICE_NAME"
    echo "  查看日志: tail -f $LOG_DIR/agent_helper.log"
    echo ""
}

# 主流程
main() {
    echo "========================================"
    echo "Agent Helper Linux Client 安装脚本"
    echo "========================================"
    echo ""

    check_root
    detect_os
    install_deps
    create_dirs
    download_client
    create_config
    create_service
    start_service
    show_info
}

# 执行
main "$@"
