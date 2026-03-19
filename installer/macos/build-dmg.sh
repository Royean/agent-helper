#!/bin/bash
# AgentLinker macOS DMG 打包脚本
# 创建 .app 应用程序和 .dmg 安装包

set -e

# 配置
APP_NAME="AgentLinker"
APP_DIR="/tmp/AgentLinker-App"
DMG_DIR="/tmp/AgentLinker-DMG"
OUTPUT_DIR="/tmp/AgentLinker-Releases"
VERSION="2.0.0"

echo "🍎 AgentLinker macOS 打包脚本"
echo "版本：$VERSION"
echo ""

# 清理旧文件
rm -rf "$APP_DIR" "$DMG_DIR" "$OUTPUT_DIR"
mkdir -p "$APP_DIR/$APP_NAME.app/Contents/MacOS"
mkdir -p "$APP_DIR/$APP_NAME.app/Contents/Resources"
mkdir -p "$DMG_DIR"
mkdir -p "$OUTPUT_DIR"

# 创建 Info.plist
echo "📦 创建 Info.plist..."
cat > "$APP_DIR/$APP_NAME.app/Contents/Info.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>agentlinker</string>
    <key>CFBundleIdentifier</key>
    <string>com.agentlinker.client</string>
    <key>CFBundleName</key>
    <string>AgentLinker</string>
    <key>CFBundleDisplayName</key>
    <string>AgentLinker</string>
    <key>CFBundleVersion</key>
    <string>$VERSION</string>
    <key>CFBundleShortVersionString</key>
    <string>$VERSION</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleSignature</key>
    <string>????</string>
    <key>CFBundleLicense</key>
    <string>MIT</string>
    <key>NSHumanReadableCopyright</key>
    <string>Copyright © 2026 AgentLinker. All rights reserved.</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.15</string>
    <key>LSUIElement</key>
    <true/>
</dict>
</plist>
EOF

# 创建启动脚本
echo "📝 创建启动脚本..."
cat > "$APP_DIR/$APP_NAME.app/Contents/MacOS/agentlinker" << 'EOF'
#!/bin/bash
# AgentLinker macOS App 启动脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"
INSTALL_DIR="$APP_DIR/Contents/Resources"

# 检查配置
CONFIG_FILE="/etc/agentlinker/config.json"

if [ ! -f "$CONFIG_FILE" ]; then
    osascript -e "display dialog \"配置文件不存在，请先运行安装脚本。\" with title \"AgentLinker\""
    exit 1
fi

# 激活虚拟环境
source "$INSTALL_DIR/venv/bin/activate"

# 启动客户端
cd "$INSTALL_DIR"
exec python3 "$INSTALL_DIR/client/cli.py" --mode client --config "$CONFIG_FILE"
EOF

chmod +x "$APP_DIR/$APP_NAME.app/Contents/MacOS/agentlinker"

# 复制资源文件
echo "📁 复制资源文件..."
cp -r /tmp/AgentLinker/* "$APP_DIR/$APP_NAME.app/Contents/Resources/"

# 创建虚拟环境
echo "🐍 创建虚拟环境..."
cd "$APP_DIR/$APP_NAME.app/Contents/Resources"
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r client/requirements.txt

# 创建 PkgInfo
echo "APPL????" > "$APP_DIR/$APP_NAME.app/Contents/PkgInfo"

# 创建 DMG 背景
echo "💿 创建 DMG..."
cp -r "$APP_DIR/$APP_NAME.app" "$DMG_DIR/"

# 创建安装说明
cat > "$DMG_DIR/README.txt" << EOF
AgentLinker $VERSION for macOS

安装步骤:
1. 将此应用程序拖拽到 /Applications 文件夹
2. 运行安装脚本配置服务（可选）
3. 编辑配置文件：/etc/agentlinker/config.json
4. 启动服务

或者使用命令行安装:
  sudo bash installer/macos/install.sh

更多信息请访问:
https://github.com/Royean/AgentLinker
EOF

# 创建符号链接到 Applications
ln -s /Applications "$DMG_DIR/Applications"

# 创建 DMG 文件
echo "🔨 构建 DMG..."
hdiutil create -volname "$APP_NAME" \
    -srcfolder "$DMG_DIR" \
    -ov -format UDZO \
    "$OUTPUT_DIR/${APP_NAME}_${VERSION}_macOS.dmg"

# 计算文件大小
DMG_SIZE=$(du -h "$OUTPUT_DIR/${APP_NAME}_${VERSION}_macOS.dmg" | cut -f1)

echo ""
echo "✅ 打包完成!"
echo ""
echo "输出文件:"
echo "  📦 DMG: $OUTPUT_DIR/${APP_NAME}_${VERSION}_macOS.dmg ($DMG_SIZE)"
echo "  📱 APP: $APP_DIR/$APP_NAME.app"
echo ""
echo "下一步:"
echo "  1. 测试 DMG 安装"
echo "  2. 签名和公证（发布到生产环境）"
echo "  3. 创建 GitHub Release"
echo ""
