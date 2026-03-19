#!/usr/bin/env python3
"""
AgentLinker 二维码配对 & 局域网发现演示
"""

import asyncio
import json
import sys
import time
from pathlib import Path

# 添加模块路径
sys.path.insert(0, str(Path(__file__).parent / "client" / "utils"))

from discovery import LANDiscovery, QRCodePairing, DiscoveredDevice


async def demo_qr_pairing():
    """演示二维码配对"""
    print("\n" + "=" * 60)
    print(" 📱 演示：二维码配对")
    print("=" * 60 + "\n")
    
    qr = QRCodePairing()
    
    # 生成配对二维码
    print("1️⃣  在被控端生成二维码...\n")
    
    qr_content = qr.generate_pairing_qr(
        device_id="demo-server-001",
        pairing_key="XK9M2P7Q",
        device_name="演示服务器",
        server_url="ws://192.168.1.100:8080/ws/client"
    )
    
    print("二维码内容:")
    print(json.dumps(json.loads(qr_content), indent=2, ensure_ascii=False))
    print()
    
    # 在终端打印二维码
    print("2️⃣  主控端扫描二维码:\n")
    qr.print_qr_terminal(qr_content)
    
    # 解析二维码
    print("3️⃣  解析二维码信息:\n")
    result = qr.parse_pairing_qr(qr_content)
    
    if result:
        print("✅ 解析成功!")
        print(f"   设备 ID: {result['device_id']}")
        print(f"   设备名：{result.get('device_name', 'N/A')}")
        print(f"   配对密钥：{result['pairing_key']}")
        print(f"   服务端：{result.get('server_url', 'N/A')}")
    else:
        print("❌ 解析失败")
    
    print("\n" + "=" * 60 + "\n")


async def demo_lan_discovery():
    """演示局域网发现"""
    print("\n" + "=" * 60)
    print(" 📡 演示：局域网发现")
    print("=" * 60 + "\n")
    
    # 启动一个模拟设备广播
    print("1️⃣  启动模拟设备广播...\n")
    
    beacon = LANDiscovery(
        device_id="demo-beacon-001",
        device_name="演示信标"
    )
    
    beacon.start_broadcast(
        port=8080,
        extra_info={"pairing_key": "DEMO123"}
    )
    
    # 启动监听器
    print("2️⃣  启动主控端监听...\n")
    
    discovered = []
    
    def on_found(device: DiscoveredDevice):
        discovered.append(device)
        print(f"\n📱 发现设备:")
        print(f"   设备名：{device.device_name}")
        print(f"   设备 ID: {device.device_id}")
        print(f"   IP 地址：{device.ip_address}:{device.port}")
        print(f"   平台：{device.platform}")
        if device.pairing_key:
            print(f"   🔑 配对密钥：{device.pairing_key}")
    
    listener = LANDiscovery()
    listener.on_device_found = on_found
    listener.start_listener(timeout=5.0)
    
    # 等待发现
    await asyncio.sleep(6)
    
    # 停止
    beacon.stop()
    listener.stop()
    
    # 显示结果
    print("\n" + "=" * 60)
    print(f"搜索完成，共发现 {len(discovered)} 个设备")
    print("=" * 60 + "\n")
    
    if discovered:
        print("可以开始配对:")
        for dev in discovered:
            if dev.pairing_key:
                print(f"  agentlinker pair {dev.device_id} {dev.pairing_key}")
    
    print()


async def demo_interactive():
    """演示交互式配对"""
    print("\n" + "=" * 60)
    print(" 🎮 演示：交互式配对流程")
    print("=" * 60 + "\n")
    
    print("模拟主控端交互界面:\n")
    
    # 模拟发现设备
    devices = [
        DiscoveredDevice(
            device_id="server-001",
            device_name="阿里云服务器",
            ip_address="43.98.243.80",
            port=8080,
            platform="Linux 5.15.0",
            last_seen=time.time(),
            pairing_key="XK9M2P7Q"
        ),
        DiscoveredDevice(
            device_id="macbook-pro",
            device_name="MacBook Pro",
            ip_address="192.168.1.105",
            port=8080,
            platform="macOS 14.0",
            last_seen=time.time(),
            pairing_key="P3K8M2X9"
        )
    ]
    
    print("发现以下设备:")
    for i, dev in enumerate(devices, 1):
        status = "🟢" if dev.pairing_key else "🔴"
        print(f"  {i}. {status} {dev.device_name} @ {dev.ip_address}")
    
    print("\n选择设备编号：1")
    selected = devices[0]
    
    print(f"\n正在配对 {selected.device_name}...")
    print(f"使用配对密钥：{selected.pairing_key}")
    print("✅ 配对成功!\n")
    
    print("现在可以开始控制设备:")
    print(f"  [controller]> exec {selected.device_id} df -h")
    print(f"  [controller]> info {selected.device_id}")
    print()


async def main():
    """主演示函数"""
    print("\n" + "🚀" * 30)
    print(" AgentLinker 新功能演示")
    print(" 二维码配对 | 局域网发现 | 交互式配对")
    print("🚀" * 30 + "\n")
    
    # 演示 1: 二维码配对
    await demo_qr_pairing()
    
    # 演示 2: 局域网发现
    await demo_lan_discovery()
    
    # 演示 3: 交互式配对
    await demo_interactive()
    
    print("\n" + "=" * 60)
    print(" ✨ 演示完成!")
    print("=" * 60)
    print("\n📚 查看完整文档:")
    print("   docs/二维码配对指南.md")
    print("\n💻 开始使用:")
    print("   agentlinker --mode controller")
    print("   [controller]> discover")
    print("   [controller]> qr-pair")
    print("\n🔗 GitHub: https://github.com/Royean/AgentLinker")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
