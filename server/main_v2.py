"""
AgentLinker Server v2.1 - 安全增强版
新增功能:
- TLS/SSL 加密传输
- 操作审计日志
- 改进的心跳机制
- 连接池管理
"""

import asyncio
import json
import time
import uuid
import ssl
import hashlib
from typing import Dict, Optional, Set
from datetime import datetime
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from starlette.middleware.cors import CORSMiddleware
import uvicorn

# ============== 配置 ==============
SERVER_AGENT_TOKEN = "ah_server_token_change_in_production"
LINUX_DEVICE_TOKEN = "ah_device_token_change_in_production"

# TLS 配置
TLS_ENABLED = False  # 生产环境设为 True
TLS_CERT_FILE = "/opt/agentlinker/server/cert.pem"
TLS_KEY_FILE = "/opt/agentlinker/server/key.pem"

# 审计日志配置
AUDIT_LOG_ENABLED = True
AUDIT_LOG_FILE = "/var/log/agentlinker/audit.log"

# ============== 数据模型 ==============

class DeviceInfo(BaseModel):
    device_id: str
    device_name: str
    platform: str
    connected_at: float
    last_ping: float
    websocket: Optional[WebSocket] = None
    pending_requests: Dict[str, asyncio.Future] = {}
    paired_controllers: Set[str] = set()


class ControllerInfo(BaseModel):
    controller_id: str
    platform: str
    connected_at: float
    last_ping: float
    websocket: Optional[WebSocket] = None
    paired_devices: Set[str] = set()


class AuditLogEntry(BaseModel):
    timestamp: str
    action: str
    actor_type: str  # "device" or "controller"
    actor_id: str
    target_type: Optional[str] = None
    target_id: Optional[str] = None
    result: str  # "success" or "failure"
    details: Optional[dict] = None
    ip_address: Optional[str] = None


# ============== 全局状态 ==============

connected_devices: Dict[str, DeviceInfo] = {}
connected_controllers: Dict[str, ControllerInfo] = {}
security = HTTPBearer()

# 配对密钥存储
pairing_keys: Dict[str, dict] = {}

# 审计日志
audit_logs: list = []


# ============== 工具函数 ==============

def log_audit(action: str, actor_type: str, actor_id: str, 
              result: str, target_type: str = None, target_id: str = None,
              details: dict = None, ip_address: str = None):
    """记录审计日志"""
    if not AUDIT_LOG_ENABLED:
        return
    
    entry = AuditLogEntry(
        timestamp=datetime.utcnow().isoformat(),
        action=action,
        actor_type=actor_type,
        actor_id=actor_id,
        target_type=target_type,
        target_id=target_id,
        result=result,
        details=details,
        ip_address=ip_address
    )
    
    audit_logs.append(entry)
    
    # 异步写入文件
    asyncio.create_task(write_audit_log(entry))
    
    # 限制内存中的日志数量
    if len(audit_logs) > 10000:
        audit_logs.pop(0)


async def write_audit_log(entry: AuditLogEntry):
    """将审计日志写入文件"""
    try:
        log_path = Path(AUDIT_LOG_FILE)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(log_path, "a") as f:
            f.write(entry.model_dump_json() + "\n")
    except Exception as e:
        print(f"写入审计日志失败：{e}")


def generate_pairing_key() -> str:
    """生成配对密钥（8 位字母数字）"""
    import secrets
    import string
    return ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))


def hash_sensitive_data(data: str) -> str:
    """对敏感数据进行哈希"""
    return hashlib.sha256(data.encode()).hexdigest()[:16]


# ============== FastAPI 应用 ==============

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    print("🚀 AgentLinker Server 启动")
    print(f"   TLS: {'启用' if TLS_ENABLED else '禁用'}")
    print(f"   审计日志：{'启用' if AUDIT_LOG_ENABLED else '禁用'}")
    if AUDIT_LOG_ENABLED:
        print(f"   日志文件：{AUDIT_LOG_FILE}")
    yield
    print("🛑 AgentLinker Server 停止")


app = FastAPI(
    title="AgentLinker Server",
    description="AI Agent 远程控制系统 - 安全增强版",
    version="2.1.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============== API 端点 ==============

@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "ok",
        "version": "2.1.0",
        "connected_devices": len(connected_devices),
        "connected_controllers": len(connected_controllers),
        "tls_enabled": TLS_ENABLED
    }


@app.get("/api/v1/devices")
async def list_devices(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """获取设备列表"""
    if credentials.credentials != SERVER_AGENT_TOKEN:
        log_audit("list_devices", "controller", "unknown", "failure", details={"reason": "invalid_token"})
        raise HTTPException(status_code=401, detail="Invalid token")
    
    devices = []
    for device_id, info in connected_devices.items():
        devices.append({
            "device_id": device_id,
            "device_name": info.device_name,
            "platform": info.platform,
            "connected_at": info.connected_at,
            "last_ping": info.last_ping,
            "online_duration": time.time() - info.connected_at
        })
    
    log_audit("list_devices", "controller", "api", "success", 
              details={"count": len(devices)})
    
    return {"code": 0, "devices": devices}


@app.get("/api/v1/audit-logs")
async def get_audit_logs(
    limit: int = 100,
    actor_id: str = None,
    action: str = None,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """获取审计日志"""
    if credentials.credentials != SERVER_AGENT_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    logs = audit_logs
    
    # 过滤
    if actor_id:
        logs = [l for l in logs if l.actor_id == actor_id]
    if action:
        logs = [l for l in logs if l.action == action]
    
    # 限制数量
    logs = logs[-limit:]
    
    return {
        "code": 0,
        "logs": [l.model_dump() for l in logs],
        "total": len(logs)
    }


# ============== WebSocket 处理 ==============

@app.websocket("/ws/client")
async def websocket_client(websocket: WebSocket):
    """设备端 WebSocket 连接"""
    await websocket.accept()
    
    device_id = None
    try:
        # 等待注册消息
        data = await websocket.receive_json()
        
        if data.get("type") != "register":
            await websocket.send_json({"type": "error", "msg": "Expected register message"})
            return
        
        device_id = data.get("device_id")
        device_name = data.get("device_name", device_id)
        token = data.get("token")
        platform = data.get("platform", "Unknown")
        
        # 验证 token
        if not verify_device_token(token):
            log_audit("register", "device", device_id, "failure", 
                     details={"reason": "invalid_token", "platform": platform})
            await websocket.send_json({
                "type": "error",
                "msg": "Invalid token"
            })
            return
        
        # 注册设备
        connected_devices[device_id] = DeviceInfo(
            device_id=device_id,
            device_name=device_name,
            platform=platform,
            connected_at=time.time(),
            last_ping=time.time(),
            websocket=websocket
        )
        
        # 生成配对密钥
        pairing_key = generate_pairing_key()
        pairing_keys[device_id] = {
            "key": pairing_key,
            "expires_at": time.time() + 3600  # 1 小时过期
        }
        
        # 发送注册成功响应
        await websocket.send_json({
            "type": "registered",
            "device_id": device_id,
            "device_name": device_name,
            "pairing_key": pairing_key
        })
        
        log_audit("register", "device", device_id, "success",
                 details={"platform": platform, "device_name": device_name})
        
        # 保持连接并处理消息
        await handle_device_messages(device_id)
        
    except WebSocketDisconnect:
        if device_id and device_id in connected_devices:
            del connected_devices[device_id]
            log_audit("disconnect", "device", device_id, "success")
    except Exception as e:
        if device_id:
            log_audit("error", "device", device_id, "failure",
                     details={"error": str(e)})
        if device_id and device_id in connected_devices:
            del connected_devices[device_id]


async def handle_device_messages(device_id: str):
    """处理设备消息"""
    device_info = connected_devices.get(device_id)
    if not device_info:
        return
    
    heartbeat_interval = 30
    
    while device_id in connected_devices:
        try:
            # 等待消息，超时则发送心跳
            try:
                data = await asyncio.wait_for(
                    device_info.websocket.receive_json(),
                    timeout=heartbeat_interval
                )
            except asyncio.TimeoutError:
                # 发送心跳
                await device_info.websocket.send_json({
                    "type": "ping",
                    "timestamp": time.time()
                })
                continue
            
            msg_type = data.get("type")
            
            if msg_type == "pong":
                device_info.last_ping = time.time()
            
            elif msg_type == "result":
                # 处理执行结果
                req_id = data.get("req_id")
                if req_id and req_id in device_info.pending_requests:
                    future = device_info.pending_requests[req_id]
                    if not future.done():
                        future.set_result(data)
            
            elif msg_type == "exec":
                # 设备主动执行命令（未来功能）
                pass
        
        except Exception as e:
            print(f"处理设备消息错误 {device_id}: {e}")
            break


@app.websocket("/ws/controller")
async def websocket_controller(websocket: WebSocket):
    """控制器端 WebSocket 连接"""
    await websocket.accept()
    
    controller_id = None
    try:
        # 等待握手
        data = await websocket.receive_json()
        
        if data.get("type") != "controller_handshake":
            await websocket.send_json({"type": "error", "msg": "Expected handshake"})
            return
        
        controller_id = data.get("controller_id")
        platform = data.get("platform", "Unknown")
        
        # 注册控制器
        connected_controllers[controller_id] = ControllerInfo(
            controller_id=controller_id,
            platform=platform,
            connected_at=time.time(),
            last_ping=time.time(),
            websocket=websocket
        )
        
        await websocket.send_json({
            "type": "controller_ready",
            "controller_id": controller_id
        })
        
        log_audit("controller_connect", "controller", controller_id, "success",
                 details={"platform": platform})
        
        # 保持连接并处理消息
        await handle_controller_messages(controller_id)
        
    except WebSocketDisconnect:
        if controller_id and controller_id in connected_controllers:
            # 清理配对关系
            controller_info = connected_controllers[controller_id]
            for device_id in controller_info.paired_devices:
                if device_id in connected_devices:
                    device_info = connected_devices[device_id]
                    device_info.paired_controllers.discard(controller_id)
            
            del connected_controllers[controller_id]
            log_audit("controller_disconnect", "controller", controller_id, "success")
    except Exception as e:
        if controller_id:
            log_audit("controller_error", "controller", controller_id, "failure",
                     details={"error": str(e)})
        if controller_id and controller_id in connected_controllers:
            del connected_controllers[controller_id]


async def handle_controller_messages(controller_id: str):
    """处理控制器消息"""
    controller_info = connected_controllers.get(controller_id)
    if not controller_info:
        return
    
    heartbeat_interval = 30
    
    while controller_id in connected_controllers:
        try:
            try:
                data = await asyncio.wait_for(
                    controller_info.websocket.receive_json(),
                    timeout=heartbeat_interval
                )
            except asyncio.TimeoutError:
                await controller_info.websocket.send_json({
                    "type": "ping",
                    "timestamp": time.time()
                })
                continue
            
            msg_type = data.get("type")
            
            if msg_type == "pong":
                controller_info.last_ping = time.time()
            
            elif msg_type == "pair":
                # 配对设备
                device_id = data.get("device_id")
                pairing_key = data.get("pairing_key")
                
                if device_id in connected_devices:
                    device_info = connected_devices[device_id]
                    stored_key = pairing_keys.get(device_id, {}).get("key")
                    
                    if stored_key and stored_key == pairing_key:
                        # 配对成功
                        device_info.paired_controllers.add(controller_id)
                        controller_info.paired_devices.add(device_id)
                        
                        await controller_info.websocket.send_json({
                            "type": "paired",
                            "device_id": device_id
                        })
                        
                        log_audit("pair", "controller", controller_id, "success",
                                 target_type="device", target_id=device_id)
                    else:
                        await controller_info.websocket.send_json({
                            "type": "error",
                            "msg": "Invalid pairing key"
                        })
                        
                        log_audit("pair", "controller", controller_id, "failure",
                                 target_type="device", target_id=device_id,
                                 details={"reason": "invalid_key"})
            
            elif msg_type == "exec":
                # 执行命令
                device_id = data.get("device_id")
                req_id = data.get("req_id")
                action = data.get("action")
                params = data.get("params", {})
                
                if device_id not in connected_devices:
                    await controller_info.websocket.send_json({
                        "type": "error",
                        "req_id": req_id,
                        "msg": f"Device {device_id} not connected"
                    })
                    continue
                
                device_info = connected_devices[device_id]
                
                if controller_id not in device_info.paired_controllers:
                    await controller_info.websocket.send_json({
                        "type": "error",
                        "req_id": req_id,
                        "msg": "Not paired with this device"
                    })
                    continue
                
                # 创建未来对象等待结果
                future = asyncio.get_event_loop().create_future()
                device_info.pending_requests[req_id] = future
                
                # 转发给设备
                await device_info.websocket.send_json({
                    "type": "exec",
                    "req_id": req_id,
                    "controller_id": controller_id,
                    "action": action,
                    "params": params
                })
                
                log_audit("exec", "controller", controller_id, "success",
                         target_type="device", target_id=device_id,
                         details={"action": action, "req_id": req_id})
                
                # 等待结果
                try:
                    result = await asyncio.wait_for(future, timeout=30)
                    await controller_info.websocket.send_json({
                        "type": "result",
                        "req_id": req_id,
                        "data": result
                    })
                except asyncio.TimeoutError:
                    await controller_info.websocket.send_json({
                        "type": "error",
                        "req_id": req_id,
                        "msg": "Request timeout"
                    })
                    if req_id in device_info.pending_requests:
                        del device_info.pending_requests[req_id]
        
        except Exception as e:
            print(f"处理控制器消息错误 {controller_id}: {e}")
            break


def verify_device_token(token: str) -> bool:
    """验证设备 token"""
    return token == LINUX_DEVICE_TOKEN


# ============== 主函数 ==============

def main():
    """启动服务器"""
    # 创建日志目录
    Path("/var/log/agentlinker").mkdir(parents=True, exist_ok=True)
    
    # SSL 上下文
    ssl_context = None
    if TLS_ENABLED:
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ssl_context.load_cert_chain(TLS_CERT_FILE, TLS_KEY_FILE)
    
    # 启动服务器
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8080,
        ssl=ssl_context,
        log_level="info"
    )


if __name__ == "__main__":
    main()
