#!/bin/bash
# AgentLinker macOS 安装脚本
# 支持 Intel 和 Apple Silicon (M1/M2/M3)

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置
INSTALL_DIR="/opt/agentlinker"
CONFIG_DIR="/etc/agentlinker"
LOG_DIR="/var/log/agentlinker"
LAUNCHD_DIR="/Library/LaunchDaemons"
SERVICE_LABEL="com.agentlinker.client"

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}   AgentLinker macOS 安装脚本${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# 检查 root 权限
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}错误：请使用 sudo 运行此脚本${NC}"
    echo "用法：sudo bash install.sh"
    exit 1
fi

# 检测 macOS 版本
detect_macos() {
    echo -e "${YELLOW}检测系统信息...${NC}"
    
    MACOS_VERSION=$(sw_vers -productVersion)
    MACOS_BUILD=$(sw_vers -buildVersion)
    ARCH=$(uname -m)
    
    echo "   macOS 版本：$MACOS_VERSION"
    echo "   构建版本：$MACOS_BUILD"
    echo "   架构：$ARCH"
    
    # 检查 Python
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version)
        echo "   $PYTHON_VERSION"
    else
        echo -e "${RED}错误：需要安装 Python 3${NC}"
        echo "请从 https://www.python.org/downloads/macos/ 下载"
        exit 1
    fi
    
    echo -e "${GREEN}✓ 系统检查通过${NC}"
    echo ""
}

# 安装依赖
install_dependencies() {
    echo -e "${YELLOW}检查依赖...${NC}"
    
    # 检查 Homebrew
    if ! command -v brew &> /dev/null; then
        echo "   安装 Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    else
        echo "   ✓ Homebrew 已安装"
    fi
    
    # 使用 Homebrew 安装 Python（如果系统 Python 不可用）
    if ! command -v python3 &> /dev/null; then
        echo "   安装 Python 3..."
        brew install python
    else
        echo "   ✓ Python 3 已安装"
    fi
    
    # 检查 pip
    if ! python3 -m pip --version &> /dev/null; then
        echo "   安装 pip..."
        curl https://bootstrap.pypa.io/get-pip.py -o /tmp/get-pip.py
        python3 /tmp/get-pip.py
    else
        echo "   ✓ pip 已安装"
    fi
    
    echo -e "${GREEN}✓ 依赖检查完成${NC}"
    echo ""
}

# 创建目录
create_directories() {
    echo -e "${YELLOW}创建安装目录...${NC}"
    
    mkdir -p "$INSTALL_DIR"
    mkdir -p "$CONFIG_DIR"
    mkdir -p "$LOG_DIR"
    
    # 设置权限
    chmod 755 "$INSTALL_DIR"
    chmod 755 "$CONFIG_DIR"
    chmod 755 "$LOG_DIR"
    
    echo -e "${GREEN}✓ 目录创建完成${NC}"
    echo ""
}

# 下载客户端
download_client() {
    echo -e "${YELLOW}下载 AgentLinker 客户端...${NC}"
    
    # 检查是否有本地源码
    if [ -d "/tmp/AgentLinker" ]; then
        echo "   使用本地源码..."
        cp -r /tmp/AgentLinker/* "$INSTALL_DIR/"
    else
        # 从 GitHub 下载最新版本
        LATEST_VERSION=$(curl -s https://api.github.com/repos/Royean/AgentLinker/releases/latest | grep '"tag_name"' | cut -d'"' -f4 || echo "main")
        
        if [ -z "$LATEST_VERSION" ]; then
            LATEST_VERSION="main"
        fi
        
        DOWNLOAD_URL="https://github.com/Royean/AgentLinker/archive/refs/heads/${LATEST_VERSION}.tar.gz"
        
        echo "   下载版本：$LATEST_VERSION"
        curl -L "$DOWNLOAD_URL" -o /tmp/agentlinker.tar.gz
        tar -xzf /tmp/agentlinker.tar.gz -C "$INSTALL_DIR" --strip-components=1
        rm -f /tmp/agentlinker.tar.gz
    fi
    
    echo -e "${GREEN}✓ 客户端下载完成${NC}"
    echo ""
}

# 创建虚拟环境
create_venv() {
    echo -e "${YELLOW}创建 Python 虚拟环境...${NC}"
    
    cd "$INSTALL_DIR"
    
    # 创建虚拟环境
    python3 -m venv venv
    
    # 激活虚拟环境
    source venv/bin/activate
    
    # 升级 pip
    pip install --upgrade pip
    
    # 安装依赖
    if [ -f "client/requirements.txt" ]; then
        echo "   安装 Python 依赖..."
        pip install -r client/requirements.txt
    else
        pip install websockets qrcode[pil]
    fi
    
    echo -e "${GREEN}✓ 虚拟环境创建完成${NC}"
    echo ""
}

# 创建配置文件
create_config() {
    echo -e "${YELLOW}创建配置文件...${NC}"
    
    cat > "$CONFIG_DIR/config.json" << 'EOF'
{
  "device_id": "",
  "device_name": "",
  "token": "YOUR_DEVICE_TOKEN",
  "server_url": "wss://your-server.com/ws/client",
  "reconnect_interval": 5,
  "heartbeat_interval": 30
}
EOF
    
    # 设置权限
    chmod 644 "$CONFIG_DIR/config.json"
    
    echo -e "${YELLOW}配置文件已创建：$CONFIG_DIR/config.json${NC}"
    echo -e "${YELLOW}请编辑配置文件，设置 token 和 server_url${NC}"
    
    echo -e "${GREEN}✓ 配置文件创建完成${NC}"
    echo ""
}

# 创建 launchd 服务
create_launchd_service() {
    echo -e "${YELLOW}创建 launchd 服务...${NC}"
    
    cat > "/tmp/$SERVICE_LABEL.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>$SERVICE_LABEL</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>$INSTALL_DIR/venv/bin/python3</string>
        <string>$INSTALL_DIR/client/cli.py</string>
        <string>--mode</string>
        <string>client</string>
        <string>--config</string>
        <string>$CONFIG_DIR/config.json</string>
    </array>
    
    <key>WorkingDirectory</key>
    <string>$INSTALL_DIR</string>
    
    <key>RunAtLoad</key>
    <true/>
    
    <key>KeepAlive</key>
    <dict>
        <key>SuccessfulExit</key>
        <false/>
        <key>Crashed</key>
        <true/>
    </dict>
    
    <key>StandardOutPath</key>
    <string>$LOG_DIR/agentlinker.log</string>
    
    <key>StandardErrorPath</key>
    <string>$LOG_DIR/agentlinker.error.log</string>
    
    <key>EnvironmentVariables</key>
    <dict>
        <key>PYTHONIOENCODING</key>
        <string>utf-8</string>
    </dict>
    
    <key>Nice</key>
    <integer>0</integer>
</dict>
</plist>
EOF
    
    # 移动到系统目录
    mv "/tmp/$SERVICE_LABEL.plist" "$LAUNCHD_DIR/$SERVICE_LABEL.plist"
    
    # 设置权限（launchd 需要 root 权限）
    chown root:wheel "$LAUNCHD_DIR/$SERVICE_LABEL.plist"
    chmod 644 "$LAUNCHD_DIR/$SERVICE_LABEL.plist"
    
    # 加载服务
    launchctl load -w "$LAUNCHD_DIR/$SERVICE_LABEL.plist"
    
    echo -e "${GREEN}✓ launchd 服务创建并加载完成${NC}"
    echo ""
}

# 创建 CLI 工具
create_cli() {
    echo -e "${YELLOW}创建命令行工具...${NC}"
    
    # 创建主程序
    cat > "$INSTALL_DIR/client/cli.py" << 'EOF'
#!/usr/bin/env python3
"""AgentLinker macOS CLI"""

import sys
import os

# 添加核心模块路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'utils'))

from discovery import Config, AgentClient, generate_device_id

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='AgentLinker Client')
    parser.add_argument('--mode', choices=['client', 'controller'], default='client',
                       help='运行模式：client(被控端) 或 controller(主控端)')
    parser.add_argument('--config', default='/etc/agentlinker/config.json',
                       help='配置文件路径')
    parser.add_argument('--server', default='ws://localhost:8080/ws/controller',
                       help='服务端 URL (controller 模式)')
    
    args = parser.parse_args()
    
    if args.mode == 'client':
        config = Config(args.config)
        
        # 如果设备 ID 为空，自动生成
        if not config.device_id:
            config.device_id = generate_device_id()
            print(f"已生成设备 ID: {config.device_id}")
        
        if not config.token or not config.server_url:
            print("错误：配置不完整，请编辑配置文件:")
            print(f"  {args.config}")
            sys.exit(1)
        
        print(f"启动 AgentLinker Client")
        print(f"设备 ID: {config.device_id}")
        print(f"服务端：{config.server_url}")
        
        client = AgentClient(config)
        
        import signal
        def signal_handler(signum, frame):
            print("\n收到退出信号，正在停止...")
            client.stop()
            sys.exit(0)
        
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
        
        import asyncio
        asyncio.run(client.run())
    
    elif args.mode == 'controller':
        from controller_v2 import ControllerClient
        import asyncio
        
        controller = ControllerClient(args.server)
        
        import signal
        def signal_handler(signum, frame):
            print("\n收到退出信号，正在停止...")
            controller.stop()
            sys.exit(0)
        
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
        
        asyncio.run(controller.run())

if __name__ == "__main__":
    main()
EOF
    
    chmod +x "$INSTALL_DIR/client/cli.py"
    
    # 创建系统链接
    ln -sf "$INSTALL_DIR/client/cli.py" /usr/local/bin/agentlinker
    
    # 创建辅助脚本
    cat > "$INSTALL_DIR/client/show-qr.sh" << 'EOF'
#!/bin/bash
# 显示配对二维码

CONFIG_FILE="/etc/agentlinker/config.json"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "错误：配置文件不存在"
    exit 1
fi

# 读取配置
DEVICE_ID=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE')).get('device_id', ''))")
TOKEN=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE')).get('token', ''))")
SERVER_URL=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE')).get('server_url', ''))")

if [ -z "$DEVICE_ID" ] || [ -z "$TOKEN" ]; then
    echo "错误：配置不完整"
    exit 1
fi

# 生成配对密钥（从日志中获取或生成新的）
PAIRING_KEY=$(tail -100 /var/log/agentlinker/agentlinker.log 2>/dev/null | grep "配对密钥" | tail -1 | awk '{print $NF}' || echo "请查看日志获取配对密钥")

echo "=================================================="
echo "  AgentLinker 配对信息"
echo "=================================================="
echo ""
echo "设备 ID: $DEVICE_ID"
echo "服务端：$SERVER_URL"
echo "配对密钥：$PAIRING_KEY"
echo ""
echo "二维码内容:"
echo "{\"type\":\"agentlinker_pair\",\"device_id\":\"$DEVICE_ID\",\"pairing_key\":\"$PAIRING_KEY\",\"server_url\":\"$SERVER_URL\"}"
echo ""
echo "=================================================="
echo ""
echo "使用主控端扫描二维码，或手动输入配对密钥"
echo ""

# 尝试显示二维码
if command -v qr &> /dev/null; then
    echo "图形二维码:"
    qr -d "{\"type\":\"agentlinker_pair\",\"device_id\":\"$DEVICE_ID\",\"pairing_key\":\"$PAIRING_KEY\"}"
fi
EOF
    
    chmod +x "$INSTALL_DIR/client/show-qr.sh"
    
    # 创建系统链接
    ln -sf "$INSTALL_DIR/client/show-qr.sh" /usr/local/bin/agentlinker-show-qr
    
    echo -e "${GREEN}✓ CLI 工具创建完成${NC}"
    echo -e "${GREEN}  可使用 'agentlinker' 命令启动${NC}"
    echo -e "${GREEN}  可使用 'agentlinker-show-qr' 显示配对二维码${NC}"
    echo ""
}

# 显示使用说明
show_usage() {
    echo -e "${BLUE}============================================${NC}"
    echo -e "${BLUE}   安装完成！${NC}"
    echo -e "${BLUE}============================================${NC}"
    echo ""
    echo "下一步:"
    echo "  1. 编辑配置文件：$CONFIG_DIR/config.json"
    echo "  2. 设置 token 和 server_url"
    echo "  3. 启动服务："
    echo "     sudo launchctl start $SERVICE_LABEL"
    echo "  4. 开机自启：已自动配置"
    echo "  5. 查看日志：tail -f $LOG_DIR/agentlinker.log"
    echo "  6. 查看配对二维码：agentlinker-show-qr"
    echo ""
    echo "常用命令:"
    echo "  sudo launchctl start $SERVICE_LABEL    - 启动服务"
    echo "  sudo launchctl stop $SERVICE_LABEL     - 停止服务"
    echo "  sudo launchctl unload -w $LAUNCHD_DIR/$SERVICE_LABEL.plist  - 卸载服务"
    echo "  agentlinker --mode controller          - 启动主控端"
    echo ""
    echo "故障排除:"
    echo "  - 查看日志：tail -f $LOG_DIR/agentlinker.log"
    echo "  - 检查服务状态：launchctl list | grep agentlinker"
    echo "  - 重启服务：sudo launchctl kickstart -k system/$SERVICE_LABEL"
    echo ""
}

# 主函数
main() {
    detect_macos
    install_dependencies
    create_directories
    download_client
    create_venv
    create_config
    create_launchd_service
    create_cli
    
    show_usage
}

# 运行
main
