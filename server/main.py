"""
Agent Helper Server
云端中转服务端 - FastAPI + WebSocket
"""

import asyncio
import json
import time
import uuid
from typing import Dict, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from starlette.middleware.cors import CORSMiddleware
import uvicorn

# ============== 配置 ==============
# MVP 版本使用内存存储，生产环境可替换为 Redis
SERVER_AGENT_TOKEN = "ah_server_token_change_in_production"  # Agent 调用 Token
LINUX_DEVICE_TOKEN = "ah_device_token_change_in_production"  # Linux 客户端 Token

# ============== 数据模型 ==============

class AgentRequest(BaseModel):
    device_id: str = Field(..., description="目标设备ID")
    req_id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), description="请求ID")
    action: str = Field(..., description="执行动作")
    params: dict = Field(default_factory=dict, description="动作参数")


class AgentResponse(BaseModel):
    code: int = 0
    msg: str = "ok"
    req_id: str
    data: Optional[dict] = None


class DeviceInfo(BaseModel):
    device_id: str
    connected_at: float
    last_ping: float
    websocket: Optional[WebSocket] = None
    pending_requests: Dict[str, asyncio.Future] = {}


# ============== 全局状态 ==============

connected_devices: Dict[str, DeviceInfo] = {}
security = HTTPBearer()


# ============== 依赖注入 ==============

def verify_agent_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """验证 Agent 调用 Token"""
    if credentials.credentials != SERVER_AGENT_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid token")
    return credentials.credentials


def verify_device_token(token: str) -> bool:
    """验证 Linux 客户端 Token"""
    return token == LINUX_DEVICE_TOKEN


# ============== FastAPI 应用 ==============

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    print("🚀 Agent Helper Server 启动")
    yield
    # 清理所有连接
    for device in connected_devices.values():
        if device.websocket:
            await device.websocket.close()
    print("🛑 Agent Helper Server 关闭")


app = FastAPI(
    title="Agent Helper Server",
    description="AI Agent Linux 远程控制服务端",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============== WebSocket 路由 (Linux 客户端连接) ==============

@app.websocket("/ws/linux")
async def linux_websocket(websocket: WebSocket):
    """Linux 客户端 WebSocket 连接入口"""
    await websocket.accept()
    device_id: Optional[str] = None

    try:
        # 第一步：接收注册消息
        raw_msg = await websocket.receive_text()
        msg = json.loads(raw_msg)

        if msg.get("type") != "register":
            await websocket.send_json({"type": "error", "msg": "First message must be register"})
            await websocket.close()
            return

        device_id = msg.get("device_id")
        token = msg.get("token")

        if not device_id or not token:
            await websocket.send_json({"type": "error", "msg": "Missing device_id or token"})
            await websocket.close()
            return

        if not verify_device_token(token):
            await websocket.send_json({"type": "error", "msg": "Invalid token"})
            await websocket.close()
            return

        # 注册成功
        now = time.time()
        device_info = DeviceInfo(
            device_id=device_id,
            connected_at=now,
            last_ping=now,
            websocket=websocket,
            pending_requests={}
        )

        # 如果设备已存在，关闭旧连接
        if device_id in connected_devices:
            old_device = connected_devices[device_id]
            if old_device.websocket:
                try:
                    await old_device.websocket.close()
                except:
                    pass
            # 取消旧请求的 Future
            for future in old_device.pending_requests.values():
                if not future.done():
                    future.set_exception(Exception("Device reconnected"))

        connected_devices[device_id] = device_info

        await websocket.send_json({
            "type": "registered",
            "device_id": device_id,
            "msg": "Connected successfully"
        })

        print(f"📱 设备上线: {device_id}")

        # 保持连接，处理心跳和结果返回
        while True:
            try:
                raw_msg = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=60.0
                )
                msg = json.loads(raw_msg)

                msg_type = msg.get("type")

                if msg_type == "ping":
                    device_info.last_ping = time.time()
                    await websocket.send_json({"type": "pong", "time": time.time()})

                elif msg_type == "result":
                    # 客户端返回执行结果
                    req_id = msg.get("req_id")
                    if req_id and req_id in device_info.pending_requests:
                        future = device_info.pending_requests.pop(req_id)
                        if not future.done():
                            future.set_result(msg)

                elif msg_type == "error":
                    req_id = msg.get("req_id")
                    if req_id and req_id in device_info.pending_requests:
                        future = device_info.pending_requests.pop(req_id)
                        if not future.done():
                            future.set_result(msg)

            except asyncio.TimeoutError:
                # 检查心跳超时
                if time.time() - device_info.last_ping > 120:
                    print(f"⏱️ 设备心跳超时: {device_id}")
                    break
                # 发送 ping
                try:
                    await websocket.send_json({"type": "ping"})
                except:
                    break

    except WebSocketDisconnect:
        print(f"📴 设备断开: {device_id}")
    except Exception as e:
        print(f"❌ 设备 {device_id} 异常: {e}")
    finally:
        if device_id and device_id in connected_devices:
            # 清理 pending requests
            device = connected_devices[device_id]
            for future in device.pending_requests.values():
                if not future.done():
                    future.set_exception(Exception("Device disconnected"))
            del connected_devices[device_id]
            print(f"🗑️ 设备注销: {device_id}")


# ============== HTTP API 路由 (Agent 调用) ==============

@app.post("/api/v1/agent/send", response_model=AgentResponse)
async def agent_send(
    request: AgentRequest,
    token: str = Depends(verify_agent_token)
):
    """
    Agent 发送指令到 Linux 客户端

    支持的 actions:
    - system.info: 获取系统信息
    - shell.exec: 执行 shell 命令
    - file.list: 列目录
    - file.read: 读文件
    - file.write: 写文件
    - process.list: 进程列表
    - process.kill: 杀死进程
    - service.operate: 系统服务操作
    """
    device_id = request.device_id

    # 检查设备是否在线
    if device_id not in connected_devices:
        raise HTTPException(status_code=404, detail=f"Device {device_id} not connected")

    device = connected_devices[device_id]

    # 创建异步 Future 等待结果
    future = asyncio.get_event_loop().create_future()
    device.pending_requests[request.req_id] = future

    try:
        # 发送指令到客户端
        await device.websocket.send_json({
            "type": "exec",
            "req_id": request.req_id,
            "action": request.action,
            "params": request.params
        })

        # 等待结果（超时 60 秒）
        result = await asyncio.wait_for(future, timeout=60.0)

        return AgentResponse(
            code=0,
            msg="ok",
            req_id=request.req_id,
            data=result.get("data") or {"success": result.get("success", False), "error": result.get("error")}
        )

    except asyncio.TimeoutError:
        return AgentResponse(
            code=408,
            msg="Request timeout",
            req_id=request.req_id,
            data={"success": False, "error": "Request timeout"}
        )
    except Exception as e:
        return AgentResponse(
            code=500,
            msg=str(e),
            req_id=request.req_id,
            data={"success": False, "error": str(e)}
        )
    finally:
        # 清理
        if request.req_id in device.pending_requests:
            del device.pending_requests[request.req_id]


@app.get("/api/v1/devices")
async def list_devices(token: str = Depends(verify_agent_token)):
    """获取在线设备列表"""
    now = time.time()
    devices = []
    for device_id, info in connected_devices.items():
        devices.append({
            "device_id": device_id,
            "connected_at": info.connected_at,
            "last_ping": info.last_ping,
            "online_duration": now - info.connected_at
        })
    return {"code": 0, "devices": devices}


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "ok",
        "connected_devices": len(connected_devices),
        "version": "1.0.0"
    }


# ============== 主入口 ==============

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8080,
        reload=False,
        log_level="info"
    )
