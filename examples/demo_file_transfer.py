#!/usr/bin/env python3
"""
AgentLinker 文件传输演示
演示完整的文件上传/下载流程
"""

import asyncio
import json
import sys
import time
from pathlib import Path

# 添加模块路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from client.file_transfer import FileTransfer


def format_size(size: int) -> str:
    """格式化文件大小"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def print_progress(transferred: int, total: int, start_time: float):
    """打印进度条"""
    percent = (transferred / total * 100) if total > 0 else 0
    bar_length = 50
    filled = int(bar_length * percent / 100)
    bar = '█' * filled + '░' * (bar_length - filled)
    
    elapsed = time.time() - start_time
    speed = transferred / elapsed if elapsed > 0 else 0
    
    def format_speed(s):
        if s < 1024:
            return f"{s:.1f} B/s"
        elif s < 1024 * 1024:
            return f"{s/1024:.1f} KB/s"
        else:
            return f"{s/(1024*1024):.1f} MB/s"
    
    # 清除行
    sys.stdout.write('\r' + ' ' * 120 + '\r')
    sys.stdout.write(f'[{bar}] {percent:5.1f}% | {format_size(transferred)}/{format_size(total)} | {format_speed(speed)}')
    sys.stdout.flush()
    
    if transferred >= total:
        print()  # 换行


async def demo_upload():
    """演示文件上传"""
    print("\n" + "=" * 80)
    print(" AgentLinker 文件传输演示 - 上传")
    print("=" * 80 + "\n")
    
    # 创建测试文件
    test_file = Path("/tmp/test_upload.bin")
    test_size = 10 * 1024 * 1024  # 10MB
    
    print(f"📝 创建测试文件：{test_file}")
    print(f"   大小：{format_size(test_size)}")
    
    # 创建随机数据
    with open(test_file, "wb") as f:
        f.write((b"0123456789ABCDEF" * (test_size // 16))[:test_size])
    
    print(f"✅ 测试文件已创建\n")
    
    # 模拟上传
    file_transfer = FileTransfer()
    start_time = time.time()
    
    print("📤 开始上传...")
    print()
    
    async def mock_send(data):
        """模拟发送数据"""
        await asyncio.sleep(0.001)  # 模拟网络延迟
    
    result = await file_transfer.upload_file(
        file_path=str(test_file),
        send_callback=mock_send,
        progress_callback=lambda t, total: print_progress(t, total, start_time)
    )
    
    print()
    if result.get("success"):
        print("✅ 上传成功！")
        print(f"\n📊 传输统计:")
        print(f"   文件名：{result.get('filename')}")
        print(f"   大小：{format_size(result.get('file_size', 0))}")
        print(f"   耗时：{result.get('duration', 0):.2f} 秒")
        print(f"   速度：{format_size(result.get('speed', 0)/1024/1024)}/s")
        print(f"   文件 ID: {result.get('file_id')}")
    else:
        print(f"❌ 上传失败：{result.get('error')}")
    
    # 清理测试文件
    test_file.unlink()
    print(f"\n🗑️  测试文件已清理")
    print()


async def demo_download():
    """演示文件下载"""
    print("\n" + "=" * 80)
    print(" AgentLinker 文件传输演示 - 下载")
    print("=" * 80 + "\n")
    
    print("⚠️  下载功能需要服务端支持")
    print("   当前为模拟演示...\n")
    
    # 模拟下载进度
    total_size = 5 * 1024 * 1024  # 5MB
    start_time = time.time()
    transferred = 0
    chunk_size = total_size // 50
    
    print("📥 开始下载...")
    print()
    
    for i in range(50):
        await asyncio.sleep(0.05)  # 模拟网络延迟
        transferred = min(transferred + chunk_size, total_size)
        print_progress(transferred, total_size, start_time)
    
    print()
    print("✅ 下载完成！")
    
    elapsed = time.time() - start_time
    speed = total_size / elapsed if elapsed > 0 else 0
    
    print(f"\n📊 传输统计:")
    print(f"   大小：{format_size(total_size)}")
    print(f"   耗时：{elapsed:.2f} 秒")
    print(f"   速度：{format_size(speed/1024/1024)}/s")
    print()


async def demo_chunk_transfer():
    """演示分块传输细节"""
    print("\n" + "=" * 80)
    print(" AgentLinker 文件传输 - 分块传输详解")
    print("=" * 80 + "\n")
    
    print("📋 分块传输流程:\n")
    
    # 创建小测试文件
    test_file = Path("/tmp/test_chunk.bin")
    test_size = 2 * 1024 * 1024  # 2MB
    chunk_size = 256 * 1024  # 256KB
    
    print(f"1️⃣  准备文件：{format_size(test_size)}")
    print(f"   分块大小：{format_size(chunk_size)}")
    print(f"   预计分块数：{test_size // chunk_size + 1}\n")
    
    with open(test_file, "wb") as f:
        f.write((b"ABCDEFGHIJKLMNOP" * (test_size // 16))[:test_size])
    
    print(f"2️⃣  读取并分块:\n")
    
    chunk_index = 0
    with open(test_file, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            
            print(f"   分块 {chunk_index:2d}: {len(chunk):6d} bytes")
            chunk_index += 1
            
            await asyncio.sleep(0.1)  # 模拟处理时间
    
    print(f"\n3️⃣  所有分块已发送")
    print(f"   总分块数：{chunk_index}")
    print(f"   总大小：{format_size(test_size)}\n")
    
    # 清理
    test_file.unlink()
    print(f"4️⃣  测试完成，文件已清理\n")


async def main():
    """主函数"""
    print("\n" + "🚀" * 40)
    print(" AgentLinker 文件传输演示")
    print(" 分块传输 | 哈希验证 | 进度显示 | 速度统计")
    print("🚀" * 40 + "\n")
    
    # 演示 1: 上传
    await demo_upload()
    
    # 演示 2: 下载
    await demo_download()
    
    # 演示 3: 分块传输详解
    await demo_chunk_transfer()
    
    print("\n" + "=" * 80)
    print(" ✨ 演示完成！")
    print("=" * 80)
    print("\n📚 更多信息请查看:")
    print("   docs/文件传输指南.md")
    print("\n💻 使用命令行工具:")
    print("   python3 tools/file_transfer_cli.py upload file.txt -d device-001")
    print("   python3 tools/file_transfer_cli.py download file_id -s /tmp/file.txt")
    print("\n🔗 GitHub: https://github.com/Royean/AgentLinker")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
