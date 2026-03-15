"""
Agent Helper Linux Client
Linux 高权限接入客户端
"""

import asyncio
import json
import os
import platform
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional

import websockets
from websockets.exceptions import ConnectionClosed

# ============== 配置 ==============

CONFIG_PATH = "/etc/agent_helper/config.json"
LOG_DIR = "/var/log/agent_helper"
LOG_FILE = f"{LOG_DIR}/agent_helper.log"

DEFAULT_CONFIG = {
    "device_id": "",
    "token": "",
    "server_url": "wss://your-server.com/ws/linux",
    "reconnect_interval": 5,
    "heartbeat_interval": 30
}

# ============== 日志工具 ==============

class Logger:
    def __init__(self, log_file: str):
        self.log_file = log_file
        self._ensure_dir()

    def _ensure_dir(self):
        Path(self.log_file).parent.mkdir(parents=True, exist_ok=True)

    def _write(self, level: str, msg: str):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{timestamp}] [{level}] {msg}\n"
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(line)
        except:
            pass
        print(line.strip())

    def info(self, msg: str):
        self._write("INFO", msg)

    def error(self, msg: str):
        self._write("ERROR", msg)

    def warning(self, msg: str):
        self._write("WARN", msg)

    def debug(self, msg: str):
        self._write("DEBUG", msg)


logger = Logger(LOG_FILE)

# ============== 配置管理 ==============

class Config:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.data = self._load()

    def _load(self) -> dict:
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    return {**DEFAULT_CONFIG, **json.load(f)}
            except Exception as e:
                logger.error(f"加载配置失败: {e}")
        return DEFAULT_CONFIG.copy()

    def save(self):
        try:
            Path(self.config_path).parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"保存配置失败: {e}")

    @property
    def device_id(self) -> str:
        return self.data.get("device_id", "")

    @property
    def token(self) -> str:
        return self.data.get("token", "")

    @property
    def server_url(self) -> str:
        return self.data.get("server_url", "")


# ============== 指令执行器 ==============

class Executor:
    """指令执行器 - 以 root 权限执行各种系统操作"""

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
            logger.error(f"执行 {action} 失败: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def system_info(params: dict) -> Dict[str, Any]:
        """获取系统信息"""
        try:
            uname = platform.uname()

            # 内存信息
            mem_info = {}
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
                stat = os.statvfs("/")
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
            logger.info(f"执行命令: {cmd}")

            result = subprocess.run(
                cmd,
                shell=True,
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
                        "mode": oct(stat.st_mode)[-3:],
                        "mtime": stat.st_mtime,
                        "uid": stat.st_uid,
                        "gid": stat.st_gid
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
        limit = params.get("limit", 100000)  # 默认最多 100KB

        if not path:
            return {"success": False, "error": "Path required"}

        try:
            with open(path, "rb") as f:
                f.seek(offset)
                content = f.read(limit)

            # 尝试解码为文本
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
                # 二进制文件
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
        create_dirs = params.get("create_dirs", True)

        if not path:
            return {"success": False, "error": "Path required"}

        try:
            if create_dirs:
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
            result = subprocess.run(
                ["ps", "aux"],
                capture_output=True,
                text=True,
                timeout=10
            )

            lines = result.stdout.strip().split("\n")
            processes = []

            # 跳过标题行
            for line in lines[1:]:
                parts = line.split(None, 10)
                if len(parts) >= 11:
                    processes.append({
                        "user": parts[0],
                        "pid": int(parts[1]),
                        "cpu": float(parts[2]),
                        "mem": float(parts[3]),
                        "vsz": parts[4],
                        "rss": parts[5],
                        "tty": parts[6],
                        "stat": parts[7],
                        "start": parts[8],
                        "time": parts[9],
                        "command": parts[10]
                    })

            return {"success": True, "data": {"processes": processes}}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def process_kill(params: dict) -> Dict[str, Any]:
        """杀死进程"""
        pid = params.get("pid")
        signal_num = params.get("signal", 15)  # SIGTERM

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
        operation = params.get("operation", "status")  # start, stop, restart, status, enable, disable

        if not service:
            return {"success": False, "error": "Service name required"}

        valid_ops = ["start", "stop", "restart", "reload", "status", "enable", "disable", "is-active", "is-enabled"]
        if operation not in valid_ops:
            return {"success": False, "error": f"Invalid operation. Valid: {valid_ops}"}

        try:
            result = subprocess.run(
                ["systemctl", operation, service],
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


# ============== WebSocket 客户端 ==============

class AgentClient:
    def __init__(self, config: Config):
        self.config = config
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.running = True
        self.reconnect_interval = config.data.get("reconnect_interval", 5)
        self.heartbeat_interval = config.data.get("heartbeat_interval", 30)

    async def connect(self):
        """建立 WebSocket 连接"""
        logger.info(f"连接到服务端: {self.config.server_url}")

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
                "token": self.config.token
            }))

            # 等待注册响应
            response = await asyncio.wait_for(self.ws.recv(), timeout=10)
            resp_data = json.loads(response)

            if resp_data.get("type") == "registered":
                logger.info(f"注册成功: {resp_data.get('device_id')}")
                return True
            else:
                logger.error(f"注册失败: {resp_data}")
                return False

        except Exception as e:
            logger.error(f"连接失败: {e}")
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

                elif msg_type == "exec":
                    # 执行指令
                    req_id = data.get("req_id")
                    action = data.get("action")
                    params = data.get("params", {})

                    logger.info(f"收到指令: {action} (req_id: {req_id})")

                    # 执行
                    result = Executor.execute(action, params)

                    # 返回结果
                    await self.ws.send(json.dumps({
                        "type": "result",
                        "req_id": req_id,
                        "success": result.get("success", False),
                        "data": result
                    }))

                elif msg_type == "error":
                    logger.error(f"服务端错误: {data.get('msg')}")

            except asyncio.TimeoutError:
                # 发送心跳
                try:
                    await self.ws.send(json.dumps({"type": "ping", "time": time.time()}))
                except:
                    break

            except ConnectionClosed:
                logger.warning("连接已关闭")
                break

            except Exception as e:
                logger.error(f"消息处理错误: {e}")
                break

    async def run(self):
        """主循环"""
        while self.running:
            if await self.connect():
                try:
                    await self.handle_messages()
                except Exception as e:
                    logger.error(f"连接异常: {e}")

            if self.running:
                logger.info(f"{self.reconnect_interval}秒后重连...")
                await asyncio.sleep(self.reconnect_interval)

    def stop(self):
        """停止客户端"""
        self.running = False
        if self.ws:
            asyncio.create_task(self.ws.close())


# ============== 主入口 ==============

def signal_handler(client: AgentClient):
    """信号处理"""
    def handler(signum, frame):
        logger.info(f"收到信号 {signum}，正在退出...")
        client.stop()
    return handler


def check_root():
    """检查是否以 root 运行"""
    if os.geteuid() != 0:
        logger.error("请以 root 权限运行此程序")
        sys.exit(1)


def generate_device_id() -> str:
    """生成设备ID"""
    import uuid
    hostname = platform.node()
    unique_id = uuid.uuid4().hex[:8]
    return f"{hostname}-{unique_id}"


def main():
    """主函数"""
    # 检查 root 权限
    check_root()

    # 加载配置
    config = Config(CONFIG_PATH)

    # 如果配置为空，初始化
    if not config.device_id:
        config.data["device_id"] = generate_device_id()
        config.save()
        logger.info(f"已生成设备ID: {config.device_id}")
        logger.warning("请编辑配置文件设置 token 和 server_url:")
        logger.warning(f"  {CONFIG_PATH}")
        sys.exit(1)

    if not config.token or not config.server_url:
        logger.error("配置不完整，请编辑配置文件:")
        logger.error(f"  {CONFIG_PATH}")
        sys.exit(1)

    logger.info(f"启动 Agent Helper Client")
    logger.info(f"设备ID: {config.device_id}")
    logger.info(f"服务端: {config.server_url}")

    # 创建客户端
    client = AgentClient(config)

    # 信号处理
    signal.signal(signal.SIGTERM, lambda s, f: signal_handler(client)(s, f))
    signal.signal(signal.SIGINT, lambda s, f: signal_handler(client)(s, f))

    # 运行
    try:
        asyncio.run(client.run())
    except KeyboardInterrupt:
        logger.info("用户中断")
    except Exception as e:
        logger.error(f"运行时错误: {e}")

    logger.info("客户端已退出")


if __name__ == "__main__":
    main()
