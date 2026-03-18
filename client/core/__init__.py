"""
AgentLinker Client Core
跨平台核心客户端逻辑
"""

import asyncio
import json
import os
import platform
import signal
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Dict, Any, Optional, Callable

import websockets
from websockets.exceptions import ConnectionClosed


class Config:
    """配置管理"""
    
    DEFAULT_CONFIG = {
        "device_id": "",
        "device_name": "",
        "token": "",
        "server_url": "wss://your-server.com/ws/linux",
        "reconnect_interval": 5,
        "heartbeat_interval": 30,
        "paired_controllers": []  # 已配对的控制器列表
    }
    
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.data = self._load()
    
    def _load(self) -> dict:
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                    return {**self.DEFAULT_CONFIG, **saved}
            except Exception as e:
                print(f"加载配置失败：{e}")
        return self.DEFAULT_CONFIG.copy()
    
    def save(self):
        try:
            Path(self.config_path).parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存配置失败：{e}")
    
    @property
    def device_id(self) -> str:
        return self.data.get("device_id", "")
    
    @device_id.setter
    def device_id(self, value: str):
        self.data["device_id"] = value
        self.save()
    
    @property
    def device_name(self) -> str:
        return self.data.get("device_name", "")
    
    @property
    def token(self) -> str:
        return self.data.get("token", "")
    
    @property
    def server_url(self) -> str:
        return self.data.get("server_url", "")
    
    @property
    def paired_controllers(self) -> list:
        return self.data.get("paired_controllers", [])
    
    def add_paired_controller(self, controller_id: str):
        if controller_id not in self.paired_controllers:
            self.paired_controllers.append(controller_id)
            self.save()


class Executor:
    """指令执行器 - 跨平台"""
    
    @staticmethod
    def execute(action: str, params: dict) -> Dict[str, Any]:
        """根据 action 分发执行"""
        handlers = {
            "system.info": Executor.system_info,
            "shell.exec": Executor.shell_exec,
            "file.list": Executor.file_list,
            "file.read": Executor.file_read,
            "file.write": Executor.file_write,
            "file.delete": Executor.file_delete,
            "process.list": Executor.process_list,
            "process.kill": Executor.process_kill,
            "service.operate": Executor.service_operate,
        }
        
        handler = handlers.get(action)
        if not handler:
            return {"success": False, "error": f"Unknown action: {action}"}
        
        try:
            return handler(params)
        except Exception as e:
            print(f"执行 {action} 失败：{e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def system_info(params: dict) -> Dict[str, Any]:
        """获取系统信息"""
        try:
            uname = platform.uname()
            system = platform.system()
            
            # 内存信息
            mem_info = {}
            if system == "Windows":
                import ctypes
                mem_info["note"] = "Windows memory info not implemented"
            elif system == "Darwin":  # macOS
                try:
                    import subprocess
                    result = subprocess.run(
                        ["sysctl", "-n", "hw.memsize"],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    mem_bytes = int(result.stdout.strip())
                    mem_info["total"] = f"{mem_bytes // 1024} kB"
                except:
                    pass
            else:  # Linux
                try:
                    with open("/proc/meminfo", "r") as f:
                        for line in f:
                            if line.startswith("MemTotal:"):
                                mem_info["total"] = line.split()[1] + " kB"
                            elif line.startswith("MemAvailable:"):
                                mem_info["available"] = line.split()[1] + " kB"
                except:
                    pass
            
            # 磁盘信息
            disk_info = {}
            try:
                stat = os.statvfs("/") if platform.system() != "Windows" else os.statvfs("C:/")
                disk_info["total"] = stat.f_frsize * stat.f_blocks
                disk_info["available"] = stat.f_frsize * stat.f_bavail
            except:
                pass
            
            # 负载
            load_avg = os.getloadavg() if hasattr(os, "getloadavg") else [0, 0, 0]
            
            return {
                "success": True,
                "data": {
                    "hostname": uname.node,
                    "system": uname.system,
                    "release": uname.release,
                    "version": uname.version,
                    "machine": uname.machine,
                    "processor": platform.processor(),
                    "python_version": platform.python_version(),
                    "memory": mem_info,
                    "disk": disk_info,
                    "load_avg": list(load_avg),
                    "uptime": Executor._get_uptime()
                }
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def _get_uptime() -> str:
        """获取系统运行时间"""
        try:
            if platform.system() == "Windows":
                import ctypes
                ticks = ctypes.windll.kernel32.GetTickCount()
                seconds = ticks / 1000
            else:
                with open("/proc/uptime", "r") as f:
                    seconds = float(f.readline().split()[0])
            
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}h {minutes}m"
        except:
            return "unknown"
    
    @staticmethod
    def shell_exec(params: dict) -> Dict[str, Any]:
        """执行 shell 命令"""
        cmd = params.get("cmd", "")
        timeout = params.get("timeout", 60)
        working_dir = params.get("cwd")
        
        if not cmd:
            return {"success": False, "error": "Empty command"}
        
        try:
            print(f"执行命令：{cmd}")
            
            shell = True if platform.system() != "Windows" else False
            result = subprocess.run(
                cmd,
                shell=shell,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=working_dir,
                env={**os.environ, "PYTHONIOENCODING": "utf-8"}
            )
            
            return {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": f"Command timed out after {timeout}s"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def file_list(params: dict) -> Dict[str, Any]:
        """列目录"""
        path = params.get("path", "/")
        
        try:
            entries = []
            for entry in os.listdir(path):
                full_path = os.path.join(path, entry)
                try:
                    stat = os.stat(full_path)
                    entries.append({
                        "name": entry,
                        "path": full_path,
                        "type": "directory" if os.path.isdir(full_path) else "file",
                        "size": stat.st_size,
                        "mode": oct(stat.st_mode)[-3:] if platform.system() != "Windows" else "N/A",
                        "mtime": stat.st_mtime,
                    })
                except:
                    entries.append({"name": entry, "path": full_path, "error": "access denied"})
            
            return {"success": True, "data": {"path": path, "entries": entries}}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def file_read(params: dict) -> Dict[str, Any]:
        """读文件"""
        path = params.get("path", "")
        offset = params.get("offset", 0)
        limit = params.get("limit", 100000)
        
        if not path:
            return {"success": False, "error": "Path required"}
        
        try:
            with open(path, "rb") as f:
                f.seek(offset)
                content = f.read(limit)
            
            try:
                text_content = content.decode("utf-8")
                return {
                    "success": True,
                    "data": {
                        "path": path,
                        "content": text_content,
                        "encoding": "utf-8",
                        "size": os.path.getsize(path)
                    }
                }
            except:
                import base64
                return {
                    "success": True,
                    "data": {
                        "path": path,
                        "content": base64.b64encode(content).decode(),
                        "encoding": "base64",
                        "size": os.path.getsize(path)
                    }
                }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def file_write(params: dict) -> Dict[str, Any]:
        """写文件"""
        path = params.get("path", "")
        content = params.get("content", "")
        encoding = params.get("encoding", "utf-8")
        append = params.get("append", False)
        
        if not path:
            return {"success": False, "error": "Path required"}
        
        try:
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            mode = "ab" if append else "wb"
            with open(path, mode) as f:
                if encoding == "base64":
                    import base64
                    f.write(base64.b64decode(content))
                else:
                    f.write(content.encode(encoding))
            
            return {"success": True, "data": {"path": path, "written": True}}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def file_delete(params: dict) -> Dict[str, Any]:
        """删除文件或目录"""
        path = params.get("path", "")
        recursive = params.get("recursive", False)
        
        if not path:
            return {"success": False, "error": "Path required"}
        
        try:
            import shutil
            if os.path.isdir(path):
                if recursive:
                    shutil.rmtree(path)
                else:
                    os.rmdir(path)
            else:
                os.remove(path)
            
            return {"success": True, "data": {"deleted": path}}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def process_list(params: dict) -> Dict[str, Any]:
        """进程列表"""
        try:
            if platform.system() == "Windows":
                result = subprocess.run(
                    ["tasklist"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
            else:
                result = subprocess.run(
                    ["ps", "aux"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
            
            lines = result.stdout.strip().split("\n")
            processes = []
            
            for i, line in enumerate(lines[1:], 1):
                processes.append({
                    "index": i,
                    "line": line
                })
            
            return {"success": True, "data": {"processes": processes}}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def process_kill(params: dict) -> Dict[str, Any]:
        """杀死进程"""
        pid = params.get("pid")
        signal_num = params.get("signal", 15)
        
        if pid is None:
            return {"success": False, "error": "PID required"}
        
        try:
            os.kill(pid, signal_num)
            return {"success": True, "data": {"killed": pid, "signal": signal_num}}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def service_operate(params: dict) -> Dict[str, Any]:
        """系统服务操作"""
        service = params.get("service", "")
        operation = params.get("operation", "status")
        
        if not service:
            return {"success": False, "error": "Service name required"}
        
        try:
            if platform.system() == "Windows":
                cmd = ["sc", operation, service]
            else:
                cmd = ["systemctl", operation, service]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            return {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "service": service,
                "operation": operation
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


class AgentClient:
    """AgentLinker 客户端"""
    
    def __init__(self, config: Config):
        self.config = config
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.running = True
        self.reconnect_interval = config.data.get("reconnect_interval", 5)
        self.heartbeat_interval = config.data.get("heartbeat_interval", 30)
        self.pairing_key: Optional[str] = None
    
    async def connect(self):
        """建立 WebSocket 连接"""
        print(f"连接到服务端：{self.config.server_url}")
        
        try:
            self.ws = await websockets.connect(
                self.config.server_url,
                ping_interval=None,
                close_timeout=10
            )
            
            # 发送注册消息
            await self.ws.send(json.dumps({
                "type": "register",
                "device_id": self.config.device_id,
                "device_name": self.config.device_name or self.config.device_id,
                "token": self.config.token,
                "platform": platform.system(),
                "platform_version": platform.version(),
            }))
            
            # 等待注册响应
            response = await asyncio.wait_for(self.ws.recv(), timeout=10)
            resp_data = json.loads(response)
            
            if resp_data.get("type") == "registered":
                print(f"注册成功：{resp_data.get('device_id')}")
                return True
            else:
                print(f"注册失败：{resp_data}")
                return False
        
        except Exception as e:
            print(f"连接失败：{e}")
            return False
    
    async def handle_messages(self):
        """处理服务端消息"""
        while self.running:
            try:
                msg = await asyncio.wait_for(self.ws.recv(), timeout=self.heartbeat_interval)
                data = json.loads(msg)
                
                msg_type = data.get("type")
                
                if msg_type == "ping":
                    await self.ws.send(json.dumps({"type": "pong", "time": time.time()}))
                
                elif msg_type == "pairing_key":
                    self.pairing_key = data.get("pairing_key")
                    device_id = data.get("device_id")
                    print("=" * 50)
                    print("🔐 配对密钥已生成！")
                    print(f"   设备 ID: {device_id}")
                    print(f"   配对密钥：{self.pairing_key}")
                    print(f"   将此密钥提供给主控端进行配对")
                    print("=" * 50)
                
                elif msg_type == "exec":
                    req_id = data.get("req_id")
                    action = data.get("action")
                    params = data.get("params", {})
                    
                    print(f"收到指令：{action} (req_id: {req_id})")
                    
                    result = Executor.execute(action, params)
                    
                    await self.ws.send(json.dumps({
                        "type": "result",
                        "req_id": req_id,
                        "success": result.get("success", False),
                        "data": result
                    }))
                
                elif msg_type == "error":
                    print(f"服务端错误：{data.get('msg')}")
                
                elif msg_type == "controller_connected":
                    controller_id = data.get("controller_id")
                    print(f"🎮 控制器 {controller_id} 已连接")
                    self.config.add_paired_controller(controller_id)
                
                elif msg_type == "controller_disconnected":
                    controller_id = data.get("controller_id")
                    print(f"🎮 控制器 {controller_id} 已断开")
            
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
    
    async def run(self):
        """主循环"""
        while self.running:
            if await self.connect():
                try:
                    await self.handle_messages()
                except Exception as e:
                    print(f"连接异常：{e}")
            
            if self.running:
                print(f"{self.reconnect_interval}秒后重连...")
                await asyncio.sleep(self.reconnect_interval)
    
    def stop(self):
        """停止客户端"""
        self.running = False
        if self.ws:
            asyncio.create_task(self.ws.close())


def generate_device_id() -> str:
    """生成设备 ID"""
    hostname = platform.node()
    unique_id = uuid.uuid4().hex[:8]
    return f"{hostname}-{unique_id}"
