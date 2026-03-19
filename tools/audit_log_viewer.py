#!/usr/bin/env python3
"""
AgentLinker 审计日志查看工具
用于查看和分析操作审计日志
"""

import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict

AUDIT_LOG_FILE = "/var/log/agentlinker/audit.log"


def load_logs(limit: int = 100) -> List[Dict]:
    """加载审计日志"""
    log_path = Path(AUDIT_LOG_FILE)
    if not log_path.exists():
        print(f"日志文件不存在：{AUDIT_LOG_FILE}")
        return []
    
    logs = []
    with open(log_path, "r") as f:
        for line in f:
            try:
                logs.append(json.loads(line.strip()))
            except:
                continue
            
            if len(logs) >= limit:
                break
    
    return logs


def format_log(log: Dict) -> str:
    """格式化日志条目"""
    timestamp = log.get("timestamp", "")[:19]
    action = log.get("action", "")
    actor_type = log.get("actor_type", "")
    actor_id = log.get("actor_id", "")
    result = log.get("result", "")
    
    result_icon = "✅" if result == "success" else "❌"
    
    line = f"{timestamp} | {result_icon} {action:20} | {actor_type:10} | {actor_id:30}"
    
    # 添加目标信息
    target_type = log.get("target_type")
    target_id = log.get("target_id")
    if target_type and target_id:
        line += f" -> {target_type}({target_id})"
    
    return line


def filter_logs(logs: List[Dict], actor_id: str = None, action: str = None, 
                result: str = None, start_time: str = None) -> List[Dict]:
    """过滤日志"""
    filtered = logs
    
    if actor_id:
        filtered = [l for l in filtered if l.get("actor_id") == actor_id]
    
    if action:
        filtered = [l for l in filtered if l.get("action") == action]
    
    if result:
        filtered = [l for l in filtered if l.get("result") == result]
    
    if start_time:
        filtered = [l for l in filtered if l.get("timestamp", "") >= start_time]
    
    return filtered


def show_statistics(logs: List[Dict]):
    """显示统计信息"""
    total = len(logs)
    success = sum(1 for l in logs if l.get("result") == "success")
    failure = total - success
    
    # 按动作统计
    action_count = {}
    for log in logs:
        action = log.get("action", "unknown")
        action_count[action] = action_count.get(action, 0) + 1
    
    # 按角色统计
    actor_count = {}
    for log in logs:
        actor = log.get("actor_id", "unknown")
        actor_count[actor] = actor_count.get(actor, 0) + 1
    
    print("\n📊 统计信息")
    print("=" * 80)
    print(f"总记录数：{total}")
    print(f"成功：{success} ({success/total*100:.1f}%)")
    print(f"失败：{failure} ({failure/total*100:.1f}%)")
    print()
    
    print("按动作统计:")
    for action, count in sorted(action_count.items(), key=lambda x: -x[1])[:10]:
        print(f"  {action:25} {count:5} ({count/total*100:5.1f}%)")
    print()
    
    print("按设备/控制器统计:")
    for actor, count in sorted(actor_count.items(), key=lambda x: -x[1])[:10]:
        print(f"  {actor:30} {count:5} ({count/total*100:5.1f}%)")
    print("=" * 80)


def export_logs(logs: List[Dict], output_file: str, format: str = "json"):
    """导出日志"""
    if format == "json":
        with open(output_file, "w") as f:
            json.dump(logs, f, indent=2)
    
    elif format == "csv":
        import csv
        with open(output_file, "w", newline="") as f:
            if logs:
                writer = csv.DictWriter(f, fieldnames=logs[0].keys())
                writer.writeheader()
                writer.writerows(logs)
    
    print(f"✅ 已导出 {len(logs)} 条记录到 {output_file}")


def main():
    parser = argparse.ArgumentParser(description="AgentLinker 审计日志查看工具")
    
    parser.add_argument("-l", "--limit", type=int, default=100,
                       help="显示记录数 (默认：100)")
    parser.add_argument("--actor", type=str,
                       help="按设备/控制器 ID 过滤")
    parser.add_argument("--action", type=str,
                       help="按动作类型过滤")
    parser.add_argument("--success", action="store_true",
                       help="只显示成功记录")
    parser.add_argument("--failure", action="store_true",
                       help="只显示失败记录")
    parser.add_argument("--stats", action="store_true",
                       help="显示统计信息")
    parser.add_argument("-o", "--output", type=str,
                       help="导出到文件")
    parser.add_argument("--format", choices=["json", "csv"], default="json",
                       help="导出格式 (默认：json)")
    parser.add_argument("--follow", "-f", action="store_true",
                       help="跟踪日志（类似 tail -f）")
    
    args = parser.parse_args()
    
    # 加载日志
    logs = load_logs(limit=args.limit * 2)  # 多加载一些用于过滤
    
    # 过滤
    result_filter = None
    if args.success:
        result_filter = "success"
    elif args.failure:
        result_filter = "failure"
    
    logs = filter_logs(
        logs,
        actor_id=args.actor,
        action=args.action,
        result=result_filter
    )
    
    # 限制数量
    logs = logs[:args.limit]
    
    # 显示
    if args.stats:
        show_statistics(logs)
    else:
        print(f"\n📋 审计日志 (显示 {len(logs)} 条)\n")
        print("=" * 100)
        for log in logs:
            print(format_log(log))
        print("=" * 100)
    
    # 导出
    if args.output:
        export_logs(logs, args.output, args.format)


if __name__ == "__main__":
    main()
