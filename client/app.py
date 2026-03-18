#!/usr/bin/env python3
"""
AgentLinker Client App v2.1
现代化图形客户端 - 支持深色模式、菜单栏
"""

import asyncio
import json
import os
import platform
import sys
import time
import uuid
import webbrowser
from pathlib import Path
from datetime import datetime

# 添加核心模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))

from core import Config, AgentClient, generate_device_id, Executor

# 检查 GUI 支持
try:
    import tkinter as tk
    from tkinter import messagebox, ttk
    HAS_TK = True
except:
    HAS_TK = False

# 尝试导入深色模式支持
try:
    import darkdetect
    HAS_DARKDETECT = True
except:
    HAS_DARKDETECT = False

# 默认配置
DEFAULT_SERVER = "ws://43.98.243.80:8080/ws/client"
DEFAULT_TOKEN = "ah_device_token_change_in_production"
CONFIG_DIR = Path.home() / ".agentlinker"
CONFIG_FILE = CONFIG_DIR / "config.json"
VERSION = "2.1.0"


class ModernStyle:
    """现代化 UI 样式"""
    
    # 浅色主题
    LIGHT = {
        'bg': '#ffffff',
        'fg': '#1a1a1a',
        'accent': '#4287f5',
        'accent_light': '#669eea',
        'success': '#34c759',
        'warning': '#ff9500',
        'error': '#ff3b30',
        'border': '#e0e0e0',
        'log_bg': '#f5f5f5',
        'button_bg': '#4287f5',
        'button_fg': '#ffffff',
        'header_font': ('SF Pro Display', 24, 'bold'),
        'text_font': ('SF Pro Text', 13),
        'small_font': ('SF Pro Text', 11),
        'mono_font': ('SF Mono', 11),
    }
    
    # 深色主题
    DARK = {
        'bg': '#1c1c1e',
        'fg': '#ffffff',
        'accent': '#0a84ff',
        'accent_light': '#409cff',
        'success': '#30d158',
        'warning': '#ff9f0a',
        'error': '#ff453a',
        'border': '#38383a',
        'log_bg': '#2c2c2e',
        'button_bg': '#0a84ff',
        'button_fg': '#ffffff',
        'header_font': ('SF Pro Display', 24, 'bold'),
        'text_font': ('SF Pro Text', 13),
        'small_font': ('SF Pro Text', 11),
        'mono_font': ('SF Mono', 11),
    }
    
    @classmethod
    def get_theme(cls, dark_mode=None):
        """获取当前主题"""
        if dark_mode is None:
            if HAS_DARKDETECT:
                dark_mode = darkdetect.isDark()
            else:
                dark_mode = False
        
        return cls.DARK if dark_mode else cls.LIGHT


class AgentLinkerApp:
    """AgentLinker 现代化客户端"""
    
    def __init__(self):
        self.config = self._load_config()
        self.client = None
        self.pairing_key = None
        self.running = False
        self.root = None
        self.style = None
        self.dark_mode = self.config.get('dark_mode', None)  # None = 自动
        
    def _load_config(self) -> dict:
        """加载配置"""
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        return {
            "device_id": generate_device_id(),
            "device_name": f"{platform.node()} ({platform.system()})",
            "token": DEFAULT_TOKEN,
            "server_url": DEFAULT_SERVER,
            "auto_start": True,
            "minimize_to_tray": True,
            "dark_mode": None,
            "copy_on_start": True
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
        
        # 应用主题
        self.style = ModernStyle.get_theme(self.dark_mode)
        
        self.root = tk.Tk()
        self.root.title("AgentLinker")
        self.root.geometry("600x500")
        self.root.minsize(500, 400)
        
        # 设置窗口背景色
        self.root.configure(bg=self.style['bg'])
        
        # 标题栏框架
        header_frame = tk.Frame(self.root, bg=self.style['bg'])
        header_frame.pack(fill="x", padx=30, pady=(20, 10))
        
        # 标题
        title = tk.Label(
            header_frame,
            text="🤖 AgentLinker",
            font=self.style['header_font'],
            fg=self.style['fg'],
            bg=self.style['bg']
        )
        title.pack(side="left")
        
        # 版本标签
        version = tk.Label(
            header_frame,
            text=f"v{VERSION}",
            font=self.style['small_font'],
            fg=self.style['accent'],
            bg=self.style['bg']
        )
        version.pack(side="right", pady=10)
        
        # 状态卡片
        status_frame = tk.LabelFrame(
            self.root,
            text="  状态  ",
            font=self.style['small_font'],
            fg=self.style['fg'],
            bg=self.style['bg'],
            padx=15,
            pady=15
        )
        status_frame.pack(fill="x", padx=30, pady=10)
        
        self.status_indicator = tk.Label(
            status_frame,
            text="⚪",
            font=("Arial", 20),
            bg=self.style['bg']
        )
        self.status_indicator.pack(side="left", padx=(0, 10))
        
        self.status_label = tk.Label(
            status_frame,
            text="未连接",
            font=self.style['text_font'],
            fg=self.style['fg'],
            bg=self.style['bg']
        )
        self.status_label.pack(side="left")
        
        # 设备信息卡片
        device_frame = tk.LabelFrame(
            self.root,
            text="  设备信息  ",
            font=self.style['small_font'],
            fg=self.style['fg'],
            bg=self.style['bg'],
            padx=15,
            pady=15
        )
        device_frame.pack(fill="x", padx=30, pady=10)
        
        info_grid = tk.Frame(device_frame, bg=self.style['bg'])
        info_grid.pack(fill="x")
        
        # 设备 ID
        tk.Label(
            info_grid,
            text="设备 ID:",
            font=self.style['text_font'],
            fg=self.style['fg'],
            bg=self.style['bg']
        ).grid(row=0, column=0, sticky="w", pady=5)
        
        self.device_id_var = tk.StringVar(value=self.config['device_id'])
        device_id_entry = tk.Entry(
            info_grid,
            textvariable=self.device_id_var,
            font=self.style['mono_font'],
            bg=self.style['log_bg'],
            fg=self.style['fg'],
            relief="flat",
            width=40
        )
        device_id_entry.grid(row=0, column=1, sticky="ew", pady=5, padx=(10, 0))
        
        # 设备名称
        tk.Label(
            info_grid,
            text="名称:",
            font=self.style['text_font'],
            fg=self.style['fg'],
            bg=self.style['bg']
        ).grid(row=1, column=0, sticky="w", pady=5)
        
        tk.Label(
            info_grid,
            text=self.config['device_name'],
            font=self.style['text_font'],
            fg=self.style['fg'],
            bg=self.style['bg']
        ).grid(row=1, column=1, sticky="w", pady=5, padx=(10, 0))
        
        # 配对密钥
        tk.Label(
            info_grid,
            text="配对密钥:",
            font=self.style['text_font'],
            fg=self.style['fg'],
            bg=self.style['bg']
        ).grid(row=2, column=0, sticky="w", pady=5)
        
        self.pairing_key_var = tk.StringVar(value="等待连接...")
        self.pairing_label = tk.Label(
            info_grid,
            textvariable=self.pairing_key_var,
            font=self.style['mono_font'],
            fg=self.style['accent'],
            bg=self.style['bg']
        )
        self.pairing_label.grid(row=2, column=1, sticky="w", pady=5, padx=(10, 0))
        
        info_grid.columnconfigure(1, weight=1)
        
        # 按钮框架
        btn_frame = tk.Frame(self.root, bg=self.style['bg'])
        btn_frame.pack(pady=20)
        
        self.start_btn = tk.Button(
            btn_frame,
            text="启动服务",
            command=self.toggle_service,
            font=self.style['text_font'],
            bg=self.style['button_bg'],
            fg=self.style['button_fg'],
            activebackground=self.style['accent_light'],
            activeforeground=self.style['button_fg'],
            relief="flat",
            padx=30,
            pady=12,
            cursor="hand2"
        )
        self.start_btn.pack(side="left", padx=10)
        
        copy_btn = tk.Button(
            btn_frame,
            text="📋 复制密钥",
            command=self.copy_pairing_key,
            font=self.style['text_font'],
            bg=self.style['log_bg'],
            fg=self.style['fg'],
            activebackground=self.style['border'],
            relief="flat",
            padx=20,
            pady=12,
            cursor="hand2"
        )
        copy_btn.pack(side="left", padx=10)
        
        theme_btn = tk.Button(
            btn_frame,
            text="🌓 主题",
            command=self.toggle_theme,
            font=self.style['text_font'],
            bg=self.style['log_bg'],
            fg=self.style['fg'],
            activebackground=self.style['border'],
            relief="flat",
            padx=20,
            pady=12,
            cursor="hand2"
        )
        theme_btn.pack(side="left", padx=10)
        
        # 日志框架
        log_frame = tk.LabelFrame(
            self.root,
            text="  日志  ",
            font=self.style['small_font'],
            fg=self.style['fg'],
            bg=self.style['bg'],
            padx=10,
            pady=10
        )
        log_frame.pack(fill="both", expand=True, padx=30, pady=(0, 20))
        
        self.log_text = tk.Text(
            log_frame,
            height=8,
            wrap="word",
            font=self.style['mono_font'],
            bg=self.style['log_bg'],
            fg=self.style['fg'],
            relief="flat",
            selectbackground=self.style['accent'],
            selectforeground=self.style['button_fg']
        )
        self.log_text.pack(fill="both", expand=True)
        
        scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        scrollbar.pack(side="right", fill="y")
        self.log_text.config(yscrollcommand=scrollbar.set)
        
        # 菜单
        menubar = tk.Menu(self.root, bg=self.style['bg'], fg=self.style['fg'])
        
        file_menu = tk.Menu(menubar, tearoff=0, bg=self.style['bg'], fg=self.style['fg'])
        file_menu.add_command(label="修改设备 ID", command=self.edit_device_id)
        file_menu.add_command(label="修改服务器", command=self.edit_server)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.on_close)
        menubar.add_cascade(label="文件", menu=file_menu)
        
        help_menu = tk.Menu(menubar, tearoff=0, bg=self.style['bg'], fg=self.style['fg'])
        help_menu.add_command(label="查看文档", command=lambda: webbrowser.open("https://github.com/Royean/AgentLinker"))
        help_menu.add_command(label="关于", command=self.show_about)
        menubar.add_cascade(label="帮助", menu=help_menu)
        
        self.root.config(menu=menubar)
        
        # 窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        self.log("✅ 应用已启动")
        self.log(f"设备 ID: {self.config['device_id']}")
        self.log(f"服务器：{self.config['server_url']}")
        
        # 自动启动
        if self.config.get('auto_start', True):
            self.root.after(1000, self.start_client)
        
        # 居中窗口
        self.center_window()
        
        self.root.mainloop()
    
    def center_window(self):
        """居中窗口"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def log(self, message: str):
        """添加日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
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
        self.update_status("connecting", "连接中...")
        
        import threading
        thread = threading.Thread(target=self._run_client, daemon=True)
        thread.start()
    
    def _run_client(self):
        """运行客户端（后台线程）"""
        try:
            config = Config(str(CONFIG_FILE))
            config.data = self.config
            
            self.client = AgentClient(config)
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            connected = loop.run_until_complete(self.client.connect())
            
            if connected:
                self.running = True
                
                # 等待配对密钥
                for _ in range(30):
                    if self.client.pairing_key:
                        self.pairing_key = self.client.pairing_key
                        self.root.after(0, self._on_pairing_key_received, self.pairing_key)
                        
                        # 自动复制
                        if self.config.get('copy_on_start', True):
                            self.root.after(500, self.copy_pairing_key)
                        
                        break
                    time.sleep(1)
                
                loop.run_until_complete(self.client.handle_messages())
            else:
                self.root.after(0, self._on_connection_failed)
                
        except Exception as e:
            self.root.after(0, self._on_error, str(e))
    
    def _on_pairing_key_received(self, pairing_key: str):
        """配对密钥收到回调"""
        self.update_status("connected", "已连接")
        self.pairing_key_var.set(pairing_key)
        self.start_btn.config(text="停止服务", bg=self.style['error'])
        self.log(f"✅ 连接成功！配对密钥：{pairing_key}")
    
    def _on_connection_failed(self):
        """连接失败回调"""
        self.update_status("error", "连接失败")
        self.log("❌ 连接失败，请检查服务器地址")
    
    def _on_error(self, error: str):
        """错误回调"""
        self.update_status("error", "错误")
        self.log(f"❌ 错误：{error}")
    
    def update_status(self, status: str, text: str):
        """更新状态显示"""
        indicators = {
            "disconnected": ("⚪", self.style['fg']),
            "connecting": ("🟡", self.style['warning']),
            "connected": ("🟢", self.style['success']),
            "error": ("🔴", self.style['error'])
        }
        
        indicator, color = indicators.get(status, indicators['disconnected'])
        self.status_indicator.config(text=indicator)
        self.status_label.config(text=text, fg=color)
    
    def stop_client(self):
        """停止客户端"""
        if self.client:
            self.client.stop()
        self.running = False
        self.update_status("disconnected", "已停止")
        self.start_btn.config(text="启动服务", bg=self.style['button_bg'])
        self.log("服务已停止")
    
    def copy_pairing_key(self):
        """复制配对密钥到剪贴板"""
        if self.pairing_key:
            self.root.clipboard_clear()
            self.root.clipboard_append(self.pairing_key)
            self.root.update()  # 确保剪贴板更新
            
            self.log(f"✅ 配对密钥已复制：{self.pairing_key}")
            
            # 显示提示
            messagebox.showinfo(
                "复制成功",
                f"配对密钥 {self.pairing_key} 已复制到剪贴板",
                parent=self.root
            )
        else:
            messagebox.showwarning(
                "无密钥",
                "请先启动服务获取配对密钥",
                parent=self.root
            )
    
    def toggle_theme(self):
        """切换主题"""
        if self.dark_mode is None:
            self.dark_mode = not (ModernStyle.get_theme(None) == ModernStyle.DARK)
        else:
            self.dark_mode = not self.dark_mode
        
        self.config['dark_mode'] = self.dark_mode
        self._save_config()
        
        self.log(f"主题切换：{'深色' if self.dark_mode else '浅色'}")
        
        # 重启应用以应用新主题
        self.on_close()
        self.show_gui()
    
    def edit_device_id(self):
        """修改设备 ID"""
        dialog = tk.Toplevel(self.root)
        dialog.title("修改设备 ID")
        dialog.geometry("450x180")
        dialog.configure(bg=self.style['bg'])
        
        tk.Label(
            dialog,
            text="设备 ID:",
            font=self.style['text_font'],
            fg=self.style['fg'],
            bg=self.style['bg']
        ).pack(pady=10)
        
        entry = tk.Entry(
            dialog,
            font=self.style['mono_font'],
            width=50,
            bg=self.style['log_bg'],
            fg=self.style['fg']
        )
        entry.insert(0, self.config['device_id'])
        entry.pack(pady=5)
        
        def save():
            new_id = entry.get().strip()
            if new_id:
                self.config['device_id'] = new_id
                self.device_id_var.set(new_id)
                self._save_config()
                self.log(f"设备 ID 已修改：{new_id}")
                messagebox.showinfo("成功", "设备 ID 已保存", parent=dialog)
            dialog.destroy()
        
        tk.Button(
            dialog,
            text="保存",
            command=save,
            font=self.style['text_font'],
            bg=self.style['button_bg'],
            fg=self.style['button_fg']
        ).pack(pady=15)
    
    def edit_server(self):
        """修改服务器地址"""
        dialog = tk.Toplevel(self.root)
        dialog.title("修改服务器")
        dialog.geometry("550x180")
        dialog.configure(bg=self.style['bg'])
        
        tk.Label(
            dialog,
            text="WebSocket 服务器地址:",
            font=self.style['text_font'],
            fg=self.style['fg'],
            bg=self.style['bg']
        ).pack(pady=10)
        
        entry = tk.Entry(
            dialog,
            font=self.style['mono_font'],
            width=60,
            bg=self.style['log_bg'],
            fg=self.style['fg']
        )
        entry.insert(0, self.config['server_url'])
        entry.pack(pady=5)
        
        def save():
            new_url = entry.get().strip()
            if new_url:
                self.config['server_url'] = new_url
                self._save_config()
                self.log(f"服务器已修改：{new_url}")
                messagebox.showinfo("成功", "服务器地址已保存，重启生效", parent=dialog)
            dialog.destroy()
        
        tk.Button(
            dialog,
            text="保存",
            command=save,
            font=self.style['text_font'],
            bg=self.style['button_bg'],
            fg=self.style['button_fg']
        ).pack(pady=15)
    
    def show_about(self):
        """显示关于对话框"""
        messagebox.showinfo(
            "关于 AgentLinker",
            f"AgentLinker v{VERSION}\n\n"
            f"跨平台 AI Agent 远程控制系统\n\n"
            f"官网：https://github.com/Royean/AgentLinker\n"
            f"文档：https://github.com/Royean/AgentLinker#readme",
            parent=self.root
        )
    
    def run_cli(self):
        """命令行模式"""
        print("=" * 60)
        print(f"AgentLinker 客户端 v{VERSION}")
        print("=" * 60)
        print(f"设备 ID: {self.config['device_id']}")
        print(f"服务器：{self.config['server_url']}")
        print("=" * 60)
        self.start_client()
    
    def on_close(self):
        """关闭应用"""
        self.stop_client()
        if self.root:
            try:
                self.root.destroy()
            except:
                pass
        sys.exit(0)


def main():
    """主函数"""
    app = AgentLinkerApp()
    app.show_gui()


if __name__ == "__main__":
    main()
