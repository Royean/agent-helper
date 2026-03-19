#!/bin/bash
# AgentLinker macOS 一键打包脚本
# 自动执行所有打包步骤

set -e

echo "🚀 AgentLinker macOS 一键打包"
echo ""

# 检查是否在项目目录
if [ ! -d "/tmp/AgentLinker" ]; then
    echo "❌ 错误：项目目录不存在"
    exit 1
fi

cd /tmp/AgentLinker

# 1. 确保所有文件已提交
echo "📝 检查代码..."
git status

read -p "继续打包？(y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
fi

# 2. 设置执行权限
echo "🔧 设置权限..."
chmod +x installer/macos/install.sh
chmod +x installer/macos/build-dmg.sh

# 3. 运行打包
echo "📦 开始打包..."
bash installer/macos/build-dmg.sh

# 4. 显示输出
echo ""
echo "✅ 打包完成！"
echo ""
echo "输出目录：/tmp/AgentLinker-Releases/"
ls -lh /tmp/AgentLinker-Releases/

echo ""
echo "📦 可执行的操作:"
echo "  1. 测试安装：open /tmp/AgentLinker-Releases/AgentLinker_2.0.0_macOS.dmg"
echo "  2. 创建 GitHub Release"
echo "  3. 上传到发布页面"
echo ""
