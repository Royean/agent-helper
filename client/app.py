#!/usr/bin/env python3
"""
AgentLinker Client App
图形化客户端 - 菜单栏应用
"""

import asyncio
import json
import os
import platform
import sys
import time
import uuid
from pathlib import Path

# 添加核心模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))

from core import Config, AgentClient, generate_device_id, Executor

# 检查是否有 GUI 支持
try:
    import tkinter as tk
    from tkinter import messagebox, ttk
    HAS_TK = True
except:
    HAS_TK = False

# 默认配置
DEFAULT_SERVER = "ws://43.98.243.80:8080/ws/client"
DEFAULT_TOKEN = "ah_device_token_change_in_production"
CONFIG_DIR = Path.home() / ".agentlinker"
CONFIG_FILE = CONFIG_DIR / "config.json"


class AgentLinkerApp:
    """AgentLinker 客户端应用"""
    
    def __init__(self):
        self.config = self._load_config()
        self.client = None
        self.pairing_key = None
        self.running = False
        self.root = None
        
    def _load_config(self) -> dict:
        """加载配置"""
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        # 默认配置
        return {
            "device_id": generate_device_id(),
            "device_name": f"{platform.node()} ({platform.system()})",
            "token": DEFAULT_TOKEN,
            "server_url": DEFAULT_SERVER,
            "auto_start": True
        }
    
    def _save_config(self):
        """保存配置"""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, 'w') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def show_gui(self):
        """显示图形界面"""
        if not HAS_TK:
            print("❌ 不支持图形界面，使用命令行模式")
            self.run_cli()
            return
        
        self.root = tk.Tk()
        self.root.title("AgentLinker")
        self.root.geometry("500x400")
        self.root.resizable(True, True)
        
        # 标题
        title = tk.Label(
            self.root,
            text="🤖 AgentLinker",
            font=("Arial", 20, "bold")
        )
        title.pack(pady=20)
        
        # 状态框架
        status_frame = tk.LabelFrame(self.root, text="状态", padx=10, pady=10)
        status_frame.pack(fill="x", padx=20, pady=10)
        
        self.status_label = tk.Label(status_frame, text="⚪ 未连接", fg="gray")
        self.status_label.pack()
        
        # 设备信息框架
        device_frame = tk.LabelFrame(self.root, text="设备信息", padx=10, pady=10)
        device_frame.pack(fill="x", padx=20, pady=10)
        
        tk.Label(device_frame, text=f"设备 ID: {self.config['device_id']}").pack(anchor="w")
        tk.Label(device_frame, text=f"设备名称: {self.config['device_name']}").pack(anchor="w")
        
        self.pairing_label = tk.Label(device_frame, text="配对密钥：等待连接...", fg="blue")
        self.pairing_label.pack(anchor="w")
        
        # 按钮框架
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=20)
        
        self.start_btn = tk.Button(
            btn_frame,
            text="启动服务",
            command=self.toggle_service,
            bg="green",
            fg="white",
            padx=20,
            pady=10
        )
        self.start_btn.pack(side="left", padx=10)
        
        copy_btn = tk.Button(
            btn_frame,
            text="复制配对密钥",
            command=self.copy_pairing_key,
            padx=20,
            pady=10
        )
        copy_btn.pack(side="left", padx=10)
        
        # 日志框架
        log_frame = tk.LabelFrame(self.root, text="日志", padx=10, pady=10)
        log_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.log_text = tk.Text(log_frame, height=8, wrap="word")
        self.log_text.pack(fill="both", expand=True)
        
        scrollbar = tk.Scrollbar(log_frame, command=self.log_text.yview)
        scrollbar.pack(side="right", fill="y")
        self.log_text.config(yscrollcommand=scrollbar.set)
        
        # 菜单
        menubar = tk.Menu(self.root)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="修改设备 ID", command=self.edit_device_id)
        file_menu.add_command(label="修改服务器", command=self.edit_server)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.on_close)
        menubar.add_cascade(label="文件", menu=file_menu)
        self.root.config(menu=menubar)
        
        # 窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        self.log("✅ 应用已启动")
        self.log(f"设备 ID: {self.config['device_id']}")
        self.log(f"服务器：{self.config['server_url']}")
        
        # 自动启动
        if self.config.get('auto_start', True):
            self.root.after(1000, self.start_client)
        
        self.root.mainloop()
    
    def log(self, message: str):
        """添加日志"""
        timestamp = time.strftime("%H:%M:%S")
        log_line = f"[{timestamp}] {message}\n"
        
        if hasattr(self, 'log_text') and self.log_text:
            self.log_text.insert("end", log_line)
            self.log_text.see("end")
        else:
            print(log_line.strip())
    
    def toggle_service(self):
        """切换服务状态"""
        if self.running:
            self.stop_client()
        else:
            self.start_client()
    
    def start_client(self):
        """启动客户端"""
        if self.running:
            return
        
        self.log("正在连接服务端...")
        self.status_label.config(text="🟡 连接中...", fg="orange")
        
        # 在后台线程运行
        import threading
        thread = threading.Thread(target=self._run_client, daemon=True)
        thread.start()
    
    def _run_client(self):
        """运行客户端（后台线程）"""
        try:
            config = Config(str(CONFIG_FILE))
            config.data = self.config
            
            self.client = AgentClient(config)
            
            # 连接
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            connected = loop.run_until_complete(self.client.connect())
            
            if connected:
                self.running = True
                
                # 等待配对密钥
                for _ in range(30):  # 最多等 30 秒
                    if self.client.pairing_key:
                        self.pairing_key = self.client.pairing_key
                        self.root.after(0, self._on_pairing_key_received, self.pairing_key)
                        break
                    time.sleep(1)
                
                # 处理消息
                loop.run_until_complete(self.client.handle_messages())
            else:
                self.root.after(0, self._on_connection_failed)
                
        except Exception as e:
            self.root.after(0, self._on_error, str(e))
    
    def _on_pairing_key_received(self, pairing_key: str):
        """配对密钥收到回调"""
        self.status_label.config(text="🟢 已连接", fg="green")
        self.pairing_label.config(text=f"配对密钥：{pairing_key}", fg="green")
        self.start_btn.config(text="停止服务", bg="red")
        self.log(f"✅ 连接成功！配对密钥：{pairing_key}")
    
    def _on_connection_failed(self):
        """连接失败回调"""
        self.status_label.config(text="🔴 连接失败", fg="red")
        self.log("❌ 连接失败，请检查服务器地址")
    
    def _on_error(self, error: str):
        """错误回调"""
        self.status_label.config(text="🔴 错误", fg="red")
        self.log(f"❌ 错误：{error}")
    
    def stop_client(self):
        """停止客户端"""
        if self.client:
            self.client.stop()
        self.running = False
        self.status_label.config(text="⚪ 已停止", fg="gray")
        self.start_btn.config(text="启动服务", bg="green")
        self.log("服务已停止")
    
    def copy_pairing_key(self):
        """复制配对密钥到剪贴板"""
        if self.pairing_key:
            self.root.clipboard_clear()
            self.root.clipboard_append(self.pairing_key)
            self.log(f"✅ 配对密钥已复制：{self.pairing_key}")
            messagebox.showinfo("复制成功", f"配对密钥 {self.pairing_key} 已复制到剪贴板")
        else:
            messagebox.showwarning("无密钥", "请先启动服务获取配对密钥")
    
    def edit_device_id(self):
        """修改设备 ID"""
        dialog = tk.Toplevel(self.root)
        dialog.title("修改设备 ID")
        dialog.geometry("400x150")
        
        tk.Label(dialog, text="设备 ID:").pack(pady=10)
        
        entry = tk.Entry(dialog, width=50)
        entry.insert(0, self.config['device_id'])
        entry.pack(pady=5)
        
        def save():
            new_id = entry.get().strip()
            if new_id:
                self.config['device_id'] = new_id
                self._save_config()
                self.log(f"设备 ID 已修改：{new_id}")
                messagebox.showinfo("成功", "设备 ID 已保存")
            dialog.destroy()
        
        tk.Button(dialog, text="保存", command=save).pack(pady=10)
    
    def edit_server(self):
        """修改服务器地址"""
        dialog = tk.Toplevel(self.root)
        dialog.title("修改服务器")
        dialog.geometry("500x150")
        
        tk.Label(dialog, text="WebSocket 服务器地址:").pack(pady=10)
        
        entry = tk.Entry(dialog, width=60)
        entry.insert(0, self.config['server_url'])
        entry.pack(pady=5)
        
        def save():
            new_url = entry.get().strip()
            if new_url:
                self.config['server_url'] = new_url
                self._save_config()
                self.log(f"服务器已修改：{new_url}")
                messagebox.showinfo("成功", "服务器地址已保存，重启生效")
            dialog.destroy()
        
        tk.Button(dialog, text="保存", command=save).pack(pady=10)
    
    def run_cli(self):
        """命令行模式"""
        print("=" * 60)
        print("AgentLinker 客户端")
        print("=" * 60)
        print(f"设备 ID: {self.config['device_id']}")
        print(f"服务器：{self.config['server_url']}")
        print("=" * 60)
        
        # 启动客户端
        self.start_client()
    
    def on_close(self):
        """关闭应用"""
        self.stop_client()
        if self.root:
            self.root.destroy()
        sys.exit(0)


def main():
    """主函数"""
    app = AgentLinkerApp()
    app.show_gui()


if __name__ == "__main__":
    main()
