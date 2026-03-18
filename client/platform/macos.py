"""
AgentLinker macOS 平台特定实现
"""

import platform
import subprocess
import os


def get_platform_info() -> dict:
    """获取 macOS 平台信息"""
    try:
        # 获取 macOS 版本
        result = subprocess.run(
            ["sw_vers", "-productVersion"],
            capture_output=True,
            text=True,
            timeout=5
        )
        macos_version = result.stdout.strip()
    except:
        macos_version = "Unknown"
    
    try:
        # 获取架构
        arch = platform.machine()
        if arch == "arm64":
            arch_name = "Apple Silicon (M1/M2/M3)"
        elif arch == "x86_64":
            arch_name = "Intel"
        else:
            arch_name = arch
    except:
        arch_name = "Unknown"
    
    return {
        "platform": "macOS",
        "version": macos_version,
        "architecture": arch_name,
        "hostname": platform.node()
    }


def get_system_info_extended() -> dict:
    """获取扩展系统信息（macOS 特定）"""
    info = {}
    
    # 电池状态（如果是笔记本）
    try:
        result = subprocess.run(
            ["pmset", "-g", "batt"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if "charging" in result.stdout.lower():
            info["battery_status"] = "Charging"
        elif "discharging" in result.stdout.lower():
            info["battery_status"] = "On Battery"
    except:
        pass
    
    # 电源适配器状态
    try:
        result = subprocess.run(
            ["pmset", "-g", "ps"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if "AC Power" in result.stdout:
            info["power_source"] = "AC Power"
        else:
            info["power_source"] = "Battery"
    except:
        pass
    
    return info


def list_applications() -> list:
    """列出已安装的应用程序"""
    apps = []
    app_dirs = ["/Applications", "/Applications/Utilities", os.path.expanduser("~/Applications")]
    
    for app_dir in app_dirs:
        if os.path.exists(app_dir):
            try:
                for item in os.listdir(app_dir):
                    if item.endswith(".app"):
                        apps.append({
                            "name": item,
                            "path": os.path.join(app_dir, item)
                        })
            except:
                pass
    
    return apps


def get_wifi_info() -> dict:
    """获取 WiFi 信息"""
    info = {}
    
    try:
        result = subprocess.run(
            ["/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport", "-I"],
            capture_output=True,
            text=True,
            timeout=5
        )
        for line in result.stdout.split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip()
                if key == "SSID":
                    info["ssid"] = value
                elif key == "BSSID":
                    info["bssid"] = value
                elif key == "channel":
                    info["channel"] = value
                elif key == "security":
                    info["security"] = value
    except:
        pass
    
    return info


def execute_applescript(script: str) -> dict:
    """执行 AppleScript"""
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=10
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
