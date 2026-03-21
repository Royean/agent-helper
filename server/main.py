"""
AgentLinker Server
云端中转服务端 - FastAPI + WebSocket
支持一对多控制
"""

import asyncio
import json
import time
import uuid
from typing import Dict, Optional, Set
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from starlette.middleware.cors import CORSMiddleware
import uvicorn

# ============== 配置 ==============
SERVER_AGENT_TOKEN = "ah_server_token_change_in_production"
LINUX_DEVICE_TOKEN = "ah_device_token_change_in_production"

# ============== 数据模型 ==============

class AgentRequest(BaseModel):
    device_id: str = Field(..., description="目标设备 ID")
    req_id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), description="请求 ID")
    action: str = Field(..., description="执行动作")
    params: dict = Field(default_factory=dict, description="动作参数")


class AgentResponse(BaseModel):
    code: int = 0
    msg: str = "ok"
    req_id: str
    data: Optional[dict] = None


class DeviceInfo(BaseModel):
    model_config = {"arbitrary_types_allowed": True}
    
    device_id: str
    device_name: str
    platform: str
    connected_at: float
    last_ping: float
    websocket: Optional[WebSocket] = None
    pending_requests: Dict[str, asyncio.Future] = {}
    paired_controllers: Set[str] = set()  # 已配对的控制器


class ControllerInfo(BaseModel):
    model_config = {"arbitrary_types_allowed": True}
    
    controller_id: str
    platform: str
    connected_at: float
    last_ping: float
    websocket: Optional[WebSocket] = None
    paired_devices: Set[str] = set()  # 已配对的设备


# ============== 全局状态 ==============

connected_devices: Dict[str, DeviceInfo] = {}
connected_controllers: Dict[str, ControllerInfo] = {}
security = HTTPBearer()

# 配对密钥存储 (临时，生产环境应该用 Redis)
pairing_keys: Dict[str, dict] = {}  # device_id -> {key, expires_at}


# ============== 工具函数 ==============

def verify_agent_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """验证 Agent 调用 Token"""
    if credentials.credentials != SERVER_AGENT_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid token")
    return credentials.credentials


def verify_device_token(token: str) -> bool:
    """验证 Linux 客户端 Token"""
    return token == LINUX_DEVICE_TOKEN


def generate_pairing_key() -> str:
    """生成配对密钥（8 位字母数字）"""
    import secrets
    import string
    return ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))


def cleanup_expired_pairing_keys():
    """清理过期的配对密钥"""
    now = time.time()
    expired = [k for k, v in pairing_keys.items() if v.get('expires_at', 0) < now]
    for k in expired:
        del pairing_keys[k]


# ============== FastAPI 应用 ==============

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    print("🚀 AgentLinker Server 启动")
    print(f"   服务端 Token: {SERVER_AGENT_TOKEN[:8]}...")
    yield
    # 清理所有连接
    for device in connected_devices.values():
        if device.websocket:
            await device.websocket.close()
    for controller in connected_controllers.values():
        if controller.websocket:
            await controller.websocket.close()
    print("🛑 AgentLinker Server 关闭")


app = FastAPI(
    title="AgentLinker Server",
    description="AI Agent 远程控制系统服务端",
    version="2.0.0",
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


# ============== WebSocket 路由 (设备端连接) ==============

@app.websocket("/ws/client")
async def client_websocket(websocket: WebSocket):
    """设备端 WebSocket 连接入口"""
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
        device_name = msg.get("device_name", device_id)
        platform = msg.get("platform", "Unknown")
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
            device_name=device_name,
            platform=platform,
            connected_at=now,
            last_ping=now,
            websocket=websocket,
            pending_requests={},
            paired_controllers=set()
        )
        
        # 如果设备已存在，关闭旧连接
        if device_id in connected_devices:
            old_device = connected_devices[device_id]
            if old_device.websocket:
                try:
                    await old_device.websocket.close()
                except:
                    pass
            # 取消旧请求
            for future in old_device.pending_requests.values():
                if not future.done():
                    future.set_exception(Exception("Device reconnected"))
        
        connected_devices[device_id] = device_info
        
        # 检查是否为自动接受模式
        auto_accept = msg.get("auto_accept", False)
        
        await websocket.send_json({
            "type": "registered",
            "device_id": device_id,
            "device_name": device_name,
            "auto_accept": auto_accept,
            "msg": "Connected successfully"
        })
        
        print(f"📱 设备上线：{device_id} ({platform}), auto_accept={auto_accept}")
        
        if auto_accept:
            # 自动配对模式 - 生成特殊配对密钥并立即配对
            pairing_key = "AUTO_" + generate_pairing_key()
            pairing_keys[device_id] = {
                "key": pairing_key,
                "expires_at": now + 86400,  # 24小时过期
                "created_at": now,
                "auto": True
            }
            # 通知设备已自动配对
            await websocket.send_json({
                "type": "auto_paired",
                "device_id": device_id,
                "msg": "Device auto-paired, waiting for controller..."
            })
            print(f"🔓 设备 {device_id} 已自动配对")
        else:
            # 生成并发送配对密钥（传统模式）
            pairing_key = generate_pairing_key()
            pairing_keys[device_id] = {
                "key": pairing_key,
                "expires_at": now + 3600,  # 1 小时过期
                "created_at": now
            }
            
            await websocket.send_json({
                "type": "pairing_key",
                "device_id": device_id,
                "pairing_key": pairing_key,
                "msg": f"Your pairing key: {pairing_key}"
            })
            print(f"🔑 设备 {device_id} 配对密钥：{pairing_key}")
        
        # 通知已配对的控制器
        for ctrl_id in device_info.paired_controllers:
            if ctrl_id in connected_controllers:
                ctrl = connected_controllers[ctrl_id]
                if ctrl.websocket:
                    try:
                        await ctrl.websocket.send_json({
                            "type": "device_online",
                            "device_id": device_id
                        })
                    except:
                        pass
        
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
                if time.time() - device_info.last_ping > 120:
                    print(f"⏱️ 设备心跳超时：{device_id}")
                    break
                try:
                    await websocket.send_json({"type": "ping"})
                except:
                    break
    
    except WebSocketDisconnect:
        print(f"📴 设备断开：{device_id}")
    except Exception as e:
        print(f"❌ 设备 {device_id} 异常：{e}")
    finally:
        if device_id and device_id in connected_devices:
            device = connected_devices[device_id]
            # 清理 pending requests
            for future in device.pending_requests.values():
                if not future.done():
                    future.set_exception(Exception("Device disconnected"))
            
            # 通知控制器设备离线
            for ctrl_id in device.paired_controllers:
                if ctrl_id in connected_controllers:
                    ctrl = connected_controllers[ctrl_id]
                    if ctrl.websocket:
                        try:
                            await ctrl.websocket.send_json({
                                "type": "device_offline",
                                "device_id": device_id
                            })
                        except:
                            pass
            
            del connected_devices[device_id]
            # 清理配对密钥
            if device_id in pairing_keys:
                del pairing_keys[device_id]
            print(f"🗑️ 设备注销：{device_id}")


# ============== WebSocket 路由 (控制器端连接) ==============

@app.websocket("/ws/controller")
async def controller_websocket(websocket: WebSocket):
    """控制器 WebSocket 连接入口"""
    await websocket.accept()
    controller_id: Optional[str] = None
    
    try:
        # 第一步：接收握手消息
        raw_msg = await websocket.receive_text()
        msg = json.loads(raw_msg)
        
        if msg.get("type") != "controller_handshake":
            await websocket.send_json({"type": "error", "msg": "First message must be controller_handshake"})
            await websocket.close()
            return
        
        controller_id = msg.get("controller_id")
        platform = msg.get("platform", "Unknown")
        
        if not controller_id:
            await websocket.send_json({"type": "error", "msg": "Missing controller_id"})
            await websocket.close()
            return
        
        # 注册控制器
        now = time.time()
        controller_info = ControllerInfo(
            controller_id=controller_id,
            platform=platform,
            connected_at=now,
            last_ping=now,
            websocket=websocket,
            paired_devices=set()
        )
        
        # 如果控制器已存在，关闭旧连接
        if controller_id in connected_controllers:
            old_controller = connected_controllers[controller_id]
            if old_controller.websocket:
                try:
                    await old_controller.websocket.close()
                except:
                    pass
        
        connected_controllers[controller_id] = controller_info
        
        await websocket.send_json({
            "type": "controller_ready",
            "controller_id": controller_id,
            "msg": "Controller ready"
        })
        
        print(f"🎮 控制器上线：{controller_id} ({platform})")
        
        # 保持连接，处理指令
        while True:
            try:
                raw_msg = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=60.0
                )
                msg = json.loads(raw_msg)
                
                msg_type = msg.get("type")
                
                if msg_type == "ping":
                    controller_info.last_ping = time.time()
                    await websocket.send_json({"type": "pong", "time": time.time()})
                
                elif msg_type == "pair":
                    # 配对设备
                    device_id = msg.get("device_id")
                    pairing_key = msg.get("pairing_key")
                    
                    # 验证配对密钥
                    cleanup_expired_pairing_keys()
                    
                    if device_id not in pairing_keys:
                        await websocket.send_json({
                            "type": "error",
                            "msg": f"Device {device_id} not found or pairing key expired"
                        })
                        continue
                    
                    if pairing_keys[device_id]["key"] != pairing_key:
                        # 对于 auto_accept 设备，也接受 AUTO_PAIR 通配符
                        is_auto = pairing_keys[device_id].get("auto", False)
                        if not (is_auto and pairing_key == "AUTO_PAIR"):
                            await websocket.send_json({
                                "type": "error",
                                "msg": "Invalid pairing key"
                            })
                            continue
                    
                    # 检查设备是否在线
                    if device_id not in connected_devices:
                        await websocket.send_json({
                            "type": "error",
                            "msg": f"Device {device_id} is offline"
                        })
                        continue
                    
                    # 配对成功
                    device = connected_devices[device_id]
                    device.paired_controllers.add(controller_id)
                    controller_info.paired_devices.add(device_id)
                    
                    await websocket.send_json({
                        "type": "paired",
                        "controller_id": controller_id,
                        "device_id": device_id,
                        "msg": f"Successfully paired with {device_id}"
                    })
                    
                    # 通知设备
                    if device.websocket:
                        await device.websocket.send_json({
                            "type": "controller_connected",
                            "controller_id": controller_id
                        })
                    
                    print(f"🔗 控制器 {controller_id} 配对设备 {device_id}")
                
                elif msg_type == "unpair":
                    # 解除配对
                    device_id = msg.get("device_id")
                    
                    if device_id in connected_devices:
                        device = connected_devices[device_id]
                        device.paired_controllers.discard(controller_id)
                        if device.websocket:
                            await device.websocket.send_json({
                                "type": "controller_disconnected",
                                "controller_id": controller_id
                            })
                    
                    controller_info.paired_devices.discard(device_id)
                    print(f"🔓 控制器 {controller_id} 解除配对 {device_id}")
                
                elif msg_type == "exec":
                    # 转发指令到设备
                    req_id = msg.get("req_id", str(uuid.uuid4()))
                    device_id = msg.get("device_id")
                    action = msg.get("action")
                    params = msg.get("params", {})
                    
                    # 检查是否已配对
                    if device_id not in controller_info.paired_devices:
                        await websocket.send_json({
                            "type": "error",
                            "req_id": req_id,
                            "msg": f"Device {device_id} not paired"
                        })
                        continue
                    
                    # 检查设备是否在线
                    if device_id not in connected_devices:
                        await websocket.send_json({
                            "type": "error",
                            "req_id": req_id,
                            "msg": f"Device {device_id} is offline"
                        })
                        continue
                    
                    target_device = connected_devices[device_id]
                    
                    # 创建 Future 等待结果
                    future = asyncio.get_event_loop().create_future()
                    target_device.pending_requests[req_id] = future
                    
                    # 发送指令到设备
                    await target_device.websocket.send_json({
                        "type": "exec",
                        "req_id": req_id,
                        "action": action,
                        "params": params
                    })
                    
                    # 等待结果（超时 30 秒）
                    try:
                        result = await asyncio.wait_for(future, timeout=30.0)
                        await websocket.send_json({
                            "type": "result",
                            "req_id": req_id,
                            "data": result.get("data") or result
                        })
                    except asyncio.TimeoutError:
                        await websocket.send_json({
                            "type": "error",
                            "req_id": req_id,
                            "msg": "Request timeout"
                        })
                    finally:
                        if req_id in target_device.pending_requests:
                            del target_device.pending_requests[req_id]
                
                elif msg_type == "list_devices":
                    # 返回在线设备列表
                    req_id = msg.get("req_id")
                    devices = []
                    for dev_id, dev in connected_devices.items():
                        devices.append({
                            "device_id": dev_id,
                            "device_name": dev.device_name,
                            "platform": dev.platform,
                            "online_duration": time.time() - dev.connected_at
                        })
                    
                    await websocket.send_json({
                        "type": "result",
                        "req_id": req_id,
                        "devices": devices
                    })
                
            except asyncio.TimeoutError:
                try:
                    await websocket.send_json({"type": "ping"})
                except:
                    break
    
    except WebSocketDisconnect:
        print(f"🎮 控制器断开：{controller_id}")
    except Exception as e:
        print(f"❌ 控制器 {controller_id} 异常：{e}")
    finally:
        if controller_id and controller_id in connected_controllers:
            # 清理配对关系
            controller = connected_controllers[controller_id]
            for device_id in controller.paired_devices:
                if device_id in connected_devices:
                    device = connected_devices[device_id]
                    device.paired_controllers.discard(controller_id)
            
            del connected_controllers[controller_id]
            print(f"🗑️ 控制器注销：{controller_id}")


# ============== HTTP API 路由 ==============

@app.post("/api/v1/agent/send", response_model=AgentResponse)
async def agent_send(
    request: AgentRequest,
    token: str = Depends(verify_agent_token)
):
    """Agent 发送指令到设备"""
    device_id = request.device_id
    
    if device_id not in connected_devices:
        raise HTTPException(status_code=404, detail=f"Device {device_id} not connected")
    
    device = connected_devices[device_id]
    future = asyncio.get_event_loop().create_future()
    device.pending_requests[request.req_id] = future
    
    try:
        await device.websocket.send_json({
            "type": "exec",
            "req_id": request.req_id,
            "action": request.action,
            "params": request.params
        })
        
        result = await asyncio.wait_for(future, timeout=60.0)
        
        return AgentResponse(
            code=0,
            msg="ok",
            req_id=request.req_id,
            data=result.get("data") or {"success": result.get("success", False)}
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
            "device_name": info.device_name,
            "platform": info.platform,
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
        "connected_controllers": len(connected_controllers),
        "version": "2.0.0"
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
