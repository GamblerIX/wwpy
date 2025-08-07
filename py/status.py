#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
鸣潮服务器状态监控脚本

功能：
- 检查服务器运行状态
- 端口占用检查
- 系统资源监控
- 进程健康检查
- 实时状态显示
"""

import os
import sys
import time
import psutil
import socket
from pathlib import Path
from datetime import datetime, timedelta
from threading import Thread, Event

class WuWaStatus:
    """鸣潮服务器状态监控类"""
    
    def __init__(self, project_root):
        self.project_root = Path(project_root)
        self.logs_dir = self.project_root / "logs"
        
        # 确保目录存在
        self.logs_dir.mkdir(exist_ok=True)
        
        # 服务器配置
        self.servers = {
            "config-server": {
                "name": "wicked-waifus-config-server",
                "port": 8888,
                "description": "配置服务器"
            },
            "hotpatch-server": {
                "name": "wicked-waifus-hotpatch-server",
                "port": 8892,
                "description": "热更新服务器"
            },
            "login-server": {
                "name": "wicked-waifus-login-server",
                "port": 8889,
                "description": "登录服务器"
            },
            "gateway-server": {
                "name": "wicked-waifus-gateway-server",
                "port": 8890,
                "description": "网关服务器"
            },
            "game-server": {
                "name": "wicked-waifus-game-server",
                "port": 8891,
                "description": "游戏服务器"
            }
        }
        
        # 监控标志
        self.monitoring = False
        self.monitor_event = Event()
        
    def log_message(self, message, log_type="INFO"):
        """记录日志消息"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{log_type}] {message}"
        
        # 输出到控制台
        print(log_entry)
        
        # 写入日志文件
        log_file = self.logs_dir / "status.log"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(log_entry + "\n")
            
    def check_port_status(self, port):
        """检查端口状态"""
        try:
            # 检查端口是否被监听
            for conn in psutil.net_connections():
                if conn.laddr.port == port and conn.status == psutil.CONN_LISTEN:
                    return {
                        "listening": True,
                        "pid": conn.pid,
                        "address": f"{conn.laddr.ip}:{conn.laddr.port}"
                    }
        except (psutil.AccessDenied, AttributeError):
            # 如果无法获取网络连接信息，尝试socket连接
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(1)
                    result = s.connect_ex(('127.0.0.1', port))
                    if result == 0:
                        return {
                            "listening": True,
                            "pid": None,
                            "address": f"127.0.0.1:{port}"
                        }
            except Exception:
                pass
                
        return {
            "listening": False,
            "pid": None,
            "address": None
        }
        
    def find_server_processes(self):
        """查找服务器进程"""
        processes = {}
        
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time', 'cpu_percent', 'memory_info']):
                try:
                    proc_info = proc.info
                    proc_name = proc_info['name'].lower()
                    cmdline = ' '.join(proc_info['cmdline']) if proc_info['cmdline'] else ''
                    
                    # 检查是否是我们的服务器进程
                    for server_key, server in self.servers.items():
                        server_name = server['name']
                        
                        if (server_name in proc_name or 
                            server_name in cmdline or
                            (proc_name.endswith('.exe') and server_name.replace('-', '_') in proc_name)):
                            
                            # 获取进程详细信息
                            create_time = datetime.fromtimestamp(proc_info['create_time'])
                            uptime = datetime.now() - create_time
                            
                            # 获取CPU和内存使用率
                            try:
                                cpu_percent = proc.cpu_percent()
                                memory_info = proc_info['memory_info']
                                memory_mb = memory_info.rss / 1024 / 1024
                            except (psutil.NoSuchProcess, psutil.AccessDenied):
                                cpu_percent = 0
                                memory_mb = 0
                                
                            processes[server_key] = {
                                "pid": proc_info['pid'],
                                "name": proc_info['name'],
                                "cmdline": cmdline,
                                "create_time": create_time,
                                "uptime": uptime,
                                "cpu_percent": cpu_percent,
                                "memory_mb": memory_mb,
                                "status": "running"
                            }
                            break
                            
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
                    
        except Exception as e:
            self.log_message(f"查找进程时发生错误: {e}", "ERROR")
            
        return processes
        
    def get_system_info(self):
        """获取系统信息"""
        try:
            # CPU信息
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # 内存信息
            memory = psutil.virtual_memory()
            memory_total_gb = memory.total / 1024 / 1024 / 1024
            memory_used_gb = memory.used / 1024 / 1024 / 1024
            memory_percent = memory.percent
            
            # 磁盘信息
            disk = psutil.disk_usage(str(self.project_root))
            disk_total_gb = disk.total / 1024 / 1024 / 1024
            disk_used_gb = disk.used / 1024 / 1024 / 1024
            disk_percent = (disk.used / disk.total) * 100
            
            return {
                "cpu": {
                    "percent": cpu_percent,
                    "count": cpu_count
                },
                "memory": {
                    "total_gb": memory_total_gb,
                    "used_gb": memory_used_gb,
                    "percent": memory_percent
                },
                "disk": {
                    "total_gb": disk_total_gb,
                    "used_gb": disk_used_gb,
                    "percent": disk_percent
                }
            }
        except Exception as e:
            self.log_message(f"获取系统信息时发生错误: {e}", "ERROR")
            return None
            
    def format_uptime(self, uptime):
        """格式化运行时间"""
        if isinstance(uptime, timedelta):
            total_seconds = int(uptime.total_seconds())
        else:
            total_seconds = int(uptime)
            
        days = total_seconds // 86400
        hours = (total_seconds % 86400) // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        if days > 0:
            return f"{days}天 {hours}小时 {minutes}分钟"
        elif hours > 0:
            return f"{hours}小时 {minutes}分钟"
        elif minutes > 0:
            return f"{minutes}分钟 {seconds}秒"
        else:
            return f"{seconds}秒"
            
    def show_status(self, detailed=True):
        """显示服务器状态"""
        print("\n" + "=" * 80)
        print("                        鸣潮服务器状态监控")
        print("=" * 80)
        
        # 获取当前时间
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"检查时间: {current_time}")
        
        # 获取进程信息
        processes = self.find_server_processes()
        
        # 显示服务器状态
        print("\n📊 服务器状态:")
        print("-" * 80)
        
        running_count = 0
        for server_key, server in self.servers.items():
            port = server['port']
            description = server['description']
            
            # 检查端口状态
            port_status = self.check_port_status(port)
            
            # 检查进程状态
            if server_key in processes:
                proc_info = processes[server_key]
                status = "🟢 运行中"
                running_count += 1
                
                if detailed:
                    print(f"\n{description} (端口 {port}):")
                    print(f"  状态: {status}")
                    print(f"  进程ID: {proc_info['pid']}")
                    print(f"  运行时间: {self.format_uptime(proc_info['uptime'])}")
                    print(f"  CPU使用率: {proc_info['cpu_percent']:.1f}%")
                    print(f"  内存使用: {proc_info['memory_mb']:.1f} MB")
                    if port_status['listening']:
                        print(f"  监听地址: {port_status['address']}")
                else:
                    print(f"{description:15} | 端口 {port:4} | {status} | PID {proc_info['pid']:6} | {self.format_uptime(proc_info['uptime'])}")
            else:
                status = "🔴 未运行"
                if detailed:
                    print(f"\n{description} (端口 {port}):")
                    print(f"  状态: {status}")
                    if port_status['listening']:
                        print(f"  ⚠️  端口被其他进程占用: PID {port_status['pid']}")
                else:
                    print(f"{description:15} | 端口 {port:4} | {status} | {'':12} | {'':10}")
                    
        print(f"\n📈 总计: {running_count}/{len(self.servers)} 个服务器正在运行")
        
        # 显示系统信息
        if detailed:
            system_info = self.get_system_info()
            if system_info:
                print("\n💻 系统资源:")
                print("-" * 40)
                print(f"CPU使用率: {system_info['cpu']['percent']:.1f}% ({system_info['cpu']['count']} 核心)")
                print(f"内存使用: {system_info['memory']['used_gb']:.1f}GB / {system_info['memory']['total_gb']:.1f}GB ({system_info['memory']['percent']:.1f}%)")
                print(f"磁盘使用: {system_info['disk']['used_gb']:.1f}GB / {system_info['disk']['total_gb']:.1f}GB ({system_info['disk']['percent']:.1f}%)")
                
        # 显示日志文件信息
        if detailed:
            self.show_log_files_info()
            
        print("\n" + "=" * 80)
        
    def show_log_files_info(self):
        """显示日志文件信息"""
        print("\n📝 日志文件:")
        print("-" * 40)
        
        log_files = [
            "build.log",
            "run.log", 
            "status.log",
            "config-server.log",
            "hotpatch-server.log",
            "login-server.log",
            "gateway-server.log",
            "game-server.log"
        ]
        
        for log_file in log_files:
            log_path = self.logs_dir / log_file
            if log_path.exists():
                stat = log_path.stat()
                size_mb = stat.st_size / 1024 / 1024
                mtime = datetime.fromtimestamp(stat.st_mtime)
                print(f"  {log_file:20} | {size_mb:6.1f} MB | {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                print(f"  {log_file:20} | {'不存在':>6} | {'':19}")
                
    def monitor_continuously(self, interval=30):
        """持续监控模式"""
        self.monitoring = True
        self.monitor_event.clear()
        
        print(f"\n开始持续监控模式 (每{interval}秒刷新一次)")
        print("按 Ctrl+C 停止监控\n")
        
        try:
            while self.monitoring:
                # 清屏
                os.system('cls' if os.name == 'nt' else 'clear')
                
                # 显示状态
                self.show_status(detailed=False)
                
                # 等待指定时间或停止信号
                if self.monitor_event.wait(timeout=interval):
                    break
                    
        except KeyboardInterrupt:
            pass
        finally:
            self.monitoring = False
            print("\n监控已停止")
            
    def stop_monitoring(self):
        """停止监控"""
        self.monitoring = False
        self.monitor_event.set()
        
    def check_server_health(self):
        """检查服务器健康状态"""
        health_report = {
            "timestamp": datetime.now(),
            "servers": {},
            "system": {},
            "issues": []
        }
        
        # 检查服务器进程
        processes = self.find_server_processes()
        
        for server_key, server in self.servers.items():
            port = server['port']
            server_name = server['name']
            
            # 检查端口
            port_status = self.check_port_status(port)
            
            # 检查进程
            if server_key in processes:
                proc_info = processes[server_key]
                
                # 检查CPU使用率
                if proc_info['cpu_percent'] > 80:
                    health_report['issues'].append(f"{server_name} CPU使用率过高: {proc_info['cpu_percent']:.1f}%")
                    
                # 检查内存使用
                if proc_info['memory_mb'] > 1000:  # 超过1GB
                    health_report['issues'].append(f"{server_name} 内存使用过高: {proc_info['memory_mb']:.1f} MB")
                    
                health_report['servers'][server_key] = {
                    "status": "running",
                    "port_listening": port_status['listening'],
                    "cpu_percent": proc_info['cpu_percent'],
                    "memory_mb": proc_info['memory_mb'],
                    "uptime": proc_info['uptime']
                }
            else:
                health_report['servers'][server_key] = {
                    "status": "not_running",
                    "port_listening": port_status['listening']
                }
                health_report['issues'].append(f"{server_name} 未运行")
                
        # 检查系统资源
        system_info = self.get_system_info()
        if system_info:
            health_report['system'] = system_info
            
            # 检查系统资源使用
            if system_info['cpu']['percent'] > 80:
                health_report['issues'].append(f"系统CPU使用率过高: {system_info['cpu']['percent']:.1f}%")
                
            if system_info['memory']['percent'] > 80:
                health_report['issues'].append(f"系统内存使用率过高: {system_info['memory']['percent']:.1f}%")
                
            if system_info['disk']['percent'] > 90:
                health_report['issues'].append(f"磁盘空间不足: {system_info['disk']['percent']:.1f}%")
                
        return health_report
        
    def generate_status_report(self):
        """生成状态报告"""
        report = self.check_server_health()
        
        report_file = self.logs_dir / f"status_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        with open(report_file, "w", encoding="utf-8") as f:
            f.write("鸣潮服务器状态报告\n")
            f.write("=" * 50 + "\n")
            f.write(f"生成时间: {report['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # 服务器状态
            f.write("服务器状态:\n")
            f.write("-" * 30 + "\n")
            for server_key, status in report['servers'].items():
                server_name = self.servers[server_key]['name']
                f.write(f"{server_name}: {status['status']}\n")
                if status['status'] == 'running':
                    f.write(f"  CPU: {status['cpu_percent']:.1f}%\n")
                    f.write(f"  内存: {status['memory_mb']:.1f} MB\n")
                    f.write(f"  运行时间: {self.format_uptime(status['uptime'])}\n")
                f.write("\n")
                
            # 系统资源
            if 'cpu' in report['system']:
                f.write("系统资源:\n")
                f.write("-" * 30 + "\n")
                f.write(f"CPU: {report['system']['cpu']['percent']:.1f}%\n")
                f.write(f"内存: {report['system']['memory']['percent']:.1f}%\n")
                f.write(f"磁盘: {report['system']['disk']['percent']:.1f}%\n\n")
                
            # 问题列表
            if report['issues']:
                f.write("发现的问题:\n")
                f.write("-" * 30 + "\n")
                for issue in report['issues']:
                    f.write(f"- {issue}\n")
            else:
                f.write("未发现问题\n")
                
        self.log_message(f"状态报告已生成: {report_file}")
        return report_file

def main():
    """测试函数"""
    project_root = Path(__file__).parent.parent
    status_checker = WuWaStatus(project_root)
    
    print("服务器状态检查测试...")
    
    # 显示状态
    status_checker.show_status()
    
    # 生成报告
    report_file = status_checker.generate_status_report()
    print(f"\n报告已生成: {report_file}")

if __name__ == "__main__":
    main()