#!/usr/bin/env python3
"""测试客户端与服务端连接和配对"""

import asyncio
import json
import sys
import time
import websockets

SERVER_URL = "ws://127.0.0.1:8080/ws/client"
CONTROLLER_URL = "ws://127.0.0.1:8080/ws/controller"
DEVICE_TOKEN = "ah_device_token_change_in_production"

async def test_device_connection():
    """测试设备连接"""
    print("\n" + "=" * 60)
    print("测试 1: 设备连接服务端")
    print("=" * 60 + "\n")
    
    device_id = "test-device-001"
    
    try:
        ws = await websockets.connect(SERVER_URL)
        
        # 注册
        await ws.send(json.dumps({
            "type": "register",
            "device_id": device_id,
            "device_name": "测试设备",
            "token": DEVICE_TOKEN,
            "platform": "Linux"
        }))
        
        # 等待注册响应
        response = await asyncio.wait_for(ws.recv(), timeout=10)
        data = json.loads(response)
        
        if data.get("type") == "registered":
            print(f"✅ 设备注册成功!")
            print(f"   设备 ID: {device_id}")
            print(f"   设备名：{data.get('device_name')}")
        else:
            print(f"❌ 注册失败：{data}")
            await ws.close()
            return None
        
        # 等待配对密钥
        response = await asyncio.wait_for(ws.recv(), timeout=10)
        data = json.loads(response)
        
        if data.get("type") == "pairing_key":
            pairing_key = data.get("pairing_key")
            print(f"✅ 收到配对密钥：{pairing_key}")
            print(f"   设备已就绪，等待控制器连接...")
            
            return ws, pairing_key
        else:
            print(f"❌ 未收到配对密钥：{data}")
            await ws.close()
            return None
            
    except Exception as e:
        print(f"❌ 连接失败：{e}")
        return None

async def test_controller_connection(pairing_key: str):
    """测试控制器连接和配对"""
    print("\n" + "=" * 60)
    print("测试 2: 控制器连接和配对")
    print("=" * 60 + "\n")
    
    try:
        ws = await websockets.connect(CONTROLLER_URL)
        
        # 握手
        await ws.send(json.dumps({
            "type": "controller_handshake",
            "controller_id": "test-controller-001",
            "platform": "Linux"
        }))
        
        response = await asyncio.wait_for(ws.recv(), timeout=10)
        data = json.loads(response)
        
        if data.get("type") == "controller_ready":
            print(f"✅ 控制器就绪!")
            print(f"   控制器 ID: {data.get('controller_id')}")
        else:
            print(f"❌ 握手失败：{data}")
            await ws.close()
            return False
        
        # 配对设备
        print(f"\n正在配对设备 (密钥：{pairing_key})...")
        await ws.send(json.dumps({
            "type": "pair",
            "controller_id": "test-controller-001",
            "device_id": "test-device-001",
            "pairing_key": pairing_key
        }))
        
        response = await asyncio.wait_for(ws.recv(), timeout=10)
        data = json.loads(response)
        
        if data.get("type") == "paired":
            print(f"✅ 配对成功!")
            print(f"   设备 ID: test-device-001")
            return ws
        else:
            print(f"❌ 配对失败：{data.get('msg')}")
            await ws.close()
            return None
            
    except Exception as e:
        print(f"❌ 控制器连接失败：{e}")
        return None

async def test_command_execution(controller_ws):
    """测试指令执行"""
    print("\n" + "=" * 60)
    print("测试 3: 指令执行")
    print("=" * 60 + "\n")
    
    import uuid
    
    # 发送执行指令
    req_id = str(uuid.uuid4())
    await controller_ws.send(json.dumps({
        "type": "exec",
        "req_id": req_id,
        "device_id": "test-device-001",
        "action": "shell.exec",
        "params": {"cmd": "echo 'Hello from AgentLinker!'"}
    }))
    
    print("发送指令：shell.exec (echo 'Hello from AgentLinker!')")
    
    # 等待结果
    try:
        response = await asyncio.wait_for(controller_ws.recv(), timeout=30)
        data = json.loads(response)
        
        if data.get("type") == "result":
            result_data = data.get("data", {})
            if result_data.get("success"):
                stdout = result_data.get("data", {}).get("stdout", "")
                print(f"✅ 指令执行成功!")
                print(f"   输出：{stdout.strip()}")
                return True
            else:
                print(f"❌ 指令执行失败：{result_data.get('error')}")
        else:
            print(f"❌ 意外响应：{data}")
    except asyncio.TimeoutError:
        print("❌ 等待响应超时")
    
    return False

async def main():
    print("\n🚀 AgentLinker 端到端测试")
    print("=" * 60)
    
    # 测试 1: 设备连接
    device_result = await test_device_connection()
    
    if not device_result:
        print("\n❌ 设备连接测试失败，终止后续测试")
        return
    
    device_ws, pairing_key = device_result
    
    # 测试 2: 控制器连接和配对
    controller_ws = await test_controller_connection(pairing_key)
    
    if not controller_ws:
        print("\n❌ 控制器测试失败")
        device_ws.close()
        return
    
    # 测试 3: 指令执行
    await test_command_execution(controller_ws)
    
    # 清理
    print("\n" + "=" * 60)
    print("清理连接...")
    await device_ws.close()
    await controller_ws.close()
    
    print("\n✅ 所有测试完成!\n")

if __name__ == "__main__":
    asyncio.run(main())
