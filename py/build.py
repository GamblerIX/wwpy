#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
鸣潮服务器构建脚本

功能：
- 环境检查（Rust、Protoc、PgSQL）
- 编译Rust服务端
- 断点续编支持
- 自动重试机制
- 智能资源监控
"""

import os
import sys
import subprocess
import time
import shutil
import psutil
from pathlib import Path
from datetime import datetime

class WuWaBuild:
    """鸣潮服务器构建类"""
    
    def __init__(self, project_root):
        self.project_root = Path(project_root)
        self.wicked_waifus_path = self.project_root / "wicked-waifus-rs"
        self.logs_dir = self.project_root / "logs"
        self.release_dir = self.project_root / "release"
        self.temp_dir = self.project_root / "temp"
        
        # 确保目录存在
        self.logs_dir.mkdir(exist_ok=True)
        self.release_dir.mkdir(exist_ok=True)
        self.temp_dir.mkdir(exist_ok=True)
        
        # 服务器列表
        self.servers = [
            "wicked-waifus-config-server",
            "wicked-waifus-hotpatch-server", 
            "wicked-waifus-login-server",
            "wicked-waifus-gateway-server",
            "wicked-waifus-game-server"
        ]
        
    def log_message(self, message, log_type="INFO"):
        """记录日志消息"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{log_type}] {message}"
        
        # 输出到控制台
        print(log_entry)
        
        # 写入日志文件
        log_file = self.logs_dir / "build.log"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(log_entry + "\n")
            
    def check_command_exists(self, command):
        """检查命令是否存在"""
        try:
            result = subprocess.run([command, "--version"], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=10)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            return False
            
    def check_rust_environment(self):
        """检查Rust环境"""
        self.log_message("检查Rust环境...")
        
        # 检查cargo
        if not self.check_command_exists("cargo"):
            self.log_message("❌ Cargo未安装或不在PATH中", "ERROR")
            self.log_message("请安装Rust: https://www.rust-lang.org/tools/install", "ERROR")
            return False
            
        # 检查rustc
        if not self.check_command_exists("rustc"):
            self.log_message("❌ Rustc未安装或不在PATH中", "ERROR")
            return False
            
        # 获取Rust版本信息
        try:
            result = subprocess.run(["cargo", "--version"], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=10)
            if result.returncode == 0:
                self.log_message(f"✅ {result.stdout.strip()}")
            
            result = subprocess.run(["rustc", "--version"], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=10)
            if result.returncode == 0:
                self.log_message(f"✅ {result.stdout.strip()}")
                
        except subprocess.TimeoutExpired:
            self.log_message("⚠️  获取Rust版本信息超时", "WARNING")
            
        return True
        
    def check_protoc_environment(self):
        """检查Protoc环境"""
        self.log_message("检查Protoc环境...")
        
        if not self.check_command_exists("protoc"):
            self.log_message("❌ Protoc未安装或不在PATH中", "ERROR")
            self.log_message("请下载并安装Protoc: https://github.com/protocolbuffers/protobuf/releases", "ERROR")
            return False
            
        # 获取Protoc版本信息
        try:
            result = subprocess.run(["protoc", "--version"], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=10)
            if result.returncode == 0:
                self.log_message(f"✅ {result.stdout.strip()}")
        except subprocess.TimeoutExpired:
            self.log_message("⚠️  获取Protoc版本信息超时", "WARNING")
            
        return True
        
    def check_postgresql_environment(self):
        """检查PostgreSQL环境"""
        self.log_message("检查PostgreSQL环境...")
        
        # 检查psql命令
        if self.check_command_exists("psql"):
            try:
                result = subprocess.run(["psql", "--version"], 
                                      capture_output=True, 
                                      text=True, 
                                      timeout=10)
                if result.returncode == 0:
                    version_output = result.stdout.strip()
                    self.log_message(f"✅ {version_output}")
                    
                    # 检查版本是否满足要求 (PostgreSQL 12+)
                    import re
                    version_match = re.search(r'PostgreSQL (\d+)\.(\d+)', version_output)
                    if version_match:
                        major_version = int(version_match.group(1))
                        if major_version >= 12:
                            self.log_message(f"✅ PostgreSQL版本满足要求 (需要12+)")
                        else:
                            self.log_message(f"⚠️  PostgreSQL版本过低: {major_version} (建议12+)", "WARNING")
                    else:
                        self.log_message("⚠️  无法解析PostgreSQL版本信息", "WARNING")
            except subprocess.TimeoutExpired:
                self.log_message("⚠️  获取PostgreSQL版本信息超时", "WARNING")
        else:
            self.log_message("⚠️  PostgreSQL命令行工具未找到，但可能已安装", "WARNING")
            
        # 检查PostgreSQL服务是否运行
        postgres_running = False
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if 'postgres' in proc.info['name'].lower():
                    postgres_running = True
                    break
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
                
        if postgres_running:
            self.log_message("✅ PostgreSQL服务正在运行")
        else:
            self.log_message("⚠️  PostgreSQL服务未运行，请确保数据库已启动", "WARNING")
            
        return True
        
    def check_git_environment(self):
        """检查Git环境"""
        self.log_message("检查Git环境...")
        
        if not self.check_command_exists("git"):
            self.log_message("❌ Git未安装或不在PATH中", "ERROR")
            self.log_message("请安装Git: https://git-scm.com/download/win", "ERROR")
            return False
            
        # 获取Git版本信息
        try:
            result = subprocess.run(["git", "--version"], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=10)
            if result.returncode == 0:
                self.log_message(f"✅ {result.stdout.strip()}")
        except subprocess.TimeoutExpired:
            self.log_message("⚠️  获取Git版本信息超时", "WARNING")
            
        return True
        
    def check_system_resources(self):
        """检查系统资源"""
        self.log_message("检查系统资源...")
        
        # 检查CPU核心数
        cpu_count = psutil.cpu_count()
        if cpu_count >= 2:
            self.log_message(f"✅ CPU核心数: {cpu_count}核")
        else:
            self.log_message(f"⚠️  CPU核心数不足: {cpu_count}核 (建议2核+)", "WARNING")
        
        # 检查内存
        memory = psutil.virtual_memory()
        memory_gb = memory.total / (1024**3)
        
        if memory_gb >= 4:
            self.log_message(f"✅ 系统内存: {memory_gb:.1f}GB (可用: {memory.available / (1024**3):.1f}GB)")
        else:
            self.log_message(f"⚠️  系统内存不足: {memory_gb:.1f}GB (建议4GB+)", "WARNING")
            
        # 检查磁盘空间
        disk = psutil.disk_usage(str(self.project_root))
        disk_gb = disk.free / (1024**3)
        
        if disk_gb >= 10:
            self.log_message(f"✅ 可用磁盘空间: {disk_gb:.1f}GB")
        else:
            self.log_message(f"⚠️  磁盘空间不足: {disk_gb:.1f}GB (建议10GB+)", "WARNING")
            
        return True
        
    def check_source_code(self):
        """检查源码目录"""
        self.log_message("检查源码目录...")
        
        if not self.wicked_waifus_path.exists():
            self.log_message("❌ wicked-waifus-rs源码目录不存在", "ERROR")
            self.log_message("请确保已克隆源码到正确位置", "ERROR")
            return False
            
        # 检查Cargo.toml文件
        cargo_toml = self.wicked_waifus_path / "Cargo.toml"
        if not cargo_toml.exists():
            self.log_message("❌ Cargo.toml文件不存在", "ERROR")
            return False
            
        self.log_message("✅ 源码目录检查通过")
        return True
        
    def check_all_requirements(self):
        """检查所有环境要求"""
        self.log_message("=== 开始环境检查 ===")
        
        checks = [
            self.check_rust_environment,
            self.check_protoc_environment,
            self.check_postgresql_environment,
            self.check_git_environment,
            self.check_system_resources,
            self.check_source_code
        ]
        
        all_passed = True
        for check in checks:
            if not check():
                all_passed = False
                
        if all_passed:
            self.log_message("✅ 所有环境检查通过")
        else:
            self.log_message("❌ 部分环境检查失败，请解决后重试", "ERROR")
            
        self.log_message("=== 环境检查完成 ===")
        return all_passed
        
    def build_single_server(self, server_name, retry_count=3):
        """构建单个服务器"""
        self.log_message(f"开始构建 {server_name}...")
        
        for attempt in range(retry_count):
            try:
                # 构建命令
                cmd = ["cargo", "build", "-r", "--bin", server_name]
                
                self.log_message(f"执行命令: {' '.join(cmd)} (尝试 {attempt + 1}/{retry_count})")
                
                # 执行构建
                process = subprocess.Popen(
                    cmd,
                    cwd=str(self.wicked_waifus_path),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    universal_newlines=True
                )
                
                # 实时输出构建日志
                while True:
                    output = process.stdout.readline()
                    if output == '' and process.poll() is not None:
                        break
                    if output:
                        self.log_message(f"[{server_name}] {output.strip()}")
                        
                # 等待进程完成
                return_code = process.wait()
                
                if return_code == 0:
                    self.log_message(f"✅ {server_name} 构建成功")
                    
                    # 复制可执行文件到release目录
                    exe_name = f"{server_name}.exe"
                    source_path = self.wicked_waifus_path / "target" / "release" / exe_name
                    target_path = self.release_dir / exe_name
                    
                    if source_path.exists():
                        shutil.copy2(source_path, target_path)
                        self.log_message(f"✅ {exe_name} 已复制到release目录")
                    else:
                        self.log_message(f"⚠️  {exe_name} 文件未找到", "WARNING")
                        
                    return True
                else:
                    self.log_message(f"❌ {server_name} 构建失败 (退出码: {return_code})", "ERROR")
                    
            except subprocess.TimeoutExpired:
                self.log_message(f"❌ {server_name} 构建超时", "ERROR")
                process.kill()
            except Exception as e:
                self.log_message(f"❌ {server_name} 构建异常: {e}", "ERROR")
                
            if attempt < retry_count - 1:
                self.log_message(f"等待5秒后重试...")
                time.sleep(5)
                
        self.log_message(f"❌ {server_name} 构建失败，已达到最大重试次数", "ERROR")
        return False
        
    def build_servers(self):
        """构建所有服务器"""
        self.log_message("=== 开始构建服务器 ===")
        
        # 环境检查
        if not self.check_all_requirements():
            return False
            
        # 记录开始时间
        start_time = time.time()
        
        # 构建所有服务器
        success_count = 0
        for server in self.servers:
            if self.build_single_server(server):
                success_count += 1
            else:
                self.log_message(f"❌ 停止构建，因为 {server} 构建失败", "ERROR")
                break
                
        # 记录结束时间
        end_time = time.time()
        build_time = end_time - start_time
        
        if success_count == len(self.servers):
            self.log_message(f"✅ 所有服务器构建完成 ({success_count}/{len(self.servers)})")
            self.log_message(f"✅ 总构建时间: {build_time:.1f}秒")
            self.log_message("=== 构建完成 ===")
            return True
        else:
            self.log_message(f"❌ 构建失败 ({success_count}/{len(self.servers)})")
            self.log_message(f"❌ 构建时间: {build_time:.1f}秒")
            self.log_message("=== 构建失败 ===")
            return False
            
    def clean_build(self):
        """清理构建文件"""
        self.log_message("清理构建文件...")
        
        try:
            # 清理target目录
            target_dir = self.wicked_waifus_path / "target"
            if target_dir.exists():
                shutil.rmtree(target_dir)
                self.log_message("✅ target目录已清理")
                
            # 清理release目录
            if self.release_dir.exists():
                for file in self.release_dir.glob("*.exe"):
                    file.unlink()
                self.log_message("✅ release目录已清理")
                
            return True
        except Exception as e:
            self.log_message(f"❌ 清理失败: {e}", "ERROR")
            return False

def main():
    """测试函数"""
    project_root = Path(__file__).parent.parent
    builder = WuWaBuild(project_root)
    
    print("开始构建测试...")
    success = builder.build_servers()
    
    if success:
        print("构建测试成功")
    else:
        print("构建测试失败")

if __name__ == "__main__":
    main()