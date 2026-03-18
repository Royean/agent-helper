#!/usr/bin/env python3
"""端到端测试脚本"""

import asyncio
import json
import sys
import time

sys.path.insert(0, '/tmp/AgentLinker/client')
sys.path.insert(0, '/tmp/AgentLinker/client/core')

from core import Config, AgentClient, generate_device_id
import websockets

async def test_end_to_end():
    print("=" * 60)
    print("AgentLinker 端到端测试")
    print("=" * 60)
    
    # 1. 启动被控端
    print("\n[1/4] 启动被控端...")
    config = Config('/tmp/test_device.json')
    config.data = {
        'device_id': 'test-device-e2e',
        'device_name': 'E2E 测试设备',
        'token': 'ah_device_token_change_in_production',
        'server_url': 'ws://127.0.0.1:8080/ws/client'
    }
    config.save()
    
    client = AgentClient(config)
    connect_success = await client.connect()
    
    if not connect_success:
        print("❌ 被控端连接失败")
        return
    
    print("✅ 被控端已连接")
    
    # 等待配对密钥
    await asyncio.sleep(2)
    pairing_key = client.pairing_key
    print(f"🔑 配对密钥：{pairing_key}")
    
    if not pairing_key:
        print("❌ 未获取到配对密钥")
        client.stop()
        return
    
    # 2. 连接控制器
    print("\n[2/4] 连接控制器...")
    controller_ws = await websockets.connect("ws://127.0.0.1:8080/ws/controller")
    
    await controller_ws.send(json.dumps({
        "type": "controller_handshake",
        "controller_id": "test-controller-e2e",
        "platform": "Linux"
    }))
    
    resp = json.loads(await controller_ws.recv())
    if resp.get("type") == "controller_ready":
        print("✅ 控制器已连接")
    else:
        print(f"❌ 控制器握手失败：{resp}")
        client.stop()
        return
    
    # 3. 配对设备
    print("\n[3/4] 配对设备...")
    await controller_ws.send(json.dumps({
        "type": "pair",
        "controller_id": "test-controller-e2e",
        "device_id": "test-device-e2e",
        "pairing_key": pairing_key
    }))
    
    resp = json.loads(await controller_ws.recv())
    if resp.get("type") == "paired":
        print("✅ 配对成功")
    else:
        print(f"❌ 配对失败：{resp}")
        client.stop()
        return
    
    # 4. 测试执行命令
    print("\n[4/4] 测试执行命令...")
    
    # 创建 Future 等待结果
    import uuid
    req_id = str(uuid.uuid4())
    
    await controller_ws.send(json.dumps({
        "type": "exec",
        "req_id": req_id,
        "device_id": "test-device-e2e",
        "action": "shell.exec",
        "params": {"cmd": "echo 'Hello End-to-End Test!'" }
    }))
    
    # 等待响应
    try:
        resp = json.loads(await asyncio.wait_for(controller_ws.recv(), timeout=10))
        if resp.get("type") == "result":
            data = resp.get("data", {})
            output = data.get("stdout", "").strip()
            print(f"✅ 命令执行成功！输出：{output}")
        else:
            print(f"❌ 执行失败：{resp}")
    except asyncio.TimeoutError:
        print("❌ 等待响应超时")
    
    # 清理
    client.stop()
    await controller_ws.close()
    
    print("\n" + "=" * 60)
    print("✅ 端到端测试完成！")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_end_to_end())
