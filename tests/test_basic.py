#!/usr/bin/env python3
"""
AgentLinker 测试脚本
测试服务端、客户端、控制器功能
"""

import asyncio
import json
import sys
import time

# 添加客户端模块路径
sys.path.insert(0, '/tmp/AgentLinker/client')
sys.path.insert(0, '/tmp/AgentLinker/client/core')

from core import Config, AgentClient, generate_device_id, Executor

SERVER_URL = "ws://127.0.0.1:8080/ws/client"
CONTROLLER_URL = "ws://127.0.0.1:8080/ws/controller"


async def test_executor():
    """测试指令执行器"""
    print("\n=== 测试指令执行器 ===\n")
    
    # 测试系统信息
    print("1. 测试 system.info")
    result = Executor.execute("system.info", {})
    if result.get("success"):
        data = result.get("data", {})
        print(f"   主机名：{data.get('hostname')}")
        print(f"   系统：{data.get('system')}")
        print(f"   Python: {data.get('python_version')}")
    else:
        print(f"   失败：{result.get('error')}")
    
    # 测试 shell 命令
    print("\n2. 测试 shell.exec")
    result = Executor.execute("shell.exec", {"cmd": "echo 'Hello from AgentLinker!'"})
    if result.get("success"):
        print(f"   输出：{result.get('stdout', '').strip()}")
    else:
        print(f"   失败：{result.get('error')}")
    
    # 测试文件列表
    print("\n3. 测试 file.list")
    result = Executor.execute("file.list", {"path": "/tmp"})
    if result.get("success"):
        data = result.get("data", {})
        print(f"   /tmp 下有 {len(data.get('entries', []))} 个文件/目录")
    else:
        print(f"   失败：{result.get('error')}")
    
    print("\n✅ 指令执行器测试完成\n")


async def test_client_connection():
    """测试客户端连接"""
    print("\n=== 测试客户端连接 ===\n")
    
    # 创建临时配置
    config_data = {
        "device_id": generate_device_id(),
        "device_name": "Test Client",
        "token": "ah_device_token_change_in_production",
        "server_url": SERVER_URL,
    }
    
    config = Config("/tmp/test_agentlinker_config.json")
    config.data = config_data
    config.save()
    
    client = AgentClient(config)
    
    print(f"设备 ID: {config.device_id}")
    print(f"服务端：{config.server_url}")
    print("正在连接...")
    
    # 尝试连接
    if await client.connect():
        print("✅ 连接成功！")
        
        # 保持连接几秒钟
        await asyncio.sleep(5)
        client.stop()
        print("连接已关闭")
    else:
        print("❌ 连接失败")
    
    # 清理临时配置
    import os
    if os.path.exists("/tmp/test_agentlinker_config.json"):
        os.remove("/tmp/test_agentlinker_config.json")


async def main():
    """主测试函数"""
    print("=" * 50)
    print("AgentLinker 功能测试")
    print("=" * 50)
    
    # 测试指令执行器
    await test_executor()
    
    # 测试客户端连接
    await test_client_connection()
    
    print("=" * 50)
    print("所有测试完成！")
    print("=" * 50)
    print("\n下一步:")
    print("1. 在阿里云主机上安装被控端")
    print("2. 使用配对密钥连接")
    print("3. 测试远程控制功能")
    print("")


if __name__ == "__main__":
    asyncio.run(main())
