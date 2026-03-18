#!/bin/bash
# AgentLinker macOS 快速测试脚本
# 用于在本地测试 macOS 客户端

set -e

echo "============================================"
echo "   AgentLinker macOS 快速测试"
echo "============================================"

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误：未找到 Python 3"
    exit 1
fi

echo "✅ Python 版本：$(python3 --version)"

# 创建测试目录
TEST_DIR="/tmp/agentlinker_macos_test"
rm -rf "$TEST_DIR"
mkdir -p "$TEST_DIR"

echo ""
echo "测试目录：$TEST_DIR"

# 复制客户端代码
echo ""
echo "正在复制客户端代码..."
cp -r /tmp/AgentLinker/client "$TEST_DIR/"
cp -r /tmp/AgentLinker/server "$TEST_DIR/"

# 创建虚拟环境
echo ""
echo "正在创建虚拟环境..."
cd "$TEST_DIR"
python3 -m venv venv
source venv/bin/activate

# 安装依赖
echo ""
echo "正在安装依赖..."
pip install -q websockets

# 创建测试配置
echo ""
echo "创建测试配置..."
cat > "$TEST_DIR/test_config.json" << EOF
{
  "device_id": "macos-test-$(hostname)",
  "device_name": "macOS Test Client",
  "token": "ah_device_token_change_in_production",
  "server_url": "ws://127.0.0.1:8080/ws/client"
}
EOF

echo ""
echo "============================================"
echo "   测试准备完成！"
echo "============================================"
echo ""
echo "下一步:"
echo "1. 确保服务端正在运行 (ws://127.0.0.1:8080)"
echo "2. 运行客户端测试:"
echo "   cd $TEST_DIR"
echo "   source venv/bin/activate"
echo "   python3 client/cli.py --config test_config.json"
echo ""
echo "或者直接运行端到端测试:"
echo "   python3 /tmp/AgentLinker/tests/test_e2e_fixed.py"
echo ""
