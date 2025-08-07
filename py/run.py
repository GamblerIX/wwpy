#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
鸣潮服务器运行脚本

功能：
- 启动所有服务器
- 监控服务器状态
- 僵死进程检测
- 自动重启机制
- 优雅关闭
"""

import os
import sys
import subprocess
import time
import signal
import psutil
import toml
from pathlib import Path
from datetime import datetime
from threading import Thread, Event

class WuWaRun:
    """鸣潮服务器运行类"""
    
    def __init__(self, project_root):
        self.project_root = Path(project_root)
        self.wicked_waifus_path = self.project_root / "wicked-waifus-rs"
        self.logs_dir = self.project_root / "logs"
        self.release_dir = self.project_root / "release"
        
        # 确保目录存在
        self.logs_dir.mkdir(exist_ok=True)
        
        # 服务器配置
        self.servers = {
            "config-server": {
                "name": "wicked-waifus-config-server",
                "port": 8888,
                "process": None,
                "start_time": None,
                "restart_count": 0
            },
            "hotpatch-server": {
                "name": "wicked-waifus-hotpatch-server",
                "port": 8892,
                "process": None,
                "start_time": None,
                "restart_count": 0
            },
            "login-server": {
                "name": "wicked-waifus-login-server",
                "port": 8889,
                "process": None,
                "start_time": None,
                "restart_count": 0
            },
            "gateway-server": {
                "name": "wicked-waifus-gateway-server",
                "port": 8890,
                "process": None,
                "start_time": None,
                "restart_count": 0
            },
            "game-server": {
                "name": "wicked-waifus-game-server",
                "port": 8891,
                "process": None,
                "start_time": None,
                "restart_count": 0
            }
        }
        
        # 启动顺序（重要：config-server必须先启动）
        self.start_order = [
            "config-server",
            "hotpatch-server", 
            "login-server",
            "gateway-server",
            "game-server"
        ]
        
        # 控制标志
        self.shutdown_event = Event()
        self.monitor_thread = None
        
    def log_message(self, message, log_type="INFO"):
        """记录日志消息"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{log_type}] {message}"
        
        # 输出到控制台
        print(log_entry)
        
        # 写入日志文件
        log_file = self.logs_dir / "run.log"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(log_entry + "\n")
            
    def check_port_available(self, port):
        """检查端口是否可用"""
        try:
            for conn in psutil.net_connections():
                if conn.laddr.port == port and conn.status == psutil.CONN_LISTEN:
                    return False
            return True
        except (psutil.AccessDenied, AttributeError):
            # 如果无法获取网络连接信息，尝试其他方法
            import socket
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('127.0.0.1', port))
                    return True
            except OSError:
                return False
                
    def kill_process_on_port(self, port):
        """杀死占用指定端口的进程"""
        try:
            for conn in psutil.net_connections():
                if conn.laddr.port == port and conn.status == psutil.CONN_LISTEN:
                    try:
                        process = psutil.Process(conn.pid)
                        self.log_message(f"杀死占用端口{port}的进程: {process.name()} (PID: {conn.pid})")
                        process.terminate()
                        time.sleep(2)
                        if process.is_running():
                            process.kill()
                        return True
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
        except (psutil.AccessDenied, AttributeError):
            self.log_message(f"无法检查端口{port}的占用情况", "WARNING")
        return False
        
    def start_single_server(self, server_key, use_release=True):
        """启动单个服务器"""
        server = self.servers[server_key]
        server_name = server["name"]
        port = server["port"]
        
        self.log_message(f"启动 {server_name}...")
        
        # 检查端口是否被占用
        if not self.check_port_available(port):
            self.log_message(f"端口 {port} 被占用，尝试释放...", "WARNING")
            if self.kill_process_on_port(port):
                time.sleep(3)  # 等待端口释放
            else:
                self.log_message(f"无法释放端口 {port}", "ERROR")
                return False
                
        try:
            # 确定可执行文件路径
            if use_release:
                exe_path = self.release_dir / f"{server_name}.exe"
                if not exe_path.exists():
                    self.log_message(f"Release版本不存在，使用cargo run: {exe_path}", "WARNING")
                    use_release = False
            
            if use_release:
                # 使用预编译的可执行文件
                cmd = [str(exe_path)]
                cwd = str(self.wicked_waifus_path)
            else:
                # 使用cargo run
                cmd = ["cargo", "run", "-r", "--bin", server_name]
                cwd = str(self.wicked_waifus_path)
                
            self.log_message(f"执行命令: {' '.join(cmd)}")
            
            # 启动进程
            process = subprocess.Popen(
                cmd,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
            )
            
            # 等待一段时间检查进程是否正常启动
            time.sleep(3)
            
            if process.poll() is None:
                # 进程仍在运行
                server["process"] = process
                server["start_time"] = time.time()
                self.log_message(f"✅ {server_name} 启动成功 (PID: {process.pid})")
                
                # 启动日志监控线程
                log_thread = Thread(target=self._monitor_server_output, args=(server_key, process))
                log_thread.daemon = True
                log_thread.start()
                
                return True
            else:
                # 进程已退出
                return_code = process.returncode
                self.log_message(f"❌ {server_name} 启动失败 (退出码: {return_code})", "ERROR")
                return False
                
        except Exception as e:
            self.log_message(f"❌ {server_name} 启动异常: {e}", "ERROR")
            return False
            
    def _monitor_server_output(self, server_key, process):
        """监控服务器输出"""
        server_name = self.servers[server_key]["name"]
        log_file = self.logs_dir / f"{server_key}.log"
        
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                while process.poll() is None and not self.shutdown_event.is_set():
                    try:
                        output = process.stdout.readline()
                        if output:
                            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            log_entry = f"[{timestamp}] {output.strip()}"
                            f.write(log_entry + "\n")
                            f.flush()
                    except Exception:
                        break
        except Exception as e:
            self.log_message(f"监控 {server_name} 输出时发生错误: {e}", "ERROR")
            
    def stop_single_server(self, server_key):
        """停止单个服务器"""
        server = self.servers[server_key]
        server_name = server["name"]
        process = server["process"]
        
        if process is None:
            return True
            
        self.log_message(f"停止 {server_name}...")
        
        try:
            # 尝试优雅关闭
            if os.name == 'nt':
                # Windows
                process.send_signal(signal.CTRL_BREAK_EVENT)
            else:
                # Unix-like
                process.terminate()
                
            # 等待进程结束
            try:
                process.wait(timeout=10)
                self.log_message(f"✅ {server_name} 已优雅停止")
            except subprocess.TimeoutExpired:
                # 强制杀死进程
                self.log_message(f"强制停止 {server_name}...", "WARNING")
                process.kill()
                process.wait()
                self.log_message(f"✅ {server_name} 已强制停止")
                
        except Exception as e:
            self.log_message(f"停止 {server_name} 时发生错误: {e}", "ERROR")
            
        finally:
            server["process"] = None
            server["start_time"] = None
            
        return True
        
    def start_all_servers(self, use_release=True):
        """启动所有服务器"""
        self.log_message("=== 开始启动所有服务器 ===")
        
        # 检查可执行文件是否存在
        if use_release:
            missing_files = []
            for server_key in self.start_order:
                server_name = self.servers[server_key]["name"]
                exe_path = self.release_dir / f"{server_name}.exe"
                if not exe_path.exists():
                    missing_files.append(server_name)
                    
            if missing_files:
                self.log_message(f"以下可执行文件不存在: {', '.join(missing_files)}", "WARNING")
                self.log_message("将使用cargo run模式启动", "WARNING")
                use_release = False
                
        # 按顺序启动服务器
        success_count = 0
        for server_key in self.start_order:
            if self.start_single_server(server_key, use_release):
                success_count += 1
                # 等待服务器完全启动
                time.sleep(5)
            else:
                self.log_message(f"❌ 停止启动，因为 {self.servers[server_key]['name']} 启动失败", "ERROR")
                break
                
        if success_count == len(self.start_order):
            self.log_message(f"✅ 所有服务器启动完成 ({success_count}/{len(self.start_order)})")
            
            # 启动监控线程
            self.start_monitoring()
            
            self.log_message("=== 服务器启动完成 ===")
            return True
        else:
            self.log_message(f"❌ 服务器启动失败 ({success_count}/{len(self.start_order)})")
            # 停止已启动的服务器
            self.stop_all_servers()
            self.log_message("=== 服务器启动失败 ===")
            return False
            
    def stop_all_servers(self):
        """停止所有服务器"""
        self.log_message("=== 开始停止所有服务器 ===")
        
        # 设置关闭标志
        self.shutdown_event.set()
        
        # 按相反顺序停止服务器
        for server_key in reversed(self.start_order):
            self.stop_single_server(server_key)
            time.sleep(2)
            
        # 等待监控线程结束
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5)
            
        self.log_message("✅ 所有服务器已停止")
        self.log_message("=== 服务器停止完成 ===")
        
    def start_monitoring(self):
        """启动监控线程"""
        if self.monitor_thread is None or not self.monitor_thread.is_alive():
            self.monitor_thread = Thread(target=self._monitor_servers)
            self.monitor_thread.daemon = True
            self.monitor_thread.start()
            self.log_message("✅ 服务器监控已启动")
            
    def _monitor_servers(self):
        """监控服务器状态"""
        while not self.shutdown_event.is_set():
            try:
                for server_key, server in self.servers.items():
                    process = server["process"]
                    if process is not None:
                        # 检查进程是否还在运行
                        if process.poll() is not None:
                            # 进程已退出
                            return_code = process.returncode
                            self.log_message(f"⚠️  {server['name']} 意外退出 (退出码: {return_code})", "WARNING")
                            
                            # 重启服务器（最多重启3次）
                            if server["restart_count"] < 3:
                                server["restart_count"] += 1
                                self.log_message(f"尝试重启 {server['name']} (第{server['restart_count']}次)")
                                
                                # 清理进程信息
                                server["process"] = None
                                server["start_time"] = None
                                
                                # 等待一段时间后重启
                                time.sleep(10)
                                
                                if self.start_single_server(server_key):
                                    self.log_message(f"✅ {server['name']} 重启成功")
                                else:
                                    self.log_message(f"❌ {server['name']} 重启失败", "ERROR")
                            else:
                                self.log_message(f"❌ {server['name']} 重启次数过多，停止重启", "ERROR")
                                server["process"] = None
                                server["start_time"] = None
                                
                # 每30秒检查一次
                time.sleep(30)
                
            except Exception as e:
                self.log_message(f"监控线程发生错误: {e}", "ERROR")
                time.sleep(30)
                
    def get_server_status(self):
        """获取服务器状态"""
        status = {}
        for server_key, server in self.servers.items():
            process = server["process"]
            if process is not None and process.poll() is None:
                # 服务器正在运行
                uptime = time.time() - server["start_time"] if server["start_time"] else 0
                status[server_key] = {
                    "running": True,
                    "pid": process.pid,
                    "uptime": uptime,
                    "restart_count": server["restart_count"],
                    "port": server["port"]
                }
            else:
                # 服务器未运行
                status[server_key] = {
                    "running": False,
                    "pid": None,
                    "uptime": 0,
                    "restart_count": server["restart_count"],
                    "port": server["port"]
                }
        return status
        
    def wait_for_servers(self):
        """等待服务器运行"""
        try:
            while not self.shutdown_event.is_set():
                time.sleep(1)
        except KeyboardInterrupt:
            pass
            
    def restart_server(self, server_key):
        """重启指定服务器"""
        self.log_message(f"重启 {self.servers[server_key]['name']}...")
        
        # 停止服务器
        self.stop_single_server(server_key)
        time.sleep(3)
        
        # 启动服务器
        return self.start_single_server(server_key)
        
    def modify_database_config(self):
        """修改数据库配置文件"""
        self.log_message("修改数据库配置文件...")
        
        # 需要修改的配置文件
        config_files = [
            "gameserver.toml",
            "gateway.toml", 
            "loginserver.toml"
        ]
        
        # 新的数据库配置
        new_db_config = {
            "host": "localhost:5432",
            "user_name": "users",
            "password": "password",
            "db_name": "users"
        }
        
        modified_count = 0
        
        for config_file in config_files:
            config_path = self.release_dir / config_file
            
            if config_path.exists():
                try:
                    # 读取现有配置
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config_data = toml.load(f)
                    
                    # 修改数据库配置
                    if 'database' in config_data:
                        config_data['database'].update(new_db_config)
                        
                        # 写回配置文件
                        with open(config_path, 'w', encoding='utf-8') as f:
                            toml.dump(config_data, f)
                            
                        self.log_message(f"✅ 已修改 {config_file} 的数据库配置")
                        modified_count += 1
                    else:
                        self.log_message(f"⚠️  {config_file} 中未找到 [database] 配置段", "WARNING")
                        
                except Exception as e:
                    self.log_message(f"❌ 修改 {config_file} 失败: {e}", "ERROR")
            else:
                self.log_message(f"⚠️  配置文件不存在: {config_file}", "WARNING")
                
        if modified_count > 0:
            self.log_message(f"✅ 成功修改了 {modified_count} 个配置文件")
            return True
        else:
            self.log_message("❌ 没有成功修改任何配置文件", "ERROR")
            return False
            
    def start_all_servers_with_config_modification(self, use_release=True):
        """启动所有服务器并自动修改配置"""
        self.log_message("=== 开始启动服务器并配置数据库 ===")
        
        # 第一步：启动服务器生成配置文件
        self.log_message("第一步：启动服务器生成配置文件...")
        if not self.start_all_servers(use_release):
            self.log_message("❌ 服务器启动失败，无法生成配置文件", "ERROR")
            return False
            
        # 等待配置文件生成
        self.log_message("等待配置文件生成...")
        time.sleep(10)
        
        # 第二步：停止服务器
        self.log_message("第二步：停止服务器以修改配置...")
        self.stop_all_servers()
        
        # 等待服务器完全停止
        time.sleep(5)
        
        # 第三步：修改数据库配置
        self.log_message("第三步：修改数据库配置...")
        if not self.modify_database_config():
            self.log_message("❌ 配置文件修改失败", "ERROR")
            return False
            
        # 第四步：重新启动服务器
        self.log_message("第四步：重新启动服务器...")
        if self.start_all_servers(use_release):
            self.log_message("=== 服务器启动并配置完成 ===")
            return True
        else:
            self.log_message("❌ 服务器重新启动失败", "ERROR")
            return False

def main():
    """测试函数"""
    project_root = Path(__file__).parent.parent
    runner = WuWaRun(project_root)
    
    print("开始运行测试...")
    
    try:
        success = runner.start_all_servers(use_release=False)
        
        if success:
            print("所有服务器启动成功，按Ctrl+C停止")
            runner.wait_for_servers()
        else:
            print("服务器启动失败")
            
    except KeyboardInterrupt:
        print("\n正在停止服务器...")
        runner.stop_all_servers()
        print("服务器已停止")

if __name__ == "__main__":
    main()