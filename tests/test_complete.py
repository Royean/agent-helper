#!/usr/bin/env python3
"""完整的端到端测试 - 设备保持连接"""

import asyncio
import json
import sys
import time
import uuid
import websockets

SERVER_URL = "ws://127.0.0.1:8080/ws/client"
CONTROLLER_URL = "ws://127.0.0.1:8080/ws/controller"
DEVICE_TOKEN = "ah_device_token_change_in_production"

class DeviceClient:
    """模拟设备客户端"""
    
    def __init__(self):
        self.ws = None
        self.device_id = "test-device-002"
        self.pairing_key = None
        self.running = True
    
    async def connect(self):
        print(f"\n📱 设备连接服务端...")
        self.ws = await websockets.connect(SERVER_URL)
        
        # 注册
        await self.ws.send(json.dumps({
            "type": "register",
            "device_id": self.device_id,
            "device_name": "测试设备 002",
            "token": DEVICE_TOKEN,
            "platform": "Linux"
        }))
        
        # 等待注册响应
        response = await self.ws.recv()
        data = json.loads(response)
        
        if data.get("type") == "registered":
            print(f"✅ 设备注册成功：{self.device_id}")
        else:
            print(f"❌ 注册失败：{data}")
            return False
        
        # 等待配对密钥
        response = await self.ws.recv()
        data = json.loads(response)
        
        if data.get("type") == "pairing_key":
            self.pairing_key = data.get("pairing_key")
            print(f"✅ 配对密钥：{self.pairing_key}")
            return True
        
        return False
    
    async def handle_messages(self):
        """处理服务端消息（心跳和执行指令）"""
        print(f"🔄 设备开始处理消息...")
        
        while self.running:
            try:
                msg = await asyncio.wait_for(self.ws.recv(), timeout=1.0)
                data = json.loads(msg)
                
                msg_type = data.get("type")
                
                if msg_type == "ping":
                    await self.ws.send(json.dumps({"type": "pong", "time": time.time()}))
                
                elif msg_type == "exec":
                    req_id = data.get("req_id")
                    action = data.get("action")
                    params = data.get("params", {})
                    
                    print(f"📥 收到指令：{action} (req_id: {req_id})")
                    
                    # 执行指令
                    result = await self.execute_action(action, params)
                    
                    # 返回结果
                    await self.ws.send(json.dumps({
                        "type": "result",
                        "req_id": req_id,
                        "success": result.get("success", False),
                        "data": result
                    }))
                    
                    print(f"📤 指令执行完成：{result.get('success')}")
                
            except asyncio.TimeoutError:
                pass
            except Exception as e:
                print(f"设备消息处理错误：{e}")
                break
    
    async def execute_action(self, action: str, params: dict):
        """执行指令"""
        if action == "shell.exec":
            cmd = params.get("cmd", "")
            import subprocess
            try:
                result = subprocess.run(
                    cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                return {
                    "success": result.returncode == 0,
                    "returncode": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr
                }
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        elif action == "system.info":
            import platform
            return {
                "success": True,
                "data": {
                    "hostname": "test-host",
                    "system": platform.system(),
                    "release": platform.release(),
                    "python_version": platform.python_version()
                }
            }
        
        return {"success": False, "error": f"Unknown action: {action}"}
    
    def stop(self):
        self.running = False
        if self.ws:
            asyncio.create_task(self.ws.close())


class ControllerClient:
    """模拟控制器客户端"""
    
    def __init__(self):
        self.ws = None
        self.controller_id = "test-controller-002"
    
    async def connect(self):
        print(f"\n🎮 控制器连接服务端...")
        self.ws = await websockets.connect(CONTROLLER_URL)
        
        # 握手
        await self.ws.send(json.dumps({
            "type": "controller_handshake",
            "controller_id": self.controller_id,
            "platform": "Linux"
        }))
        
        response = await self.ws.recv()
        data = json.loads(response)
        
        if data.get("type") == "controller_ready":
            print(f"✅ 控制器就绪：{self.controller_id}")
            return True
        
        return False
    
    async def pair(self, device_id: str, pairing_key: str):
        """配对设备"""
        print(f"\n🔗 正在配对设备 {device_id}...")
        
        await self.ws.send(json.dumps({
            "type": "pair",
            "controller_id": self.controller_id,
            "device_id": device_id,
            "pairing_key": pairing_key
        }))
        
        response = await self.ws.recv()
        data = json.loads(response)
        
        if data.get("type") == "paired":
            print(f"✅ 配对成功!")
            return True
        else:
            print(f"❌ 配对失败：{data.get('msg')}")
            return False
    
    async def exec_command(self, device_id: str, action: str, params: dict = None):
        """执行指令"""
        req_id = str(uuid.uuid4())
        
        print(f"\n⚡ 发送指令：{action}")
        
        await self.ws.send(json.dumps({
            "type": "exec",
            "req_id": req_id,
            "device_id": device_id,
            "action": action,
            "params": params or {}
        }))
        
        # 等待结果
        try:
            response = await asyncio.wait_for(self.ws.recv(), timeout=30)
            data = json.loads(response)
            
            if data.get("type") == "result":
                result = data.get("data", {})
                print(f"✅ 指令执行成功!")
                return result
            else:
                print(f"❌ 意外响应：{data}")
                return None
        
        except asyncio.TimeoutError:
            print("❌ 等待响应超时")
            return None


async def main():
    print("\n🚀 AgentLinker 完整端到端测试")
    print("=" * 60)
    
    # 启动设备
    device = DeviceClient()
    if not await device.connect():
        print("❌ 设备连接失败")
        return
    
    # 启动设备消息处理任务
    device_task = asyncio.create_task(device.handle_messages())
    
    # 等待一下让设备完全连接
    await asyncio.sleep(1)
    
    # 启动控制器
    controller = ControllerClient()
    if not await controller.connect():
        print("❌ 控制器连接失败")
        device.stop()
        return
    
    # 配对
    if not await controller.pair(device.device_id, device.pairing_key):
        print("❌ 配对失败")
        device.stop()
        return
    
    # 等待配对传播
    await asyncio.sleep(0.5)
    
    # 测试指令执行
    print("\n" + "=" * 60)
    print("测试指令执行")
    print("=" * 60)
    
    # 测试 1: shell 命令
    result = await controller.exec_command(
        device.device_id,
        "shell.exec",
        {"cmd": "echo 'Hello from AgentLinker!'"}
    )
    
    if result and result.get("success"):
        data = result.get("data", {})
        print(f"   输出：{data.get('stdout', '').strip()}")
    
    # 测试 2: 系统信息
    result = await controller.exec_command(
        device.device_id,
        "system.info",
        {}
    )
    
    if result and result.get("success"):
        info = result.get("data", {})
        print(f"\n系统信息:")
        print(f"   主机名：{info.get('hostname')}")
        print(f"   系统：{info.get('system')}")
        print(f"   Python: {info.get('python_version')}")
    
    # 清理
    print("\n" + "=" * 60)
    print("清理连接...")
    
    device.stop()
    device_task.cancel()
    try:
        await device_task
    except asyncio.CancelledError:
        pass
    
    if controller.ws:
        await controller.ws.close()
    
    print("\n✅ 所有测试完成!\n")


if __name__ == "__main__":
    asyncio.run(main())
