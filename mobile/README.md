# AgentLinker Mobile

📱 **AgentLinker 移动端应用 (Flutter)**

---

## 🎯 功能特性

### 已实现
- ✅ 设备列表管理
- ✅ 实时状态显示
- ✅ 配对密钥复制
- ✅ 基础命令执行
- ✅ WebSocket 连接

### 开发中
- 🚧 文件传输
- 🚧 二维码扫描
- 🚧 推送通知

---

## 📦 安装

### iOS

```bash
cd mobile
flutter pub get
flutter run
```

### Android

```bash
cd mobile
flutter pub get
flutter run
```

---

## 🏗️ 项目结构

```
mobile/
├── lib/
│   ├── main.dart              # 应用入口
│   ├── app.dart               # 应用配置
│   ├── config/
│   │   └── constants.dart     # 常量配置
│   ├── models/
│   │   ├── device.dart        # 设备模型
│   │   └── command.dart       # 命令模型
│   ├── services/
│   │   ├── websocket.dart     # WebSocket 服务
│   │   ├── storage.dart       # 本地存储
│   │   └── notification.dart  # 通知服务
│   ├── screens/
│   │   ├── home/              # 首页
│   │   ├── device/            # 设备详情
│   │   ├── terminal/          # 终端
│   │   └── settings/          # 设置
│   ├── widgets/
│   │   ├── device_card.dart   # 设备卡片
│   │   ├── command_input.dart # 命令输入
│   │   └── progress_bar.dart  # 进度条
│   └── utils/
│       └── helpers.dart       # 工具函数
├── android/                   # Android 配置
├── ios/                       # iOS 配置
└── pubspec.yaml              # 依赖配置
```

---

## 🎨 界面预览

### 首页 - 设备列表
```
┌─────────────────────────┐
│  AgentLinker       ⚙️   │
├─────────────────────────┤
│  📱 MacBook Air         │
│     🟢 在线             │
│     密钥：XK9M2P7Q [复制]│
├─────────────────────────┤
│  🖥️ Server-01           │
│     🟢 在线             │
│     密钥：P3K8M2X9 [复制]│
├─────────────────────────┤
│  🐧 Ubuntu-Test         │
│     🔴 离线             │
│                         │
├─────────────────────────┤
│         [+] 添加设备    │
└─────────────────────────┘
```

### 设备详情 - 终端
```
┌─────────────────────────┐
│  ← MacBook Air      📊  │
├─────────────────────────┤
│  $ df -h                │
│  Filesystem    Size     │
│  /dev/sda1     256G     │
│  ...                    │
│                         │
│  $                      │
│  [________________] 🔍  │
└─────────────────────────┘
```

---

## 🔧 开发指南

### 环境要求

```bash
# Flutter SDK
flutter --version  # 3.0+

# iOS 开发 (macOS)
xcode-select --install

# Android 开发
sdkmanager --install "platform-tools" "platforms;android-33"
```

### 运行项目

```bash
# 安装依赖
flutter pub get

# 运行 iOS
flutter run -d ios

# 运行 Android
flutter run -d android

# 构建 Release
flutter build ios
flutter build apk
```

---

## 📚 核心代码示例

### WebSocket 连接

```dart
import 'package:web_socket_channel/web_socket_channel.dart';

class WebSocketService {
  WebSocketChannel? _channel;
  
  Future<void> connect(String url) async {
    _channel = WebSocketChannel.connect(Uri.parse(url));
    
    // 监听消息
    _channel!.stream.listen((message) {
      _handleMessage(message);
    });
  }
  
  void send(Map<String, dynamic> data) {
    _channel?.sink.add(jsonEncode(data));
  }
  
  void _handleMessage(dynamic message) {
    // 处理服务端消息
  }
}
```

### 设备列表

```dart
class DeviceList extends StatelessWidget {
  final List<Device> devices;
  
  @override
  Widget build(BuildContext context) {
    return ListView.builder(
      itemCount: devices.length,
      itemBuilder: (context, index) {
        final device = devices[index];
        return DeviceCard(
          device: device,
          onTap: () => _openDevice(context, device),
          onCopyKey: () => _copyKey(device.pairingKey),
        );
      },
    );
  }
}
```

### 命令执行

```dart
class TerminalScreen extends StatefulWidget {
  @override
  _TerminalScreenState createState() => _TerminalScreenState();
}

class _TerminalScreenState extends State<TerminalScreen> {
  final _controller = TextEditingController();
  final List<String> _output = [];
  
  void _executeCommand(String cmd) async {
    setState(() => _output.add('\$ $cmd'));
    
    final result = await controllerService.execute(cmd);
    setState(() => _output.add(result.output));
  }
}
```

---

## 🔐 安全考虑

### 1. 存储安全
- 使用 Keychain (iOS) / Keystore (Android) 存储 Token
- 敏感数据加密存储

### 2. 通信安全
- 强制使用 WSS 加密连接
- 证书绑定（防止中间人攻击）

### 3. 权限控制
- 最小权限原则
- 敏感操作需要确认

---

## 📊 性能优化

### 1. 列表优化
```dart
// 使用 ListView.builder 而不是 ListView
ListView.builder(
  itemCount: devices.length,
  itemBuilder: (context, index) => DeviceCard(...),
)
```

### 2. 状态管理
```dart
// 使用 Provider 或 Riverpod
final deviceProvider = ChangeNotifierProvider(
  create: (_) => DeviceService(),
);
```

### 3. 图片优化
```dart
// 使用缓存
CachedNetworkImage(
  imageUrl: device.iconUrl,
  placeholder: (context, url) => CircularProgressIndicator(),
)
```

---

## 🧪 测试

```bash
# 运行测试
flutter test

# 代码分析
flutter analyze

# 格式化
dart format .
```

---

## 📱 发布

### iOS App Store

1. 创建 App Store Connect 应用
2. 配置签名证书
3. 构建 Archive
4. 上传审核

### Google Play

1. 创建 Google Play 应用
2. 生成签名密钥
3. 构建 AAB
4. 上传发布

---

## 🙏 参考资料

- [Flutter 官方文档](https://flutter.dev/docs)
- [Dart 语言指南](https://dart.dev/guides)
- [WebSocket 包](https://pub.dev/packages/web_socket_channel)

---

**版本**: 0.1.0-dev  
**更新日期**: 2026-03-19  
**维护者**: AgentLinker Team
