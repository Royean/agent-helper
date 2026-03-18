"""
AgentLinker 批量操作模块
支持同时向多台设备发送命令
"""

import asyncio
from typing import List, Dict, Any, Callable
from dataclasses import dataclass
from enum import Enum


class DeviceStatus(Enum):
    """设备状态"""
    ONLINE = "online"
    OFFLINE = "offline"
    ERROR = "error"


@dataclass
class BatchResult:
    """批量执行结果"""
    device_id: str
    success: bool
    result: Any
    error: str = ""
    execution_time: float = 0.0


class BatchExecutor:
    """批量执行器"""
    
    def __init__(self, execute_fn: Callable):
        """
        初始化批量执行器
        
        Args:
            execute_fn: 单个设备的执行函数，签名：async def execute(device_id, action, params) -> dict
        """
        self.execute_fn = execute_fn
        self.results: List[BatchResult] = []
    
    async def execute_batch(self, device_ids: List[str], action: str, 
                           params: dict, timeout: float = 30.0) -> List[BatchResult]:
        """
        批量执行命令
        
        Args:
            device_ids: 设备 ID 列表
            action: 执行动作
            params: 动作参数
            timeout: 单个设备超时时间（秒）
        
        Returns:
            BatchResult 列表
        """
        self.results = []
        
        # 创建所有设备的执行任务
        tasks = []
        for device_id in device_ids:
            task = self._execute_single(device_id, action, params, timeout)
            tasks.append(task)
        
        # 并发执行所有任务
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理结果
        batch_results = []
        for device_id, result in zip(device_ids, results):
            if isinstance(result, Exception):
                batch_results.append(BatchResult(
                    device_id=device_id,
                    success=False,
                    result=None,
                    error=str(result),
                    execution_time=0.0
                ))
            else:
                batch_results.append(result)
        
        self.results = batch_results
        return batch_results
    
    async def _execute_single(self, device_id: str, action: str, 
                             params: dict, timeout: float) -> BatchResult:
        """执行单个设备"""
        import time
        start_time = time.time()
        
        try:
            result = await asyncio.wait_for(
                self.execute_fn(device_id, action, params),
                timeout=timeout
            )
            
            execution_time = time.time() - start_time
            
            return BatchResult(
                device_id=device_id,
                success=result.get("success", False),
                result=result,
                error=result.get("error", ""),
                execution_time=execution_time
            )
        
        except asyncio.TimeoutError:
            execution_time = time.time() - start_time
            return BatchResult(
                device_id=device_id,
                success=False,
                result=None,
                error=f"Timeout after {timeout}s",
                execution_time=execution_time
            )
        
        except Exception as e:
            execution_time = time.time() - start_time
            return BatchResult(
                device_id=device_id,
                success=False,
                result=None,
                error=str(e),
                execution_time=execution_time
            )
    
    def get_summary(self) -> Dict[str, Any]:
        """获取执行摘要"""
        total = len(self.results)
        success = sum(1 for r in self.results if r.success)
        failed = total - success
        
        total_time = sum(r.execution_time for r in self.results)
        avg_time = total_time / total if total > 0 else 0
        
        return {
            "total_devices": total,
            "success_count": success,
            "failed_count": failed,
            "success_rate": f"{success/total*100:.1f}%" if total > 0 else "0%",
            "total_time": f"{total_time:.2f}s",
            "avg_time": f"{avg_time:.2f}s"
        }
    
    def get_failed_devices(self) -> List[str]:
        """获取失败的设备列表"""
        return [r.device_id for r in self.results if not r.success]
    
    def get_results_by_device(self) -> Dict[str, BatchResult]:
        """按设备 ID 获取结果"""
        return {r.device_id: r for r in self.results}


class DeviceGroup:
    """设备分组管理器"""
    
    def __init__(self):
        self.groups: Dict[str, Dict[str, Any]] = {}
        self.devices: Dict[str, Dict[str, Any]] = {}
    
    def create_group(self, group_id: str, name: str, color: str = "#4287f5") -> bool:
        """创建分组"""
        if group_id in self.groups:
            return False
        
        self.groups[group_id] = {
            "group_id": group_id,
            "name": name,
            "color": color,
            "devices": [],
            "expanded": True,
            "created_at": asyncio.get_event_loop().time()
        }
        return True
    
    def delete_group(self, group_id: str) -> bool:
        """删除分组"""
        if group_id not in self.groups:
            return False
        
        # 移除设备关联
        for device_id in self.groups[group_id]["devices"]:
            if device_id in self.devices:
                self.devices[device_id]["group_id"] = None
        
        del self.groups[group_id]
        return True
    
    def add_device_to_group(self, device_id: str, group_id: str) -> bool:
        """添加设备到分组"""
        if group_id not in self.groups:
            return False
        
        if device_id not in self.devices:
            self.devices[device_id] = {
                "device_id": device_id,
                "group_id": None,
                "name": device_id,
                "status": DeviceStatus.OFFLINE.value
            }
        
        # 从旧分组移除
        old_group_id = self.devices[device_id].get("group_id")
        if old_group_id and old_group_id in self.groups:
            if device_id in self.groups[old_group_id]["devices"]:
                self.groups[old_group_id]["devices"].remove(device_id)
        
        # 添加到新分组
        self.devices[device_id]["group_id"] = group_id
        if device_id not in self.groups[group_id]["devices"]:
            self.groups[group_id]["devices"].append(device_id)
        
        return True
    
    def remove_device_from_group(self, device_id: str) -> bool:
        """从分组移除设备"""
        if device_id not in self.devices:
            return False
        
        group_id = self.devices[device_id].get("group_id")
        if group_id and group_id in self.groups:
            if device_id in self.groups[group_id]["devices"]:
                self.groups[group_id]["devices"].remove(device_id)
        
        self.devices[device_id]["group_id"] = None
        return True
    
    def get_group_devices(self, group_id: str) -> List[str]:
        """获取分组内的设备列表"""
        if group_id not in self.groups:
            return []
        return self.groups[group_id]["devices"].copy()
    
    def get_device_group(self, device_id: str) -> str:
        """获取设备所在分组"""
        if device_id not in self.devices:
            return None
        return self.devices[device_id].get("group_id")
    
    def list_groups(self) -> List[Dict[str, Any]]:
        """列出所有分组"""
        result = []
        for group_id, group in self.groups.items():
            result.append({
                **group,
                "device_count": len(group["devices"]),
                "online_count": sum(
                    1 for d in group["devices"]
                    if self.devices.get(d, {}).get("status") == DeviceStatus.ONLINE.value
                )
            })
        return result
    
    def list_devices(self, group_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """列出设备"""
        result = []
        
        for device_id, device in self.devices.items():
            if group_id is None or device.get("group_id") == group_id:
                result.append({
                    **device,
                    "group_name": self.groups.get(device.get("group_id"), {}).get("name")
                })
        
        return result
    
    def update_device_status(self, device_id: str, status: DeviceStatus) -> bool:
        """更新设备状态"""
        if device_id not in self.devices:
            return False
        
        self.devices[device_id]["status"] = status.value
        return True
    
    def export_config(self) -> str:
        """导出配置为 JSON"""
        import json
        return json.dumps({
            "groups": self.groups,
            "devices": self.devices
        }, indent=2)
    
    def import_config(self, config_json: str) -> bool:
        """从 JSON 导入配置"""
        try:
            import json
            config = json.loads(config_json)
            
            self.groups = config.get("groups", {})
            self.devices = config.get("devices", {})
            
            return True
        except:
            return False
    
    @classmethod
    def from_config(cls, config_json: str) -> 'DeviceGroup':
        """从配置创建实例"""
        instance = cls()
        instance.import_config(config_json)
        return instance
