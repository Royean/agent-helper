#!/bin/bash
# AgentLinker macOS 构建脚本
# 支持 Swift Package Manager 构建

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

APP_NAME="AgentLinker"
VERSION="1.0.0"
BUILD_DIR=".build"
RELEASE_DIR="releases"

echo -e "${BLUE}🍎 AgentLinker macOS 构建脚本${NC}"
echo -e "版本: ${VERSION}"
echo ""

# 检查 Xcode
if ! xcodebuild -version &> /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️ 警告: 未找到完整 Xcode 安装${NC}"
    echo ""
    echo "要构建原生 SwiftUI 应用，需要安装 Xcode:"
    echo "  1. 从 App Store 安装 Xcode (推荐)"
    echo "  2. 或者从 Apple Developer 下载: https://developer.apple.com/download/"
    echo ""
    echo "安装完成后，运行:"
    echo "  sudo xcode-select -s /Applications/Xcode.app/Contents/Developer"
    echo ""
    echo -e "${YELLOW}将使用 Python 包装器创建 .app 包${NC}"
    USE_PYTHON_WRAPPER=true
else
    echo -e "${GREEN}✅ 找到 Xcode${NC}"
    xcodebuild -version | head -1
    echo ""
    USE_PYTHON_WRAPPER=false
fi

# 清理
if [ -d "$RELEASE_DIR" ]; then
    echo -e "${BLUE}🧹 清理旧构建...${NC}"
    rm -rf "$RELEASE_DIR"
fi
mkdir -p "$RELEASE_DIR"

if [ "$USE_PYTHON_WRAPPER" = false ]; then
    echo -e "${BLUE}🔨 使用 Swift Package Manager 构建...${NC}"

    # 构建
    swift build -c release

    # 创建 .app 结构
    APP_BUNDLE="$RELEASE_DIR/${APP_NAME}.app"
    mkdir -p "$APP_BUNDLE/Contents/MacOS"
    mkdir -p "$APP_BUNDLE/Contents/Resources"

    # 复制可执行文件
    cp ".build/release/${APP_NAME}" "$APP_BUNDLE/Contents/MacOS/"

    # 创建 Info.plist
    cat > "$APP_BUNDLE/Contents/Info.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>${APP_NAME}</string>
    <key>CFBundleIdentifier</key>
    <string>com.agentlinker.client</string>
    <key>CFBundleName</key>
    <string>${APP_NAME}</string>
    <key>CFBundleDisplayName</key>
    <string>${APP_NAME}</string>
    <key>CFBundleVersion</key>
    <string>${VERSION}</string>
    <key>CFBundleShortVersionString</key>
    <string>${VERSION}</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleSignature</key>
    <string>????</string>
    <key>LSMinimumSystemVersion</key>
    <string>13.0</string>
    <key>NSHumanReadableCopyright</key>
    <string>Copyright © 2026 AgentLinker. All rights reserved.</string>
    <key>LSApplicationCategoryType</key>
    <string>public.app-category.utilities</string>
</dict>
</plist>
EOF

    # 创建 PkgInfo
    echo "APPL????" > "$APP_BUNDLE/Contents/PkgInfo"

    # 代码签名
    echo -e "${BLUE}🔐 签名应用...${NC}"

    # 创建 entitlements 文件
    ENTITLEMENTS_FILE="$RELEASE_DIR/entitlements.plist"
    cat > "$ENTITLEMENTS_FILE" << 'ENTEOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>com.apple.security.network.client</key>
    <true/>
    <key>com.apple.security.network.server</key>
    <true/>
    <key>com.apple.security.app-sandbox</key>
    <false/>
    <key>com.apple.security.cs.disable-library-validation</key>
    <true/>
    <key>com.apple.security.cs.allow-unsigned-executable-memory</key>
    <true/>
</dict>
</plist>
ENTEOF

    # 使用 ad-hoc 签名（不需要开发者账号）
    codesign --force --deep --sign - --entitlements "$ENTITLEMENTS_FILE" "$APP_BUNDLE" 2>/dev/null

    if codesign -dv "$APP_BUNDLE" 2>/dev/null | grep -q "Signature=adhoc"; then
        echo -e "${GREEN}✅ 应用已签名 (ad-hoc)${NC}"
    else
        echo -e "${YELLOW}⚠️ 签名可能失败，请手动运行:${NC}"
        echo "  codesign --force --deep --sign - --entitlements $ENTITLEMENTS_FILE $APP_BUNDLE"
    fi

    echo -e "${GREEN}✅ 原生 SwiftUI 应用构建完成!${NC}"
else
    echo -e "${BLUE}📦 创建基于 Python 的 .app 包...${NC}"

    # 创建 .app 结构
    APP_BUNDLE="$RELEASE_DIR/${APP_NAME}.app"
    MACOS_DIR="$APP_BUNDLE/Contents/MacOS"
    RESOURCES_DIR="$APP_BUNDLE/Contents/Resources"
    mkdir -p "$MACOS_DIR"
    mkdir -p "$RESOURCES_DIR"

    # 创建启动脚本
    cat > "$MACOS_DIR/${APP_NAME}" << 'EOF'
#!/bin/bash
# AgentLinker for macOS - 菜单栏启动脚本

APP_DIR="$(cd "$(dirname "$(dirname "$(dirname "$0")")")" && pwd)"
RESOURCES_DIR="$APP_DIR/Contents/Resources"
CLIENT_DIR="$RESOURCES_DIR/client"

# 检查 Python
if ! command -v python3 &> /dev/null; then
    osascript -e 'display dialog "需要安装 Python 3 才能运行 AgentLinker。\n\n请访问 https://www.python.org/downloads/ 安装 Python 3" buttons {"确定"} default button 1 with icon stop'
    exit 1
fi

# 检查客户端代码
if [ ! -d "$CLIENT_DIR" ]; then
    osascript -e 'display dialog "未找到客户端文件。请重新安装 AgentLinker。" buttons {"确定"} default button 1 with icon stop'
    exit 1
fi

# 安装依赖
if [ -f "$CLIENT_DIR/requirements.txt" ]; then
    pip3 install -q -r "$CLIENT_DIR/requirements.txt" 2>/dev/null || true
fi

# 确保有配置文件
CONFIG_DIR="$HOME/.agentlinker"
CONFIG_FILE="$CONFIG_DIR/config.json"
if [ ! -f "$CONFIG_FILE" ]; then
    mkdir -p "$CONFIG_DIR"
    cat > "$CONFIG_FILE" << 'INNEREOF'
{
    "device_id": "",
    "device_name": "Mac Device",
    "token": "ah_device_token_change_in_production",
    "server_url": "ws://43.98.243.80:8080/ws/client",
    "auto_start": true,
    "copy_on_start": true
}
INNEREOF
fi

# 启动菜单栏应用
cd "$CLIENT_DIR"
nohup python3 menubar_app.py >/dev/null 2>&1 &
EOF

    chmod +x "$MACOS_DIR/${APP_NAME}"

    # 复制客户端代码
    echo -e "${BLUE}📁 复制客户端代码...${NC}"
    cp -r ../client "$RESOURCES_DIR/"

    # 创建默认配置
    cat > "$RESOURCES_DIR/config.json" << EOF
{
    "token": "ah_device_token_change_in_production",
    "server_url": "ws://43.98.243.80:8080/ws/client",
    "device_name": "Mac Device",
    "log_level": "INFO"
}
EOF

    # 创建 Info.plist
    cat > "$APP_BUNDLE/Contents/Info.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>${APP_NAME}</string>
    <key>CFBundleIdentifier</key>
    <string>com.agentlinker.client</string>
    <key>CFBundleName</key>
    <string>${APP_NAME}</string>
    <key>CFBundleDisplayName</key>
    <string>${APP_NAME}</string>
    <key>CFBundleVersion</key>
    <string>${VERSION}</string>
    <key>CFBundleShortVersionString</key>
    <string>${VERSION}</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleSignature</key>
    <string>????</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.15</string>
    <key>NSHumanReadableCopyright</key>
    <string>Copyright © 2026 AgentLinker. All rights reserved.</string>
</dict>
</plist>
EOF

    # 创建 PkgInfo
    echo "APPL????" > "$APP_BUNDLE/Contents/PkgInfo"

    echo -e "${GREEN}✅ Python 包装应用创建完成!${NC}"
fi

# 签名（仅用于本地运行）
if command -v codesign &> /dev/null; then
    echo -e "${BLUE}🔏 签名应用...${NC}"
    codesign --force --deep --sign - "$APP_BUNDLE" 2>/dev/null || echo "签名失败（不影响使用）"
fi

# 计算大小
APP_SIZE=$(du -sh "$APP_BUNDLE" | cut -f1)

echo ""
echo -e "${GREEN}✅ 构建完成!${NC}"
echo ""
echo "应用位置:"
echo "  📱 $APP_BUNDLE ($APP_SIZE)"
echo ""
echo "安装说明:"
echo "  1. 将 ${APP_NAME}.app 拖到 /Applications 目录"
echo "  2. 首次运行可能需要右键选择'打开'以绕过 Gatekeeper"
echo "  3. 如果需要，在系统设置中授予必要的权限"
echo ""

# 创建 DMG（可选）
if command -v hdiutil &> /dev/null; then
    echo -e "${BLUE}📦 创建 DMG 镜像...${NC}"
    DMG_NAME="${APP_NAME}_${VERSION}_macOS.dmg"

    # 创建临时目录
    TEMP_DIR=$(mktemp -d)
    cp -r "$APP_BUNDLE" "$TEMP_DIR/"

    # 创建 DMG
    hdiutil create -volname "$APP_NAME" -srcfolder "$TEMP_DIR" -ov -format UDZO "$RELEASE_DIR/$DMG_NAME" 2>/dev/null || echo "DMG 创建失败"

    rm -rf "$TEMP_DIR"

    if [ -f "$RELEASE_DIR/$DMG_NAME" ]; then
        DMG_SIZE=$(du -sh "$RELEASE_DIR/$DMG_NAME" | cut -f1)
        echo -e "${GREEN}✅ DMG 创建完成: $RELEASE_DIR/$DMG_NAME ($DMG_SIZE)${NC}"
    fi
fi

echo ""
echo -e "${BLUE}输出目录: $RELEASE_DIR/${NC}"
ls -la "$RELEASE_DIR/"
