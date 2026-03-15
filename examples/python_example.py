"""
Agent Helper Python 调用示例

可以直接复制使用
"""

import requests
import json

# ============ 配置 ============
SERVER_URL = "http://localhost:8080"
SERVER_TOKEN = "ah_server_token_change_in_production"
DEVICE_ID = "my-linux-server"

# ============ 封装类 ============

class AgentHelperClient:
    """Agent Helper 客户端封装"""

    def __init__(self, server_url: str, token: str, device_id: str):
        self.server_url = server_url.rstrip("/")
        self.token = token
        self.device_id = device_id
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

    def send(self, action: str, params: dict = None, req_id: str = None) -> dict:
        """发送指令"""
        import uuid

        data = {
            "device_id": self.device_id,
            "req_id": req_id or str(uuid.uuid4()),
            "action": action,
            "params": params or {}
        }

        resp = requests.post(
            f"{self.server_url}/api/v1/agent/send",
            json=data,
            headers=self.headers,
            timeout=65  # 比指令超时稍长
        )
        resp.raise_for_status()
        return resp.json()

    def shell(self, cmd: str, timeout: int = 30, cwd: str = None) -> dict:
        """执行 shell 命令"""
        params = {"cmd": cmd, "timeout": timeout}
        if cwd:
            params["cwd"] = cwd
        return self.send("shell.exec", params)

    def system_info(self) -> dict:
        """获取系统信息"""
        return self.send("system.info")

    def file_list(self, path: str = "/") -> dict:
        """列目录"""
        return self.send("file.list", {"path": path})

    def file_read(self, path: str, offset: int = 0, limit: int = 100000) -> dict:
        """读文件"""
        return self.send("file.read", {"path": path, "offset": offset, "limit": limit})

    def file_write(self, path: str, content: str, append: bool = False) -> dict:
        """写文件"""
        return self.send("file.write", {"path": path, "content": content, "append": append})

    def process_list(self) -> dict:
        """进程列表"""
        return self.send("process.list")

    def process_kill(self, pid: int, signal: int = 15) -> dict:
        """杀死进程"""
        return self.send("process.kill", {"pid": pid, "signal": signal})

    def service(self, name: str, operation: str = "status") -> dict:
        """服务操作"""
        return self.send("service.operate", {"service": name, "operation": operation})

    def list_devices(self) -> dict:
        """获取在线设备列表"""
        resp = requests.get(
            f"{self.server_url}/api/v1/devices",
            headers=self.headers
        )
        resp.raise_for_status()
        return resp.json()


# ============ 使用示例 ============

def demo():
    """演示各种用法"""

    # 创建客户端
    client = AgentHelperClient(SERVER_URL, SERVER_TOKEN, DEVICE_ID)

    print("=" * 50)
    print("Agent Helper 调用示例")
    print("=" * 50)

    # 1. 获取系统信息
    print("\n1. 获取系统信息:")
    result = client.system_info()
    if result.get("code") == 0:
        data = result["data"]["data"]
        print(f"   主机名: {data['hostname']}")
        print(f"   系统: {data['system']} {data['release']}")
        print(f"   架构: {data['machine']}")
        print(f"   运行时间: {data['uptime']}")
    else:
        print(f"   错误: {result.get('msg')}")

    # 2. 执行命令
    print("\n2. 执行命令 (whoami):")
    result = client.shell("whoami")
    if result.get("code") == 0:
        data = result["data"]
        print(f"   成功: {data['success']}")
        print(f"   输出: {data.get('stdout', '').strip()}")
    else:
        print(f"   错误: {result.get('msg')}")

    # 3. 查看磁盘
    print("\n3. 查看磁盘空间:")
    result = client.shell("df -h / | tail -1")
    if result.get("code") == 0:
        print(f"   {result['data'].get('stdout', '').strip()}")

    # 4. 列目录
    print("\n4. 列目录 (/root):")
    result = client.file_list("/root")
    if result.get("code") == 0:
        entries = result["data"]["data"]["entries"][:5]  # 只显示前5个
        for entry in entries:
            type_icon = "📁" if entry["type"] == "directory" else "📄"
            print(f"   {type_icon} {entry['name']}")

    # 5. 读文件
    print("\n5. 读文件 (/etc/os-release):")
    result = client.file_read("/etc/os-release")
    if result.get("code") == 0:
        content = result["data"]["data"]["content"]
        for line in content.split("\n")[:3]:
            if line.strip():
                print(f"   {line}")

    # 6. 进程列表
    print("\n6. 进程列表 (前3个):")
    result = client.process_list()
    if result.get("code") == 0:
        processes = result["data"]["data"]["processes"][:3]
        for proc in processes:
            print(f"   PID {proc['pid']}: {proc['command'][:50]}...")

    # 7. 服务状态
    print("\n7. 服务状态 (sshd):")
    result = client.service("sshd", "is-active")
    if result.get("code") == 0:
        print(f"   状态: {result['data'].get('stdout', 'unknown').strip()}")

    # 8. 在线设备
    print("\n8. 在线设备:")
    result = client.list_devices()
    if result.get("code") == 0:
        devices = result.get("devices", [])
        print(f"   共 {len(devices)} 个设备在线")
        for device in devices:
            print(f"   - {device['device_id']}")

    print("\n" + "=" * 50)
    print("示例完成")
    print("=" * 50)


if __name__ == "__main__":
    demo()
