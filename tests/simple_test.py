#!/usr/bin/env python3
"""简单测试二维码和发现功能"""

import sys
import json
sys.path.insert(0, '/tmp/AgentLinker/client/utils')

from discovery import LANDiscovery, QRCodePairing

print("=" * 60)
print(" AgentLinker 功能测试")
print("=" * 60)

# 测试 1: 二维码生成
print("\n1️⃣  测试二维码生成...\n")
qr = QRCodePairing()
qr_content = qr.generate_pairing_qr(
    device_id="test-server-001",
    pairing_key="XK9M2P7Q",
    device_name="测试服务器"
)
print("二维码内容:")
print(json.dumps(json.loads(qr_content), indent=2, ensure_ascii=False))

# 测试解析
result = qr.parse_pairing_qr(qr_content)
print(f"\n✅ 解析结果:")
print(f"   设备 ID: {result['device_id']}")
print(f"   配对密钥：{result['pairing_key']}")
print(f"   设备名：{result.get('device_name')}")

# 测试 2: 局域网发现
print("\n2️⃣  测试局域网发现...\n")

discovered = []

def on_found(device):
    print(f"📱 发现设备：{device.device_name}")
    print(f"   IP: {device.ip_address}:{device.port}")
    print(f"   平台：{device.platform}")
    discovered.append(device)

discovery = LANDiscovery()
discovery.on_device_found = on_found

print("开始监听 (5 秒)...")
discovery.start_listener(timeout=5.0)

import time
time.sleep(6)

discovery.stop()

print(f"\n搜索完成，发现 {len(discovered)} 个设备")

# 测试 3: 广播
print("\n3️⃣  测试广播功能...\n")

beacon = LANDiscovery(device_id="beacon-test", device_name="信标测试")
print("开始广播...")
beacon.start_broadcast(port=8080, extra_info={"pairing_key": "TEST1234"})

time.sleep(3)
beacon.stop()
print("广播已停止")

print("\n" + "=" * 60)
print(" ✅ 所有基础功能测试完成!")
print("=" * 60)
