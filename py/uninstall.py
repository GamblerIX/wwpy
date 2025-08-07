#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
鸣潮服务器卸载脚本

功能：
- 停止所有服务器进程
- 清理日志文件
- 清理临时文件
- 清理构建文件
- 数据库清理选项
- 完全卸载选项
"""

import os
import sys
import time
import shutil
import psutil
import subprocess
from pathlib import Path
from datetime import datetime

class WuWaUninstall:
    """鸣潮服务器卸载类"""
    
    def __init__(self, project_root):
        self.project_root = Path(project_root)
        self.logs_dir = self.project_root / "logs"
        self.temp_dir = self.project_root / "temp"
        self.release_dir = self.project_root / "release"
        self.source_dir = self.project_root / "wicked-waifus-rs"
        
        # 确保目录存在
        self.logs_dir.mkdir(exist_ok=True)
        
        # 服务器进程名称
        self.server_processes = [
            "wicked-waifus-config-server",
            "wicked-waifus-hotpatch-server", 
            "wicked-waifus-login-server",
            "wicked-waifus-gateway-server",
            "wicked-waifus-game-server"
        ]
        
        # 服务器端口
        self.server_ports = [8888, 8889, 8890, 8891, 8892]
        
    def log_message(self, message, log_type="INFO"):
        """记录日志消息"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{log_type}] {message}"
        
        # 输出到控制台
        print(log_entry)
        
        # 写入日志文件
        log_file = self.logs_dir / "uninstall.log"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(log_entry + "\n")
            
    def find_server_processes(self):
        """查找服务器进程"""
        found_processes = []
        
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    proc_info = proc.info
                    proc_name = proc_info['name'].lower()
                    cmdline = ' '.join(proc_info['cmdline']) if proc_info['cmdline'] else ''
                    
                    # 检查是否是我们的服务器进程
                    for server_name in self.server_processes:
                        if (server_name in proc_name or 
                            server_name in cmdline or
                            (proc_name.endswith('.exe') and server_name.replace('-', '_') in proc_name)):
                            
                            found_processes.append({
                                'pid': proc_info['pid'],
                                'name': proc_info['name'],
                                'cmdline': cmdline,
                                'server_name': server_name
                            })
                            break
                            
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
                    
        except Exception as e:
            self.log_message(f"查找进程时发生错误: {e}", "ERROR")
            
        return found_processes
        
    def stop_all_servers(self, force=False):
        """停止所有服务器进程"""
        self.log_message("开始停止所有服务器进程...")
        
        processes = self.find_server_processes()
        
        if not processes:
            self.log_message("未发现运行中的服务器进程")
            return True
            
        self.log_message(f"发现 {len(processes)} 个服务器进程")
        
        stopped_count = 0
        failed_processes = []
        
        for proc_info in processes:
            pid = proc_info['pid']
            name = proc_info['name']
            server_name = proc_info['server_name']
            
            try:
                proc = psutil.Process(pid)
                
                if force:
                    # 强制终止
                    self.log_message(f"强制终止进程: {server_name} (PID: {pid})")
                    proc.kill()
                else:
                    # 优雅停止
                    self.log_message(f"停止进程: {server_name} (PID: {pid})")
                    proc.terminate()
                    
                # 等待进程结束
                try:
                    proc.wait(timeout=10)
                    self.log_message(f"进程已停止: {server_name}")
                    stopped_count += 1
                except psutil.TimeoutExpired:
                    if not force:
                        # 如果优雅停止失败，尝试强制终止
                        self.log_message(f"优雅停止超时，强制终止: {server_name}")
                        proc.kill()
                        try:
                            proc.wait(timeout=5)
                            stopped_count += 1
                        except psutil.TimeoutExpired:
                            failed_processes.append(proc_info)
                    else:
                        failed_processes.append(proc_info)
                        
            except psutil.NoSuchProcess:
                self.log_message(f"进程已不存在: {server_name}")
                stopped_count += 1
            except psutil.AccessDenied:
                self.log_message(f"无权限停止进程: {server_name} (PID: {pid})", "ERROR")
                failed_processes.append(proc_info)
            except Exception as e:
                self.log_message(f"停止进程失败: {server_name} - {e}", "ERROR")
                failed_processes.append(proc_info)
                
        if failed_processes:
            self.log_message(f"有 {len(failed_processes)} 个进程停止失败", "WARNING")
            for proc_info in failed_processes:
                self.log_message(f"  - {proc_info['server_name']} (PID: {proc_info['pid']})", "WARNING")
            return False
        else:
            self.log_message(f"成功停止 {stopped_count} 个进程")
            return True
            
    def kill_port_processes(self):
        """杀死占用服务器端口的进程"""
        self.log_message("检查并清理端口占用...")
        
        killed_count = 0
        
        for port in self.server_ports:
            try:
                for conn in psutil.net_connections():
                    if conn.laddr.port == port and conn.pid:
                        try:
                            proc = psutil.Process(conn.pid)
                            proc_name = proc.name()
                            
                            self.log_message(f"终止占用端口 {port} 的进程: {proc_name} (PID: {conn.pid})")
                            proc.kill()
                            killed_count += 1
                            
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass
                            
            except (psutil.AccessDenied, AttributeError):
                # 如果无法获取网络连接信息，尝试使用netstat
                try:
                    if os.name == 'nt':  # Windows
                        result = subprocess.run(
                            ['netstat', '-ano'], 
                            capture_output=True, 
                            text=True, 
                            timeout=10
                        )
                        
                        for line in result.stdout.split('\n'):
                            if f':{port} ' in line and 'LISTENING' in line:
                                parts = line.split()
                                if len(parts) >= 5:
                                    pid = parts[-1]
                                    try:
                                        pid = int(pid)
                                        proc = psutil.Process(pid)
                                        proc_name = proc.name()
                                        
                                        self.log_message(f"终止占用端口 {port} 的进程: {proc_name} (PID: {pid})")
                                        proc.kill()
                                        killed_count += 1
                                        
                                    except (ValueError, psutil.NoSuchProcess, psutil.AccessDenied):
                                        pass
                except Exception:
                    pass
                    
        if killed_count > 0:
            self.log_message(f"清理了 {killed_count} 个端口占用进程")
        else:
            self.log_message("未发现端口占用")
            
    def clean_logs(self, keep_uninstall_log=True):
        """清理日志文件"""
        self.log_message("开始清理日志文件...")
        
        if not self.logs_dir.exists():
            self.log_message("日志目录不存在")
            return
            
        cleaned_files = []
        
        try:
            for log_file in self.logs_dir.iterdir():
                if log_file.is_file():
                    # 保留卸载日志
                    if keep_uninstall_log and log_file.name == "uninstall.log":
                        continue
                        
                    try:
                        log_file.unlink()
                        cleaned_files.append(log_file.name)
                    except Exception as e:
                        self.log_message(f"删除日志文件失败: {log_file.name} - {e}", "ERROR")
                        
            if cleaned_files:
                self.log_message(f"清理了 {len(cleaned_files)} 个日志文件")
                for filename in cleaned_files:
                    self.log_message(f"  - {filename}")
            else:
                self.log_message("没有需要清理的日志文件")
                
        except Exception as e:
            self.log_message(f"清理日志文件时发生错误: {e}", "ERROR")
            
    def clean_temp_files(self):
        """清理临时文件"""
        self.log_message("开始清理临时文件...")
        
        cleaned_dirs = []
        
        # 清理temp目录
        if self.temp_dir.exists():
            try:
                shutil.rmtree(self.temp_dir)
                self.temp_dir.mkdir(exist_ok=True)
                cleaned_dirs.append("temp")
                self.log_message("清理了temp目录")
            except Exception as e:
                self.log_message(f"清理temp目录失败: {e}", "ERROR")
                
        # 清理release目录
        if self.release_dir.exists():
            try:
                for item in self.release_dir.iterdir():
                    if item.is_file():
                        item.unlink()
                    elif item.is_dir():
                        shutil.rmtree(item)
                cleaned_dirs.append("release")
                self.log_message("清理了release目录")
            except Exception as e:
                self.log_message(f"清理release目录失败: {e}", "ERROR")
                
        # 清理源码目录中的构建文件
        if self.source_dir.exists():
            self._clean_rust_build_files()
            
        if cleaned_dirs:
            self.log_message(f"清理了 {len(cleaned_dirs)} 个目录: {', '.join(cleaned_dirs)}")
        else:
            self.log_message("没有需要清理的临时文件")
            
    def _clean_rust_build_files(self):
        """清理Rust构建文件"""
        self.log_message("清理Rust构建文件...")
        
        build_dirs = ["target", "Cargo.lock"]
        cleaned_items = []
        
        for item_name in build_dirs:
            item_path = self.source_dir / item_name
            
            if item_path.exists():
                try:
                    if item_path.is_dir():
                        shutil.rmtree(item_path)
                    else:
                        item_path.unlink()
                    cleaned_items.append(item_name)
                except Exception as e:
                    self.log_message(f"清理构建文件失败: {item_name} - {e}", "ERROR")
                    
        # 清理各个服务器目录中的target目录
        server_dirs = [
            "wicked-waifus-config-server",
            "wicked-waifus-hotpatch-server",
            "wicked-waifus-login-server", 
            "wicked-waifus-gateway-server",
            "wicked-waifus-game-server"
        ]
        
        for server_dir in server_dirs:
            server_path = self.source_dir / server_dir
            if server_path.exists():
                target_path = server_path / "target"
                if target_path.exists():
                    try:
                        shutil.rmtree(target_path)
                        cleaned_items.append(f"{server_dir}/target")
                    except Exception as e:
                        self.log_message(f"清理构建文件失败: {server_dir}/target - {e}", "ERROR")
                        
        if cleaned_items:
            self.log_message(f"清理了 {len(cleaned_items)} 个构建文件/目录")
            for item in cleaned_items:
                self.log_message(f"  - {item}")
        else:
            self.log_message("没有需要清理的构建文件")
            
    def backup_data(self, backup_dir=None):
        """备份重要数据"""
        if backup_dir is None:
            backup_dir = self.project_root / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        else:
            backup_dir = Path(backup_dir)
            
        self.log_message(f"开始备份数据到: {backup_dir}")
        
        try:
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # 备份配置文件
            config_files = [
                "config.toml",
                "database.toml", 
                "server.toml"
            ]
            
            backed_up_files = []
            
            for config_file in config_files:
                config_path = self.source_dir / config_file
                if config_path.exists():
                    try:
                        shutil.copy2(config_path, backup_dir / config_file)
                        backed_up_files.append(config_file)
                    except Exception as e:
                        self.log_message(f"备份配置文件失败: {config_file} - {e}", "ERROR")
                        
            # 备份重要日志
            important_logs = ["run.log", "build.log", "uninstall.log"]
            
            for log_file in important_logs:
                log_path = self.logs_dir / log_file
                if log_path.exists():
                    try:
                        shutil.copy2(log_path, backup_dir / log_file)
                        backed_up_files.append(log_file)
                    except Exception as e:
                        self.log_message(f"备份日志文件失败: {log_file} - {e}", "ERROR")
                        
            if backed_up_files:
                self.log_message(f"成功备份 {len(backed_up_files)} 个文件")
                for filename in backed_up_files:
                    self.log_message(f"  - {filename}")
                return backup_dir
            else:
                self.log_message("没有文件需要备份")
                return None
                
        except Exception as e:
            self.log_message(f"备份数据时发生错误: {e}", "ERROR")
            return None
            
    def show_cleanup_summary(self):
        """显示清理摘要"""
        print("\n" + "=" * 80)
        print("                        卸载清理摘要")
        print("=" * 80)
        
        # 检查进程状态
        processes = self.find_server_processes()
        print(f"\n🔍 服务器进程状态:")
        if processes:
            print(f"  ⚠️  仍有 {len(processes)} 个进程在运行:")
            for proc in processes:
                print(f"    - {proc['server_name']} (PID: {proc['pid']})")
        else:
            print("  ✅ 所有服务器进程已停止")
            
        # 检查目录状态
        print(f"\n📁 目录状态:")
        
        dirs_to_check = {
            "logs": self.logs_dir,
            "temp": self.temp_dir,
            "release": self.release_dir
        }
        
        for dir_name, dir_path in dirs_to_check.items():
            if dir_path.exists():
                file_count = len(list(dir_path.iterdir())) if dir_path.is_dir() else 0
                if file_count == 0:
                    print(f"  ✅ {dir_name} 目录: 已清空")
                else:
                    print(f"  📄 {dir_name} 目录: {file_count} 个文件")
            else:
                print(f"  ❌ {dir_name} 目录: 不存在")
                
        # 检查构建文件
        if self.source_dir.exists():
            target_dir = self.source_dir / "target"
            if target_dir.exists():
                print(f"  📦 构建文件: 仍存在")
            else:
                print(f"  ✅ 构建文件: 已清理")
        else:
            print(f"  ❌ 源码目录: 不存在")
            
        print("\n" + "=" * 80)
        
    def interactive_uninstall(self):
        """交互式卸载"""
        print("\n" + "=" * 80)
        print("                        鸣潮服务器卸载向导")
        print("=" * 80)
        
        print("\n⚠️  警告: 此操作将清理服务器相关文件和进程")
        print("请选择要执行的操作:")
        print("\n1. 停止服务器进程")
        print("2. 清理日志文件")
        print("3. 清理临时文件")
        print("4. 清理构建文件")
        print("5. 备份重要数据")
        print("6. 完全卸载 (执行所有清理操作)")
        print("7. 显示当前状态")
        print("0. 退出")
        
        while True:
            try:
                choice = input("\n请选择操作 (0-7): ").strip()
                
                if choice == "0":
                    print("\n退出卸载向导")
                    break
                elif choice == "1":
                    self.stop_all_servers()
                    self.kill_port_processes()
                elif choice == "2":
                    confirm = input("确认清理所有日志文件? (y/N): ").strip().lower()
                    if confirm == 'y':
                        self.clean_logs()
                elif choice == "3":
                    confirm = input("确认清理临时文件? (y/N): ").strip().lower()
                    if confirm == 'y':
                        self.clean_temp_files()
                elif choice == "4":
                    confirm = input("确认清理构建文件? (y/N): ").strip().lower()
                    if confirm == 'y':
                        self._clean_rust_build_files()
                elif choice == "5":
                    backup_path = input("输入备份目录路径 (留空使用默认): ").strip()
                    if not backup_path:
                        backup_path = None
                    self.backup_data(backup_path)
                elif choice == "6":
                    print("\n⚠️  完全卸载将执行以下操作:")
                    print("  - 停止所有服务器进程")
                    print("  - 清理端口占用")
                    print("  - 清理日志文件")
                    print("  - 清理临时文件")
                    print("  - 清理构建文件")
                    
                    confirm = input("\n确认执行完全卸载? (y/N): ").strip().lower()
                    if confirm == 'y':
                        # 先备份
                        backup_confirm = input("是否先备份重要数据? (Y/n): ").strip().lower()
                        if backup_confirm != 'n':
                            self.backup_data()
                            
                        # 执行卸载
                        self.stop_all_servers(force=True)
                        self.kill_port_processes()
                        self.clean_logs()
                        self.clean_temp_files()
                        
                        print("\n✅ 完全卸载完成")
                        self.show_cleanup_summary()
                        break
                elif choice == "7":
                    self.show_cleanup_summary()
                else:
                    print("无效选择，请重新输入")
                    
            except KeyboardInterrupt:
                print("\n\n操作已取消")
                break
            except Exception as e:
                print(f"\n操作失败: {e}")
                
    def quick_uninstall(self, backup=True):
        """快速卸载"""
        self.log_message("开始快速卸载...")
        
        try:
            # 备份数据
            if backup:
                self.backup_data()
                
            # 停止进程
            self.stop_all_servers(force=True)
            self.kill_port_processes()
            
            # 清理文件
            self.clean_logs()
            self.clean_temp_files()
            
            self.log_message("快速卸载完成")
            return True
            
        except Exception as e:
            self.log_message(f"快速卸载失败: {e}", "ERROR")
            return False

def main():
    """主函数"""
    project_root = Path(__file__).parent.parent
    uninstaller = WuWaUninstall(project_root)
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--quick":
            # 快速卸载
            uninstaller.quick_uninstall()
        elif sys.argv[1] == "--stop":
            # 仅停止服务器
            uninstaller.stop_all_servers()
        elif sys.argv[1] == "--clean":
            # 仅清理文件
            uninstaller.clean_logs()
            uninstaller.clean_temp_files()
        else:
            print("用法: python uninstall.py [--quick|--stop|--clean]")
    else:
        # 交互式卸载
        uninstaller.interactive_uninstall()

if __name__ == "__main__":
    main()