#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
鸣潮服务器源码下载脚本

功能：
- 从Git仓库克隆源码
- 断点续传支持
- 自动重试机制
- 进度监控
- 网络检查
"""

import os
import sys
import subprocess
import time
import shutil
import requests
from pathlib import Path
from datetime import datetime

class WuWaGit:
    """鸣潮服务器源码下载类"""
    
    def __init__(self, project_root):
        self.project_root = Path(project_root)
        self.wicked_waifus_path = self.project_root / "wicked-waifus-rs"
        self.logs_dir = self.project_root / "logs"
        self.temp_dir = self.project_root / "temp"
        
        # 确保目录存在
        self.logs_dir.mkdir(exist_ok=True)
        self.temp_dir.mkdir(exist_ok=True)
        
        # Git仓库配置
        self.git_url = "https://git.xeondev.com/wickedwaifus/wicked-waifus-rs.git"
        self.git_branch = "master"
        
    def log_message(self, message, log_type="INFO"):
        """记录日志消息"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{log_type}] {message}"
        
        # 输出到控制台
        print(log_entry)
        
        # 写入日志文件
        log_file = self.logs_dir / "git.log"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(log_entry + "\n")
            
    def check_git_installed(self):
        """检查Git是否已安装"""
        try:
            result = subprocess.run(["git", "--version"], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=10)
            if result.returncode == 0:
                self.log_message(f"✅ {result.stdout.strip()}")
                return True
            else:
                self.log_message("❌ Git未正确安装", "ERROR")
                return False
        except (subprocess.TimeoutExpired, FileNotFoundError):
            self.log_message("❌ Git未安装或不在PATH中", "ERROR")
            self.log_message("请安装Git: https://git-scm.com/download/win", "ERROR")
            return False
            
    def check_network_connectivity(self):
        """检查网络连接"""
        self.log_message("检查网络连接...")
        
        try:
            # 测试连接到Git服务器
            response = requests.get("https://git.xeondev.com", timeout=10)
            if response.status_code == 200:
                self.log_message("✅ 网络连接正常")
                return True
            else:
                self.log_message(f"⚠️  Git服务器响应异常: {response.status_code}", "WARNING")
                return True  # 仍然尝试克隆
        except requests.RequestException as e:
            self.log_message(f"⚠️  网络连接检查失败: {e}", "WARNING")
            self.log_message("将尝试直接克隆，如果失败请检查网络设置", "WARNING")
            return True  # 仍然尝试克隆
            
    def check_existing_repo(self):
        """检查是否已存在仓库"""
        if self.wicked_waifus_path.exists():
            git_dir = self.wicked_waifus_path / ".git"
            if git_dir.exists():
                self.log_message("发现已存在的Git仓库")
                return True
            else:
                self.log_message("发现目录但不是Git仓库，将清理后重新克隆", "WARNING")
                return False
        return False
        
    def update_existing_repo(self):
        """更新已存在的仓库"""
        self.log_message("更新现有仓库...")
        
        try:
            # 检查当前分支
            result = subprocess.run(["git", "branch", "--show-current"], 
                                  cwd=str(self.wicked_waifus_path),
                                  capture_output=True, 
                                  text=True, 
                                  timeout=30)
            
            if result.returncode == 0:
                current_branch = result.stdout.strip()
                self.log_message(f"当前分支: {current_branch}")
            
            # 拉取最新代码
            self.log_message("拉取最新代码...")
            result = subprocess.run(["git", "pull", "origin", self.git_branch], 
                                  cwd=str(self.wicked_waifus_path),
                                  capture_output=True, 
                                  text=True, 
                                  timeout=300)
            
            if result.returncode == 0:
                self.log_message("✅ 仓库更新成功")
                self.log_message(result.stdout.strip())
                return True
            else:
                self.log_message(f"❌ 仓库更新失败: {result.stderr.strip()}", "ERROR")
                return False
                
        except subprocess.TimeoutExpired:
            self.log_message("❌ 仓库更新超时", "ERROR")
            return False
        except Exception as e:
            self.log_message(f"❌ 仓库更新异常: {e}", "ERROR")
            return False
            
    def clone_repository(self, retry_count=3):
        """克隆Git仓库"""
        self.log_message(f"开始克隆仓库: {self.git_url}")
        
        for attempt in range(retry_count):
            try:
                self.log_message(f"克隆尝试 {attempt + 1}/{retry_count}")
                
                # 构建克隆命令
                cmd = [
                    "git", "clone", 
                    "--recursive",  # 包含子模块
                    "--branch", self.git_branch,
                    "--single-branch",  # 只克隆指定分支
                    "--depth", "1",  # 浅克隆，减少下载量
                    self.git_url,
                    str(self.wicked_waifus_path)
                ]
                
                self.log_message(f"执行命令: {' '.join(cmd)}")
                
                # 执行克隆
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    universal_newlines=True
                )
                
                # 实时输出克隆进度
                while True:
                    output = process.stdout.readline()
                    if output == '' and process.poll() is not None:
                        break
                    if output:
                        self.log_message(f"[Git] {output.strip()}")
                        
                # 等待进程完成
                return_code = process.wait()
                
                if return_code == 0:
                    self.log_message("✅ 仓库克隆成功")
                    
                    # 初始化子模块
                    self.init_submodules()
                    
                    return True
                else:
                    self.log_message(f"❌ 仓库克隆失败 (退出码: {return_code})", "ERROR")
                    
            except subprocess.TimeoutExpired:
                self.log_message("❌ 仓库克隆超时", "ERROR")
                process.kill()
            except Exception as e:
                self.log_message(f"❌ 仓库克隆异常: {e}", "ERROR")
                
            if attempt < retry_count - 1:
                self.log_message(f"等待10秒后重试...")
                time.sleep(10)
                
                # 清理失败的克隆
                if self.wicked_waifus_path.exists():
                    try:
                        shutil.rmtree(self.wicked_waifus_path)
                    except Exception as e:
                        self.log_message(f"清理失败的克隆时出错: {e}", "WARNING")
                        
        self.log_message("❌ 仓库克隆失败，已达到最大重试次数", "ERROR")
        return False
        
    def init_submodules(self):
        """初始化Git子模块"""
        self.log_message("初始化Git子模块...")
        
        try:
            # 初始化子模块
            result = subprocess.run(["git", "submodule", "init"], 
                                  cwd=str(self.wicked_waifus_path),
                                  capture_output=True, 
                                  text=True, 
                                  timeout=60)
            
            if result.returncode == 0:
                self.log_message("子模块初始化成功")
            
            # 更新子模块
            result = subprocess.run(["git", "submodule", "update"], 
                                  cwd=str(self.wicked_waifus_path),
                                  capture_output=True, 
                                  text=True, 
                                  timeout=300)
            
            if result.returncode == 0:
                self.log_message("✅ 子模块更新成功")
                return True
            else:
                self.log_message(f"⚠️  子模块更新失败: {result.stderr.strip()}", "WARNING")
                return False
                
        except subprocess.TimeoutExpired:
            self.log_message("❌ 子模块初始化超时", "ERROR")
            return False
        except Exception as e:
            self.log_message(f"❌ 子模块初始化异常: {e}", "ERROR")
            return False
            
    def verify_repository(self):
        """验证仓库完整性"""
        self.log_message("验证仓库完整性...")
        
        # 检查关键文件（移除src检查，因为该仓库不包含src目录）
        required_files = [
            "Cargo.toml",
            "README.md"
        ]
        
        missing_files = []
        for file_name in required_files:
            file_path = self.wicked_waifus_path / file_name
            if not file_path.exists():
                missing_files.append(file_name)
                
        if missing_files:
            self.log_message(f"❌ 缺少关键文件: {', '.join(missing_files)}", "ERROR")
            return False
        else:
            self.log_message("✅ 仓库完整性验证通过")
            return True
            
    def clean_failed_download(self):
        """清理失败的下载"""
        if self.wicked_waifus_path.exists():
            try:
                self.log_message("清理失败的下载...")
                # 尝试多次删除，处理权限问题
                for attempt in range(3):
                    try:
                        shutil.rmtree(self.wicked_waifus_path)
                        self.log_message("✅ 清理完成")
                        return
                    except PermissionError as e:
                        if attempt < 2:
                            self.log_message(f"权限错误，等待2秒后重试... ({attempt + 1}/3)", "WARNING")
                            time.sleep(2)
                        else:
                            self.log_message(f"❌ 清理失败，权限被拒绝: {e}", "ERROR")
                            self.log_message("请手动删除目录或以管理员身份运行", "WARNING")
                    except Exception as e:
                        self.log_message(f"❌ 清理失败: {e}", "ERROR")
                        break
            except Exception as e:
                self.log_message(f"❌ 清理失败: {e}", "ERROR")
                
    def download_source_code(self):
        """下载源码主函数"""
        self.log_message("=== 开始下载源码 ===")
        
        # 检查Git环境
        if not self.check_git_installed():
            return False
            
        # 检查网络连接
        if not self.check_network_connectivity():
            return False
            
        # 检查是否已存在仓库
        if self.check_existing_repo():
            self.log_message("发现已存在的仓库，尝试更新...")
            if self.update_existing_repo():
                if self.verify_repository():
                    self.log_message("=== 源码更新完成 ===")
                    return True
                else:
                    self.log_message("仓库验证失败，将重新克隆", "WARNING")
                    self.clean_failed_download()
            else:
                self.log_message("更新失败，将重新克隆", "WARNING")
                self.clean_failed_download()
                
        # 克隆新仓库
        if self.clone_repository():
            if self.verify_repository():
                self.log_message("=== 源码下载完成 ===")
                return True
            else:
                self.log_message("仓库验证失败", "ERROR")
                self.clean_failed_download()
                return False
        else:
            self.log_message("=== 源码下载失败 ===")
            return False
            
    def get_repository_info(self):
        """获取仓库信息"""
        if not self.wicked_waifus_path.exists():
            return None
            
        try:
            # 获取当前提交信息
            result = subprocess.run(["git", "log", "-1", "--format=%H|%an|%ad|%s"], 
                                  cwd=str(self.wicked_waifus_path),
                                  capture_output=True, 
                                  text=True, 
                                  timeout=10)
            
            if result.returncode == 0:
                commit_info = result.stdout.strip().split('|')
                return {
                    "commit_hash": commit_info[0][:8],
                    "author": commit_info[1],
                    "date": commit_info[2],
                    "message": commit_info[3]
                }
        except Exception:
            pass
            
        return None

    def download_source(self):
        """下载源码（别名方法，兼容main.py调用）"""
        return self.download_source_code()

def main():
    """测试函数"""
    project_root = Path(__file__).parent.parent
    git_manager = WuWaGit(project_root)
    
    print("开始源码下载测试...")
    success = git_manager.download_source_code()
    
    if success:
        print("源码下载测试成功")
        
        # 显示仓库信息
        repo_info = git_manager.get_repository_info()
        if repo_info:
            print(f"\n仓库信息:")
            print(f"提交: {repo_info['commit_hash']}")
            print(f"作者: {repo_info['author']}")
            print(f"日期: {repo_info['date']}")
            print(f"消息: {repo_info['message']}")
    else:
        print("源码下载测试失败")

if __name__ == "__main__":
    main()