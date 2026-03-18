#!/bin/bash
# AgentLinker macOS 安装脚本
# 支持 Intel 和 Apple Silicon Mac

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
LAUNCHD_LABEL="com.agentlinker.client"

echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}   AgentLinker macOS 安装脚本${NC}"
echo -e "${GREEN}============================================${NC}"

# 检查是否以 root 运行
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}错误：请使用 sudo 运行此脚本${NC}"
    echo "用法：sudo bash install.sh"
    exit 1
fi

# 检测 macOS 版本
detect_macos() {
    MACOS_VERSION=$(sw_vers -productVersion)
    MACOS_NAME=$(sw_vers -productName)
    ARCH=$(uname -m)
    
    echo "检测到系统：$MACOS_NAME $MACOS_VERSION"
    echo "架构：$ARCH"
    
    # 检查 Python
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version)
        echo "Python: $PYTHON_VERSION"
    else
        echo -e "${RED}错误：未找到 Python 3${NC}"
        echo "请先安装 Python 3 (https://www.python.org/downloads/macos/)"
        exit 1
    fi
}

# 安装依赖（如果需要）
install_dependencies() {
    echo -e "${YELLOW}检查依赖...${NC}"
    
    # 检查 Homebrew
    if ! command -v brew &> /dev/null; then
        echo -e "${YELLOW}Homebrew 未安装，正在安装...${NC}"
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi
    
    # 确保安装了 Python 3
    if ! command -v python3 &> /dev/null; then
        echo -e "${YELLOW}正在安装 Python 3...${NC}"
        brew install python3
    fi
    
    echo -e "${GREEN}✓ 依赖检查完成${NC}"
}

# 创建目录
create_directories() {
    echo -e "${YELLOW}正在创建目录...${NC}"
    
    mkdir -p "$INSTALL_DIR"
    mkdir -p "$CONFIG_DIR"
    mkdir -p "$LOG_DIR"
    
    # 设置权限
    chmod 755 "$INSTALL_DIR"
    chmod 755 "$CONFIG_DIR"
    chmod 755 "$LOG_DIR"
    
    echo -e "${GREEN}✓ 目录创建完成${NC}"
}

# 下载客户端
download_client() {
    echo -e "${YELLOW}正在下载 AgentLinker 客户端...${NC}"
    
    # 从 GitHub 下载最新版本
    LATEST_VERSION="master"
    DOWNLOAD_URL="https://github.com/Royean/AgentLinker/archive/refs/heads/${LATEST_VERSION}.tar.gz"
    
    # 下载并解压
    curl -L "$DOWNLOAD_URL" -o /tmp/agentlinker.tar.gz
    tar -xzf /tmp/agentlinker.tar.gz -C "$INSTALL_DIR" --strip-components=1
    
    rm -f /tmp/agentlinker.tar.gz
    
    echo -e "${GREEN}✓ 客户端下载完成${NC}"
}

# 创建虚拟环境
create_venv() {
    echo -e "${YELLOW}正在创建 Python 虚拟环境...${NC}"
    
    cd "$INSTALL_DIR"
    
    # 使用系统 Python 创建虚拟环境
    python3 -m venv venv
    source venv/bin/activate
    
    # 安装依赖
    if [ -f "client/requirements.txt" ]; then
        pip install -r client/requirements.txt
    else
        pip install websockets
    fi
    
    echo -e "${GREEN}✓ 虚拟环境创建完成${NC}"
}

# 创建配置文件
create_config() {
    echo -e "${YELLOW}正在创建配置文件...${NC}"
    
    # 生成设备 ID（使用 Mac 的序列号或主机名）
    HOSTNAME=$(hostname)
    DEVICE_ID="${HOSTNAME}-$(uuidgen | cut -d'-' -f1 | tr '[:upper:]' '[:lower:]')"
    
    cat > "$CONFIG_DIR/config.json" << EOF
{
  "device_id": "$DEVICE_ID",
  "device_name": "Mac - $HOSTNAME",
  "token": "ah_device_token_change_in_production",
  "server_url": "wss://your-server.com/ws/client",
  "reconnect_interval": 5,
  "heartbeat_interval": 30
}
EOF
    
    echo -e "${YELLOW}配置文件已创建：$CONFIG_DIR/config.json${NC}"
    echo -e "${YELLOW}设备 ID: $DEVICE_ID${NC}"
    echo -e "${YELLOW}请编辑配置文件，设置 server_url 为你的服务端地址${NC}"
    
    echo -e "${GREEN}✓ 配置文件创建完成${NC}"
}

# 创建 launchd 服务
create_launchd_service() {
    echo -e "${YELLOW}正在创建 launchd 服务...${NC}"
    
    # 创建启动脚本
    cat > "$INSTALL_DIR/start.sh" << 'STARTSCRIPT'
#!/bin/bash
cd /opt/agentlinker
source venv/bin/activate
exec python3 client/cli.py --mode client --config /etc/agentlinker/config.json
STARTSCRIPT
    
    chmod +x "$INSTALL_DIR/start.sh"
    
    # 创建 launchd plist
    cat > "/Library/LaunchDaemons/$LAUNCHD_LABEL.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>$LAUNCHD_LABEL</string>
    <key>ProgramArguments</key>
    <array>
        <string>/opt/agentlinker/start.sh</string>
    </array>
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
    <string>/var/log/agentlinker/agentlinker.log</string>
    <key>StandardErrorPath</key>
    <string>/var/log/agentlinker/agentlinker.error.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/opt/agentlinker/venv/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
    </dict>
    <key>WorkingDirectory</key>
    <string>/opt/agentlinker</string>
</dict>
</plist>
EOF
    
    # 设置权限
    chown root:wheel "/Library/LaunchDaemons/$LAUNCHD_LABEL.plist"
    chmod 644 "/Library/LaunchDaemons/$LAUNCHD_LABEL.plist"
    
    # 加载服务
    launchctl load -w "/Library/LaunchDaemons/$LAUNCHD_LABEL.plist"
    
    echo -e "${GREEN}✓ launchd 服务创建完成${NC}"
}

# 创建 CLI 工具
create_cli() {
    echo -e "${YELLOW}正在创建 CLI 工具...${NC}"
    
    # 确保 CLI 存在
    if [ ! -f "$INSTALL_DIR/client/cli.py" ]; then
        cat > "$INSTALL_DIR/client/cli.py" << 'CLISCRIPT'
#!/usr/bin/env python3
"""AgentLinker CLI"""

import sys
import os

# 添加核心模块路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))

from core import Config, AgentClient, generate_device_id

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
        from controller import ControllerClient
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
CLISCRIPT
        
        chmod +x "$INSTALL_DIR/client/cli.py"
    fi
    
    # 创建系统链接
    ln -sf "$INSTALL_DIR/client/cli.py" /usr/local/bin/agentlinker
    
    echo -e "${GREEN}✓ CLI 工具创建完成${NC}"
    echo -e "${GREEN}  可以使用 'agentlinker' 命令启动${NC}"
}

# 显示使用说明
show_instructions() {
    echo ""
    echo -e "${GREEN}============================================${NC}"
    echo -e "${GREEN}   安装完成！${NC}"
    echo -e "${GREEN}============================================${NC}"
    echo ""
    echo "下一步:"
    echo -e "  ${BLUE}1. 编辑配置文件：${NC}sudo nano $CONFIG_DIR/config.json"
    echo "  2. 设置 server_url 为你的服务端地址"
    echo ""
    echo -e "  ${BLUE}3. 启动服务：${NC}"
    echo "     sudo launchctl start $LAUNCHD_LABEL"
    echo ""
    echo -e "  ${BLUE}4. 开机自启：${NC}已自动配置"
    echo ""
    echo -e "  ${BLUE}5. 查看日志：${NC}"
    echo "     tail -f $LOG_DIR/agentlinker.log"
    echo ""
    echo -e "  ${BLUE}6. 查看配对密钥：${NC}"
    echo "     启动后查看日志输出"
    echo ""
    echo -e "${YELLOW}常用命令:${NC}"
    echo "  sudo launchctl start $LAUNCHD_LABEL    # 启动服务"
    echo "  sudo launchctl stop $LAUNCHD_LABEL     # 停止服务"
    echo "  sudo launchctl unload -w /Library/LaunchDaemons/$LAUNCHD_LABEL.plist  # 卸载服务"
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
    show_instructions
}

# 运行
main
