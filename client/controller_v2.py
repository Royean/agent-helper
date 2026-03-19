"""
AgentLinker Controller Client v2
主控端客户端 - 支持一对多控制、局域网发现、二维码配对、文件传输
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

# 导入发现和配对模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'utils'))
try:
    from discovery import LANDiscovery, QRCodePairing, DiscoveredDevice
except ImportError:
    print("⚠️ 发现模块未找到，局域网发现功能将不可用")
    LANDiscovery = None
    QRCodePairing = None

# 导入文件传输模块
try:
    from .file_transfer import FileTransfer
except ImportError:
    try:
        from file_transfer import FileTransfer
    except ImportError:
        print("⚠️ 文件传输模块未找到")
        FileTransfer = None


class ControllerClient:
    """主控端客户端 - 可以控制多个设备"""
    
    def __init__(self, server_url: str):
        self.server_url = server_url
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.running = True
        self.controller_id: str = f"controller-{uuid.uuid4().hex[:8]}"
        self.connected_devices: Dict[str, dict] = {}
        self.pending_requests: Dict[str, asyncio.Future] = {}
        self.discovery: Optional[LANDiscovery] = None
        self.qr: Optional[QRCodePairing] = None
        self.file_transfer: Optional[FileTransfer] = None
        self.active_transfers: Dict[str, dict] = {}  # 活跃的传输任务
        
        if LANDiscovery:
            self.discovery = LANDiscovery()
        if QRCodePairing:
            self.qr = QRCodePairing()
        if FileTransfer:
            self.file_transfer = FileTransfer()
    
    async def connect(self):
        """建立 WebSocket 连接"""
        print(f"连接到服务端：{self.server_url}")
        
        try:
            self.ws = await websockets.connect(
                self.server_url,
                ping_interval=None,
                close_timeout=10
            )
            
            await self.ws.send(json.dumps({
                "type": "controller_handshake",
                "controller_id": self.controller_id,
                "platform": platform.system(),
            }))
            
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
    
    async def pair_from_qr(self, qr_content: str) -> bool:
        """从二维码配对"""
        if not self.qr:
            print("❌ 二维码模块不可用")
            return False
        
        print("📷 解析二维码...")
        result = self.qr.parse_pairing_qr(qr_content)
        
        if not result:
            print("❌ 无效的二维码")
            return False
        
        device_id = result.get("device_id")
        pairing_key = result.get("pairing_key")
        
        if not device_id or not pairing_key:
            print("❌ 二维码信息不完整")
            return False
        
        print(f"📱 设备：{result.get('device_name', device_id)}")
        print(f"🔑 配对密钥：{pairing_key}")
        
        # 如果二维码包含服务端 URL，切换连接
        if result.get("server_url"):
            print(f"🌐 使用服务端：{result['server_url']}")
            # 可以在这里切换服务端
        
        return await self.pair_with_device(device_id, pairing_key)
    
    async def discover_lan_devices(self, timeout: int = 10) -> List[DiscoveredDevice]:
        """发现局域网设备"""
        if not self.discovery:
            print("❌ 发现模块不可用")
            return []
        
        print("📡 正在搜索局域网设备...\n")
        
        discovered = []
        
        def on_found(device: DiscoveredDevice):
            print(f"📱 发现设备：{device.device_name}")
            print(f"   IP: {device.ip_address}:{device.port}")
            print(f"   平台：{device.platform}")
            if device.pairing_key:
                print(f"   配对密钥：{device.pairing_key}")
            print()
            discovered.append(device)
        
        self.discovery.on_device_found = on_found
        self.discovery.start_listener(timeout=float(timeout))
        
        await asyncio.sleep(timeout)
        self.discovery.stop()
        
        print(f"\n搜索完成，共发现 {len(discovered)} 个设备")
        return discovered
    
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
        print(" AgentLinker 主控端 v2.0")
        print(" 支持：一对多控制 | 局域网发现 | 二维码配对")
        print("=" * 60)
        print("\n📋 可用命令:")
        print("  配对:")
        print("    pair <device_id> <pairing_key>  - 手动配对设备")
        print("    qr-pair                         - 扫描二维码配对")
        print("    discover                        - 发现局域网设备")
        print()
        print("  控制:")
        print("    list                            - 列出已配对设备")
        print("    scan                            - 扫描在线设备")
        print("    exec <device_id> <command>      - 执行命令")
        print("    info <device_id>                - 获取设备信息")
        print("    unpair <device_id>              - 解除配对")
        print()
        print("  其他:")
       ("    help                            - 显示帮助")
        print("    quit                            - 退出")
        print("=" * 60 + "\n")
        
        message_task = asyncio.create_task(self.handle_messages())
        
        loop = asyncio.get_event_loop()
        while self.running:
            try:
                cmd = await loop.run_in_executor(None, input, "[controller]> ")
                cmd = cmd.strip()
                
                if not cmd:
                    continue
                
                parts = cmd.split()
                command = parts[0].lower()
                
                if command == "quit" or command == "exit":
                    self.running = False
                    break
                
                elif command == "help":
                    self._print_help()
                
                elif command == "pair" and len(parts) >= 3:
                    device_id = parts[1]
                    pairing_key = parts[2]
                    success = await self.pair_with_device(device_id, pairing_key)
                    print(f"配对{'成功' if success else '失败'}")
                
                elif command == "qr-pair":
                    print("\n📱 请扫描设备上的二维码")
                    print("   或输入二维码内容 (JSON):")
                    print("   (输入单行 JSON 后按回车)\n")
                    
                    try:
                        qr_input = await loop.run_in_executor(None, input, "二维码内容：")
                        success = await self.pair_from_qr(qr_input.strip())
                        print(f"配对{'成功' if success else '失败'}")
                    except EOFError:
                        pass
                
                elif command == "discover":
                    timeout = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 10
                    devices = await self.discover_lan_devices(timeout=timeout)
                    
                    if devices:
                        print("\n选择设备进行配对:")
                        for i, dev in enumerate(devices, 1):
                            status = "🟢" if dev.pairing_key else "🔴"
                            print(f"  {i}. {status} {dev.device_name} @ {dev.ip_address}")
                        
                        try:
                            choice = await loop.run_in_executor(None, input, "\n选择设备编号 (或 q 退出): ")
                            if choice.lower() != 'q' and choice.isdigit():
                                idx = int(choice) - 1
                                if 0 <= idx < len(devices):
                                    selected = devices[idx]
                                    if selected.pairing_key:
                                        print(f"\n正在配对 {selected.device_name}...")
                                        success = await self.pair_with_device(
                                            selected.device_id, 
                                            selected.pairing_key
                                        )
                                        if success:
                                            print("✅ 配对成功!")
                                    else:
                                        print(f"\n需要在设备日志中查看配对密钥")
                                        print(f"设备 ID: {selected.device_id}")
                        except (EOFError, ValueError):
                            pass
                
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
                    print("输入 'help' 查看可用命令")
            
            except EOFError:
                self.running = False
                break
            except Exception as e:
                print(f"命令执行错误：{e}")
        
        message_task.cancel()
        try:
            await message_task
        except asyncio.CancelledError:
            pass
    
    def _print_help(self):
        """打印帮助信息"""
        print("\n" + "=" * 60)
        print(" AgentLinker 帮助")
        print("=" * 60)
        print("""
配对命令:
  pair <device_id> <key>    - 使用设备 ID 和配对密钥配对
  qr-pair                   - 扫描二维码配对
  discover [timeout]        - 发现局域网设备 (默认 10 秒)

控制命令:
  list                      - 列出已配对设备
  scan                      - 扫描服务端在线设备
  exec <id> <cmd>           - 在设备上执行命令
  info <id>                 - 获取设备系统信息
  unpair <id>               - 解除设备配对

其他:
  help                      - 显示此帮助
  quit/exit                 - 退出程序

示例:
  pair my-server XK9M2P7Q   - 配对设备
  exec my-server df -h      - 查看磁盘空间
  info my-server            - 查看系统信息
        """)
        print("=" * 60 + "\n")
    
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
        if self.discovery:
            self.discovery.stop()
    
    # ========== 文件传输方法 ==========
    
    async def upload_file(
        self,
        device_id: str,
        local_path: str,
        remote_path: Optional[str] = None,
        progress_callback: Optional[callable] = None
    ) -> dict:
        """
        上传文件到设备
        
        Args:
            device_id: 目标设备 ID
            local_path: 本地文件路径
            remote_path: 远程保存路径（可选）
            progress_callback: 进度回调函数
        
        Returns:
            传输结果
        """
        if not self.file_transfer:
            return {"success": False, "error": "文件传输模块未初始化"}
        
        if device_id not in self.connected_devices:
            return {"success": False, "error": f"设备 {device_id} 未连接"}
        
        # 生成文件 ID
        file_id = f"{Path(local_path).name}_{int(time.time())}"
        
        # 发送文件传输请求
        await self.ws.send(json.dumps({
            "type": "file_upload_request",
            "file_id": file_id,
            "device_id": device_id,
            "filename": Path(local_path).name,
            "remote_path": remote_path
        }))
        
        # 等待确认
        response = await asyncio.wait_for(self.ws.recv(), timeout=10)
        resp_data = json.loads(response)
        
        if resp_data.get("type") != "file_upload_accepted":
            return {"success": False, "error": resp_data.get("msg", "上传请求被拒绝")}
        
        # 开始传输
        print(f"📤 开始上传：{Path(local_path).name}")
        
        async def send_chunk(data):
            await self.ws.send(json.dumps(data))
        
        result = await self.file_transfer.upload_file(
            file_path=local_path,
            send_callback=send_chunk,
            progress_callback=progress_callback
        )
        
        if result.get("success"):
            print(f"✅ 上传完成：{result.get('filename')}")
            print(f"   大小：{result.get('file_size')} bytes")
            print(f"   耗时：{result.get('duration'):.2f}s")
            print(f"   速度：{result.get('speed', 0)/1024:.1f} KB/s")
        
        return result
    
    async def download_file(
        self,
        device_id: str,
        remote_path: str,
        local_path: str,
        progress_callback: Optional[callable] = None
    ) -> dict:
        """
        从设备下载文件
        
        Args:
            device_id: 目标设备 ID
            remote_path: 远程文件路径
            local_path: 本地保存路径
            progress_callback: 进度回调函数
        
        Returns:
            传输结果
        """
        if not self.file_transfer:
            return {"success": False, "error": "文件传输模块未初始化"}
        
        if device_id not in self.connected_devices:
            return {"success": False, "error": f"设备 {device_id} 未连接"}
        
        # 生成文件 ID
        file_id = f"download_{int(time.time())}"
        
        # 发送下载请求
        await self.ws.send(json.dumps({
            "type": "file_download_request",
            "file_id": file_id,
            "device_id": device_id,
            "remote_path": remote_path
        }))
        
        print(f"📥 开始下载：{remote_path}")
        
        # 等待接收文件数据
        # (实际实现需要在消息处理中接收分块)
        
        return {"success": False, "error": "下载功能开发中"}
    
    async def list_remote_files(
        self,
        device_id: str,
        path: str = "/"
    ) -> dict:
        """
        列出远程设备文件
        
        Args:
            device_id: 目标设备 ID
            path: 远程路径
        
        Returns:
            文件列表
        """
        if device_id not in self.connected_devices:
            return {"success": False, "error": f"设备 {device_id} 未连接"}
        
        req_id = str(uuid.uuid4())
        future = asyncio.get_event_loop().create_future()
        self.pending_requests[req_id] = future
        
        await self.ws.send(json.dumps({
            "type": "list_files",
            "req_id": req_id,
            "device_id": device_id,
            "path": path
        }))
        
        try:
            result = await asyncio.wait_for(future, timeout=30)
            return result
        except asyncio.TimeoutError:
            return {"success": False, "error": "请求超时"}
        finally:
            if req_id in self.pending_requests:
                del self.pending_requests[req_id]
    
    def get_transfer_progress(self, file_id: str) -> Optional[dict]:
        """获取传输进度"""
        if not self.file_transfer:
            return None
        
        return self.file_transfer.get_progress(file_id)
    
    def cancel_transfer(self, file_id: str) -> bool:
        """取消传输"""
        if file_id in self.active_transfers:
            self.active_transfers[file_id]["cancelled"] = True
            return True
        return False


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
