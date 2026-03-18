"""
AgentLinker Controller Client
主控端客户端 - 支持一对多控制、批量执行、设备分组
"""

import asyncio
import json
import os
import platform
import sys
import time
import uuid
from typing import Dict, Optional, List
from pathlib import Path

import websockets
from websockets.exceptions import ConnectionClosed

# 导入批量执行和分组模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))
from batch_executor import BatchExecutor, DeviceGroup, DeviceStatus
from file_transfer import FileTransfer


class ControllerClient:
    """主控端客户端 - 可以控制多个设备"""
    
    def __init__(self, server_url: str):
        self.server_url = server_url
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.running = True
        self.controller_id: str = f"controller-{uuid.uuid4().hex[:8]}"
        self.connected_devices: Dict[str, dict] = {}  # device_id -> info
        self.pending_requests: Dict[str, asyncio.Future] = {}
        
        # 批量执行和设备分组
        self.batch_executor = BatchExecutor(self.send_command)
        self.device_group = DeviceGroup()
        
        # 命令历史
        self.command_history: List[dict] = []
        self.max_history = 100
        self.favorite_commands: List[dict] = []
        
        # 配置文件
        self.config_file = Path.home() / ".agentlinker" / "controller_config.json"
        self._load_controller_config()
    
    async def connect(self):
        """建立 WebSocket 连接"""
        print(f"连接到服务端：{self.server_url}")
        
        try:
            self.ws = await websockets.connect(
                self.server_url,
                ping_interval=None,
                close_timeout=10
            )
            
            # 发送握手消息
            await self.ws.send(json.dumps({
                "type": "controller_handshake",
                "controller_id": self.controller_id,
                "platform": platform.system(),
            }))
            
            # 等待响应
            response = await asyncio.wait_for(self.ws.recv(), timeout=10)
            resp_data = json.loads(response)
            
            if resp_data.get("type") == "controller_ready":
                print(f"✅ 控制器就绪：{self.controller_id}")
                return True
            else:
                print(f"握手失败：{resp_data}")
                return False
        
        except Exception as e:
            print(f"连接失败：{e}")
            return False
    
    async def pair_with_device(self, device_id: str, pairing_key: str) -> bool:
        """与设备配对"""
        print(f"正在配对设备：{device_id} ...")
        
        await self.ws.send(json.dumps({
            "type": "pair",
            "controller_id": self.controller_id,
            "device_id": device_id,
            "pairing_key": pairing_key
        }))
        
        # 等待配对结果
        response = await asyncio.wait_for(self.ws.recv(), timeout=10)
        resp_data = json.loads(response)
        
        if resp_data.get("type") == "paired":
            print(f"✅ 配对成功：{device_id}")
            self.connected_devices[device_id] = {
                "device_id": device_id,
                "paired_at": time.time(),
                "status": "online"
            }
            return True
        else:
            print(f"❌ 配对失败：{resp_data.get('msg', 'Unknown error')}")
            return False
    
    async def unpair_device(self, device_id: str):
        """解除配对"""
        await self.ws.send(json.dumps({
            "type": "unpair",
            "controller_id": self.controller_id,
            "device_id": device_id
        }))
        
        if device_id in self.connected_devices:
            del self.connected_devices[device_id]
        print(f"已解除配对：{device_id}")
    
    async def send_command(self, device_id: str, action: str, params: dict = None, timeout: int = 30) -> dict:
        """发送指令到设备"""
        if device_id not in self.connected_devices:
            return {"success": False, "error": f"Device {device_id} not connected"}
        
        req_id = str(uuid.uuid4())
        future = asyncio.get_event_loop().create_future()
        self.pending_requests[req_id] = future
        
        await self.ws.send(json.dumps({
            "type": "exec",
            "req_id": req_id,
            "device_id": device_id,
            "action": action,
            "params": params or {}
        }))
        
        try:
            result = await asyncio.wait_for(future, timeout=timeout)
            return result
        except asyncio.TimeoutError:
            return {"success": False, "error": "Request timeout"}
        finally:
            if req_id in self.pending_requests:
                del self.pending_requests[req_id]
    
    async def list_devices(self) -> list:
        """获取在线设备列表"""
        req_id = str(uuid.uuid4())
        future = asyncio.get_event_loop().create_future()
        self.pending_requests[req_id] = future
        
        await self.ws.send(json.dumps({
            "type": "list_devices",
            "req_id": req_id,
            "controller_id": self.controller_id
        }))
        
        try:
            result = await asyncio.wait_for(future, timeout=10)
            return result.get("devices", [])
        except asyncio.TimeoutError:
            return []
        finally:
            if req_id in self.pending_requests:
                del self.pending_requests[req_id]
    
    async def handle_messages(self):
        """处理服务端消息"""
        heartbeat_interval = 30
        
        while self.running:
            try:
                msg = await asyncio.wait_for(self.ws.recv(), timeout=heartbeat_interval)
                data = json.loads(msg)
                
                msg_type = data.get("type")
                
                if msg_type == "ping":
                    await self.ws.send(json.dumps({"type": "pong", "time": time.time()}))
                
                elif msg_type == "result":
                    req_id = data.get("req_id")
                    if req_id and req_id in self.pending_requests:
                        future = self.pending_requests[req_id]
                        if not future.done():
                            future.set_result(data)
                
                elif msg_type == "device_online":
                    device_id = data.get("device_id")
                    print(f"📱 设备上线：{device_id}")
                    if device_id in self.connected_devices:
                        self.connected_devices[device_id]["status"] = "online"
                
                elif msg_type == "device_offline":
                    device_id = data.get("device_id")
                    print(f"📴 设备离线：{device_id}")
                    if device_id in self.connected_devices:
                        self.connected_devices[device_id]["status"] = "offline"
                
                elif msg_type == "error":
                    req_id = data.get("req_id")
                    if req_id and req_id in self.pending_requests:
                        future = self.pending_requests[req_id]
                        if not future.done():
                            future.set_result({"success": False, "error": data.get("msg")})
                
            except asyncio.TimeoutError:
                try:
                    await self.ws.send(json.dumps({"type": "ping", "time": time.time()}))
                except:
                    break
            
            except ConnectionClosed:
                print("连接已关闭")
                break
            
            except Exception as e:
                print(f"消息处理错误：{e}")
                break
    
    async def run_interactive(self):
        """运行交互式命令行"""
        print("\n" + "=" * 60)
        print("AgentLinker 主控端 v2.2.0")
        print("=" * 60)
        print("\n📋 基本命令:")
        print("  pair <device_id> <key>    - 配对设备")
        print("  unpair <device_id>        - 解除配对")
        print("  list                      - 列出已配对设备")
        print("  scan                      - 扫描在线设备")
        print("  exec <device_id> <cmd>    - 执行命令")
        print("  info <device_id>          - 获取设备信息")
        print("\n🎯 批量操作 (v2.2.0 新增):")
        print("  batch <group_id> <cmd>    - 批量执行命令")
        print("  batch-all <cmd>           - 向所有设备执行命令")
        print("  batch-result              - 查看批量执行结果摘要")
        print("\n📁 设备分组 (v2.2.0 新增):")
        print("  group-create <id> <name>  - 创建分组")
        print("  group-list                - 列出分组")
        print("  group-add <device> <group>- 添加设备到分组")
        print("  group-devices <group>     - 列出分组设备")
        print("\n💾 文件传输 (v2.2.0 新增):")
        print("  upload <device> <local> <remote> - 上传文件")
        print("  download <device> <remote> <local> - 下载文件")
        print("  file-info <device> <path> - 查看文件信息")
        print("\n📜 命令历史:")
        print("  history                   - 查看命令历史")
        print("  favorite <cmd>            - 收藏命令")
        print("  favorites                 - 列出收藏命令")
        print("\n其他:")
        print("  help                      - 显示帮助")
        print("  quit                      - 退出")
        print("=" * 60 + "\n")
        
        # 启动消息处理任务
        message_task = asyncio.create_task(self.handle_messages())
        
        # 交互式命令行
        loop = asyncio.get_event_loop()
        while self.running:
            try:
                # 使用 run_in_executor 避免阻塞
                cmd = await loop.run_in_executor(None, input, "[controller]> ")
                cmd = cmd.strip()
                
                if not cmd:
                    continue
                
                parts = cmd.split()
                command = parts[0].lower()
                
                if command == "quit" or command == "exit":
                    self.running = False
                    break
                
                elif command == "pair" and len(parts) >= 3:
                    device_id = parts[1]
                    pairing_key = parts[2]
                    success = await self.pair_with_device(device_id, pairing_key)
                    print(f"配对{'成功' if success else '失败'}")
                
                elif command == "unpair" and len(parts) >= 2:
                    device_id = parts[1]
                    await self.unpair_device(device_id)
                
                elif command == "list":
                    if self.connected_devices:
                        print("\n已配对设备:")
                        for dev_id, info in self.connected_devices.items():
                            status = "🟢" if info["status"] == "online" else "🔴"
                            print(f"  {status} {dev_id}")
                    else:
                        print("暂无配对设备")
                
                elif command == "scan":
                    print("扫描在线设备...")
                    devices = await self.list_devices()
                    if devices:
                        print("\n在线设备:")
                        for dev in devices:
                            print(f"  📱 {dev['device_id']} (运行 {dev.get('online_duration', 0):.0f}秒)")
                    else:
                        print("暂无在线设备")
                
                elif command == "exec" and len(parts) >= 3:
                    device_id = parts[1]
                    shell_cmd = " ".join(parts[2:])
                    print(f"在 {device_id} 上执行：{shell_cmd}")
                    result = await self.send_command(device_id, "shell.exec", {"cmd": shell_cmd})
                    if result.get("success"):
                        data = result.get("data", {})
                        if data.get("stdout"):
                            print(data["stdout"])
                        if data.get("stderr"):
                            print("STDERR:", data["stderr"])
                    else:
                        print(f"执行失败：{result.get('error')}")
                
                elif command == "info" and len(parts) >= 2:
                    device_id = parts[1]
                    print(f"获取 {device_id} 信息...")
                    result = await self.send_command(device_id, "system.info")
                    if result.get("success"):
                        info = result.get("data", {})
                        print(f"\n系统信息:")
                        print(f"  主机名：{info.get('hostname')}")
                        print(f"  系统：{info.get('system')} {info.get('release')}")
                        print(f"  Python: {info.get('python_version')}")
                        print(f"  运行时间：{info.get('uptime')}")
                    else:
                        print(f"获取失败：{result.get('error')}")
                
                else:
                    print(f"未知命令：{cmd}")
                    print("输入 'list' 查看可用命令")
            
            except EOFError:
                self.running = False
                break
            except Exception as e:
                print(f"命令执行错误：{e}")
        
        # 清理
        message_task.cancel()
        try:
            await message_task
        except asyncio.CancelledError:
            pass
    
    async def run(self):
        """主循环"""
        while self.running:
            if await self.connect():
                await self.run_interactive()
            
            if self.running:
                print("5 秒后重连...")
                await asyncio.sleep(5)
    
    def stop(self):
        """停止客户端"""
        self.running = False
        if self.ws:
            asyncio.create_task(self.ws.close())


async def main():
    """主函数"""
    if len(sys.argv) < 2:
        server_url = "ws://localhost:8080/ws/controller"
    else:
        server_url = sys.argv[1]
    
    controller = ControllerClient(server_url)
    
    try:
        await controller.run()
    except KeyboardInterrupt:
        print("\n用户中断")
    except Exception as e:
        print(f"运行时错误：{e}")
    
    print("控制器已退出")


if __name__ == "__main__":
    asyncio.run(main())
