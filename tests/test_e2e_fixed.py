#!/usr/bin/env python3
"""端到端测试脚本 - 修复版"""

import asyncio
import json
import sys
import time
import uuid

sys.path.insert(0, '/tmp/AgentLinker/client')
sys.path.insert(0, '/tmp/AgentLinker/client/core')

from core import Config, AgentClient, generate_device_id
import websockets

async def test_end_to_end():
    print("=" * 60)
    print("AgentLinker 端到端测试")
    print("=" * 60)
    
    # 1. 启动被控端
    print("\n[1/5] 启动被控端...")
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
    
    # 启动消息处理任务（后台）
    pairing_key_received = asyncio.Event()
    pairing_key = None
    
    async def handle_messages():
        nonlocal pairing_key
        try:
            while client.running and client.ws:
                msg = await asyncio.wait_for(client.ws.recv(), timeout=30)
                data = json.loads(msg)
                msg_type = data.get("type")
                
                if msg_type == "pairing_key":
                    pairing_key = data.get("pairing_key")
                    print(f"🔑 收到配对密钥：{pairing_key}")
                    pairing_key_received.set()
                elif msg_type == "ping":
                    await client.ws.send(json.dumps({"type": "pong", "time": time.time()}))
                elif msg_type == "exec":
                    # 执行指令并返回结果
                    req_id = data.get("req_id")
                    action = data.get("action")
                    params = data.get("params", {})
                    
                    from core import Executor
                    result = Executor.execute(action, params)
                    
                    await client.ws.send(json.dumps({
                        "type": "result",
                        "req_id": req_id,
                        "success": result.get("success", False),
                        "data": result
                    }))
        except asyncio.TimeoutError:
            pass
        except Exception as e:
            print(f"消息处理异常：{e}")
    
    message_task = asyncio.create_task(handle_messages())
    
    # 等待配对密钥
    print("等待配对密钥...")
    try:
        await asyncio.wait_for(pairing_key_received.wait(), timeout=10)
    except asyncio.TimeoutError:
        print("❌ 等待配对密钥超时")
        client.stop()
        message_task.cancel()
        return
    
    # 2. 连接控制器
    print("\n[2/5] 连接控制器...")
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
        message_task.cancel()
        return
    
    # 3. 配对设备
    print("\n[3/5] 配对设备...")
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
        message_task.cancel()
        return
    
    # 4. 测试执行命令
    print("\n[4/5] 测试执行命令...")
    req_id = str(uuid.uuid4())
    
    await controller_ws.send(json.dumps({
        "type": "exec",
        "req_id": req_id,
        "device_id": "test-device-e2e",
        "action": "shell.exec",
        "params": {"cmd": "echo 'Hello End-to-End Test!'"}
    }))
    
    # 等待响应
    try:
        resp = json.loads(await asyncio.wait_for(controller_ws.recv(), timeout=10))
        if resp.get("type") == "result":
            data = resp.get("data", {})
            output = data.get("stdout", "").strip()
            print(f"✅ 命令执行成功！输出：{output}")
        elif resp.get("type") == "error":
            print(f"❌ 执行错误：{resp.get('msg')}")
        else:
            print(f"❌ 未知响应：{resp}")
    except asyncio.TimeoutError:
        print("❌ 等待响应超时")
    
    # 5. 测试系统信息
    print("\n[5/5] 测试系统信息...")
    req_id = str(uuid.uuid4())
    
    await controller_ws.send(json.dumps({
        "type": "exec",
        "req_id": req_id,
        "device_id": "test-device-e2e",
        "action": "system.info",
        "params": {}
    }))
    
    try:
        resp = json.loads(await asyncio.wait_for(controller_ws.recv(), timeout=10))
        if resp.get("type") == "result":
            data = resp.get("data", {})
            print(f"✅ 系统信息获取成功！")
            print(f"   主机名：{data.get('hostname')}")
            print(f"   系统：{data.get('system')}")
            print(f"   Python: {data.get('python_version')}")
        else:
            print(f"❌ 获取失败：{resp}")
    except asyncio.TimeoutError:
        print("❌ 等待响应超时")
    
    # 清理
    print("\n清理中...")
    client.stop()
    await controller_ws.close()
    message_task.cancel()
    
    try:
        await message_task
    except asyncio.CancelledError:
        pass
    
    print("\n" + "=" * 60)
    print("✅ 端到端测试完成！")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_end_to_end())
