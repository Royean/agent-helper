"""
AgentLinker 文件传输模块
支持上传、下载、断点续传
"""

import os
import json
import hashlib
import base64
from pathlib import Path
from typing import Dict, Any, Optional


class FileTransfer:
    """文件传输管理器"""
    
    @staticmethod
    def get_file_info(path: str) -> Dict[str, Any]:
        """获取文件信息"""
        try:
            file_path = Path(path)
            if not file_path.exists():
                return {"success": False, "error": "File not found"}
            
            stat = file_path.stat()
            
            # 计算 MD5
            md5_hash = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    md5_hash.update(chunk)
            
            return {
                "success": True,
                "data": {
                    "path": str(file_path.absolute()),
                    "name": file_path.name,
                    "size": stat.st_size,
                    "size_human": FileTransfer._human_readable_size(stat.st_size),
                    "modified": stat.st_mtime,
                    "created": stat.st_ctime,
                    "is_file": file_path.is_file(),
                    "is_dir": file_path.is_dir(),
                    "md5": md5_hash.hexdigest()
                }
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def read_file_chunk(path: str, offset: int = 0, size: int = 1024 * 1024) -> Dict[str, Any]:
        """读取文件块（用于分块传输）"""
        try:
            with open(path, "rb") as f:
                f.seek(offset)
                chunk = f.read(size)
                
                return {
                    "success": True,
                    "data": {
                        "chunk": base64.b64encode(chunk).decode('utf-8'),
                        "offset": offset,
                        "size": len(chunk),
                        "eof": len(chunk) < size
                    }
                }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def write_file_chunk(path: str, chunk_base64: str, offset: int = 0) -> Dict[str, Any]:
        """写入文件块"""
        try:
            # 解码
            chunk = base64.b64decode(chunk_base64)
            
            # 创建父目录
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            
            # 写入
            mode = "r+b" if offset > 0 else "wb"
            with open(path, mode) as f:
                f.seek(offset)
                f.write(chunk)
            
            return {
                "success": True,
                "data": {
                    "written": len(chunk),
                    "offset": offset
                }
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def upload_file(path: str, content_base64: Optional[str] = None, 
                   chunked: bool = False) -> Dict[str, Any]:
        """
        上传文件
        
        两种方式：
        1. 直接上传（小文件）：提供 content_base64
        2. 分块上传（大文件）：分多次调用 write_file_chunk
        """
        try:
            if chunked:
                # 分块上传模式
                return {
                    "success": True,
                    "message": "Chunked upload initialized",
                    "data": {
                        "path": path,
                        "chunked": True,
                        "chunk_size": 1024 * 1024  # 1MB per chunk
                    }
                }
            else:
                # 直接上传
                if not content_base64:
                    return {"success": False, "error": "No content provided"}
                
                content = base64.b64decode(content_base64)
                Path(path).parent.mkdir(parents=True, exist_ok=True)
                
                with open(path, "wb") as f:
                    f.write(content)
                
                return {
                    "success": True,
                    "data": {
                        "path": path,
                        "size": len(content),
                        "md5": hashlib.md5(content).hexdigest()
                    }
                }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def download_file(path: str, chunked: bool = False) -> Dict[str, Any]:
        """
        下载文件
        
        两种方式：
        1. 直接下载（小文件）：返回完整 base64
        2. 分块下载（大文件）：返回文件信息，客户端分块请求
        """
        try:
            file_path = Path(path)
            if not file_path.exists():
                return {"success": False, "error": "File not found"}
            
            if chunked:
                # 分块下载模式
                stat = file_path.stat()
                chunk_size = 1024 * 1024  # 1MB
                total_chunks = (stat.st_size + chunk_size - 1) // chunk_size
                
                return {
                    "success": True,
                    "data": {
                        "path": str(file_path.absolute()),
                        "name": file_path.name,
                        "size": stat.st_size,
                        "chunked": True,
                        "chunk_size": chunk_size,
                        "total_chunks": total_chunks
                    }
                }
            else:
                # 直接下载（限制文件大小）
                max_size = 10 * 1024 * 1024  # 10MB
                stat = file_path.stat()
                
                if stat.st_size > max_size:
                    return {
                        "success": False,
                        "error": f"File too large ({FileTransfer._human_readable_size(stat.st_size)}). Use chunked mode."
                    }
                
                with open(file_path, "rb") as f:
                    content = f.read()
                
                return {
                    "success": True,
                    "data": {
                        "path": str(file_path.absolute()),
                        "name": file_path.name,
                        "size": stat.st_size,
                        "content": base64.b64encode(content).decode('utf-8'),
                        "md5": hashlib.md5(content).hexdigest()
                    }
                }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def transfer_status(transfer_id: str) -> Dict[str, Any]:
        """查询传输状态"""
        # TODO: 实现传输状态跟踪
        return {
            "success": True,
            "data": {
                "transfer_id": transfer_id,
                "status": "completed",
                "progress": 100
            }
        }
    
    @staticmethod
    def transfer_cancel(transfer_id: str) -> Dict[str, Any]:
        """取消传输"""
        # TODO: 实现传输取消
        return {
            "success": True,
            "message": f"Transfer {transfer_id} cancelled"
        }
    
    @staticmethod
    def _human_readable_size(size_bytes: int) -> str:
        """人类可读的文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"


# 导出到 Executor
def register_file_actions():
    """注册文件传输相关指令"""
    from core import Executor
    
    # 添加文件传输方法到 Executor
    Executor.file_transfer = FileTransfer
    
    # 注册新的 action handlers
    original_handlers = {
        "file.info": lambda params: FileTransfer.get_file_info(params.get("path", "")),
        "file.upload": lambda params: FileTransfer.upload_file(
            params.get("path", ""),
            params.get("content_base64"),
            params.get("chunked", False)
        ),
        "file.download": lambda params: FileTransfer.download_file(
            params.get("path", ""),
            params.get("chunked", False)
        ),
        "file.read_chunk": lambda params: FileTransfer.read_file_chunk(
            params.get("path", ""),
            params.get("offset", 0),
            params.get("size", 1024 * 1024)
        ),
        "file.write_chunk": lambda params: FileTransfer.write_file_chunk(
            params.get("path", ""),
            params.get("chunk_base64", ""),
            params.get("offset", 0)
        ),
        "file.transfer.status": lambda params: FileTransfer.transfer_status(
            params.get("transfer_id", "")
        ),
        "file.transfer.cancel": lambda params: FileTransfer.transfer_cancel(
            params.get("transfer_id", "")
        ),
    }
    
    # 合并到 Executor 的 handlers
    for action, handler in original_handlers.items():
        if not hasattr(Executor, f'_file_handler_{action}'):
            setattr(Executor, f'_file_handler_{action}', handler)
    
    # 修改 Executor.execute 以支持新的 handlers
    original_execute = Executor.execute
    
    def new_execute(action: str, params: dict):
        file_handlers = {
            "file.info": lambda p: FileTransfer.get_file_info(p.get("path", "")),
            "file.upload": lambda p: FileTransfer.upload_file(
                p.get("path", ""),
                p.get("content_base64"),
                p.get("chunked", False)
            ),
            "file.download": lambda p: FileTransfer.download_file(
                p.get("path", ""),
                p.get("chunked", False)
            ),
            "file.read_chunk": lambda p: FileTransfer.read_file_chunk(
                p.get("path", ""),
                p.get("offset", 0),
                p.get("size", 1024 * 1024)
            ),
            "file.write_chunk": lambda p: FileTransfer.write_file_chunk(
                p.get("path", ""),
                p.get("chunk_base64", ""),
                p.get("offset", 0)
            ),
            "file.transfer.status": lambda p: FileTransfer.transfer_status(
                p.get("transfer_id", "")
            ),
            "file.transfer.cancel": lambda p: FileTransfer.transfer_cancel(
                p.get("transfer_id", "")
            ),
        }
        
        if action in file_handlers:
            return file_handlers[action](params)
        
        return original_execute(action, params)
    
    Executor.execute = staticmethod(new_execute)
    
    return True
