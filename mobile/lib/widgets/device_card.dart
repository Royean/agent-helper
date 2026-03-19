import 'package:flutter/material.dart';
import 'package:clipboard/clipboard.dart';
import '../models/device.dart';

class DeviceCard extends StatelessWidget {
  final Device device;
  final VoidCallback onTap;
  final VoidCallback? onCopyKey;

  const DeviceCard({
    super.key,
    required this.device,
    required this.onTap,
    this.onCopyKey,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  // 平台图标
                  Text(
                    device.platformIcon,
                    style: const TextStyle(fontSize: 32),
                  ),
                  const SizedBox(width: 12),
                  
                  // 设备信息
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          device.deviceName,
                          style: Theme.of(context).textTheme.titleMedium?.copyWith(
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        const SizedBox(height: 4),
                        Row(
                          children: [
                            // 在线状态
                            Container(
                              width: 8,
                              height: 8,
                              decoration: BoxDecoration(
                                color: device.isOnline ? Colors.green : Colors.red,
                                shape: BoxShape.circle,
                              ),
                            ),
                            const SizedBox(width: 6),
                            Text(
                              device.isOnline ? '在线' : '离线',
                              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                                color: device.isOnline ? Colors.green : Colors.red,
                              ),
                            ),
                            const SizedBox(width: 12),
                            Text(
                              device.platform,
                              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                                color: Colors.grey,
                              ),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                  
                  // 复制密钥按钮
                  if (device.pairingKey != null && device.isOnline)
                    IconButton(
                      icon: const Icon(Icons.copy),
                      onPressed: () {
                        FlutterClipboard.copy(device.pairingKey!);
                        ScaffoldMessenger.of(context).showSnackBar(
                          SnackBar(
                            content: Text('配对密钥已复制：${device.pairingKey}'),
                            duration: const Duration(seconds: 2),
                          ),
                        );
                        onCopyKey?.call();
                      },
                      tooltip: '复制配对密钥',
                    ),
                ],
              ),
              
              // 配对密钥显示
              if (device.pairingKey != null && device.isOnline) ...[
                const SizedBox(height: 12),
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: Colors.blue.shade50,
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.key, size: 20, color: Colors.blue),
                      const SizedBox(width: 8),
                      Text(
                        '配对密钥：${device.pairingKey}',
                        style: const TextStyle(
                          fontFamily: 'monospace',
                          fontSize: 16,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}
