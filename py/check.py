#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
鸣潮服务端环境检查模块

功能：
- 检查系统要求（操作系统、Python版本）
- 检查必要目录（wicked-waifus-rs源码目录）
- 检查依赖环境（Rust、Cargo等）
- 提供环境检查结果和建议
"""

import os
import sys
import platform
import subprocess
import shutil
import socket
from pathlib import Path
from typing import Dict, List, Tuple

class WuWaEnvironmentChecker:
    """鸣潮服务端环境检查器"""
    
    def __init__(self, project_root):
        self.project_root = Path(project_root)
        self.wicked_waifus_path = self.project_root / "wicked-waifus-rs"
        self.release_dir = self.project_root / "release"
        self.check_results = []
        
    def add_result(self, check_name: str, passed: bool, message: str, suggestion: str = ""):
        """添加检查结果"""
        self.check_results.append({
            'name': check_name,
            'passed': passed,
            'message': message,
            'suggestion': suggestion
        })
        
    def check_operating_system(self) -> bool:
        """检查操作系统"""
        try:
            os_name = platform.system()
            os_version = platform.release()
            
            if os_name == "Windows":
                self.add_result(
                    "操作系统", True, 
                    f"✅ Windows {os_version}",
                    ""
                )
                return True
            elif os_name == "Linux":
                self.add_result(
                    "操作系统", True, 
                    f"✅ Linux {os_version}",
                    ""
                )
                return True
            elif os_name == "Darwin":
                self.add_result(
                    "操作系统", True, 
                    f"✅ macOS {os_version}",
                    ""
                )
                return True
            else:
                self.add_result(
                    "操作系统", True, 
                    f"✅ {os_name} {os_version}",
                    "如遇问题请检查依赖环境"
                )
                return True
        except Exception as e:
            self.add_result(
                "操作系统", False, 
                f"❌ 无法检测操作系统: {e}",
                "请确保系统环境正常"
            )
            return False
            
    def check_python_version(self) -> bool:
        """检查Python版本"""
        try:
            python_version = sys.version_info
            version_str = f"{python_version.major}.{python_version.minor}.{python_version.micro}"
            
            if python_version.major >= 3 and python_version.minor >= 8:
                self.add_result(
                    "Python版本", True, 
                    f"✅ Python {version_str}",
                    ""
                )
                return True
            else:
                self.add_result(
                    "Python版本", False, 
                    f"❌ Python版本过低: {version_str}",
                    "请升级到Python 3.8或更高版本"
                )
                return False
        except Exception as e:
            self.add_result(
                "Python版本", False, 
                f"❌ 无法检测Python版本: {e}",
                "请确保Python环境正常"
            )
            return False
            
    def check_source_directory(self) -> bool:
        """检查源码目录（用于构建时）"""
        try:
            if self.wicked_waifus_path.exists() and self.wicked_waifus_path.is_dir():
                # 检查是否包含Cargo.toml文件
                cargo_toml = self.wicked_waifus_path / "Cargo.toml"
                if cargo_toml.exists():
                    self.add_result(
                        "源码目录", True, 
                        "✅ wicked-waifus-rs 源码目录存在且包含Cargo.toml",
                        ""
                    )
                    return True
                else:
                    self.add_result(
                        "源码目录", False, 
                        "❌ wicked-waifus-rs 目录存在但缺少Cargo.toml",
                        "请确保源码完整下载"
                    )
                    return False
            else:
                self.add_result(
                    "源码目录", False, 
                    "❌ wicked-waifus-rs 源码目录不存在",
                    "请先下载源码（菜单选项0）"
                )
                return False
        except Exception as e:
            self.add_result(
                "源码目录", False, 
                f"❌ 检查源码目录时出错: {e}",
                "请检查文件系统权限"
            )
            return False
            
    def check_executables_for_runtime(self) -> bool:
        """检查可执行文件（用于运行时）"""
        try:
            if not self.release_dir.exists():
                self.add_result(
                    "可执行文件", False, 
                    "❌ release目录不存在",
                    "请先构建服务端（菜单选项1）或确保可执行文件存在"
                )
                return False
                
            # 检查关键可执行文件
            required_executables = [
                "wicked-waifus-config-server.exe",
                "wicked-waifus-login-server.exe",
                "wicked-waifus-gateway-server.exe",
                "wicked-waifus-game-server.exe",
                "wicked-waifus-hotpatch-server.exe"
            ]
            
            missing_files = []
            for exe in required_executables:
                exe_path = self.release_dir / exe
                if not exe_path.exists():
                    missing_files.append(exe)
                    
            if missing_files:
                # 检查是否有源码和Rust环境作为备选
                has_source = self.wicked_waifus_path.exists() and (self.wicked_waifus_path / "Cargo.toml").exists()
                has_rust = self._check_rust_available()
                
                if has_source and has_rust:
                    self.add_result(
                        "可执行文件", True, 
                        f"⚠️  缺少可执行文件: {', '.join(missing_files)}\n    ✅ 但源码和Rust环境可用，将使用cargo run模式",
                        "建议构建release版本以获得更好性能"
                    )
                    return True
                else:
                    self.add_result(
                        "可执行文件", False, 
                        f"❌ 缺少可执行文件: {', '.join(missing_files)}\n    ❌ 且无法使用cargo run模式（缺少源码或Rust环境）",
                        "请构建服务端（菜单选项1）或下载源码并安装Rust"
                    )
                    return False
            else:
                self.add_result(
                    "可执行文件", True, 
                    "✅ 所有必要的可执行文件都存在",
                    ""
                )
                return True
                
        except Exception as e:
            self.add_result(
                "可执行文件", False, 
                f"❌ 检查可执行文件时出错: {e}",
                "请检查文件系统权限"
            )
            return False
            
    def _check_rust_available(self) -> bool:
        """检查Rust是否可用（内部方法，不添加结果）"""
        try:
            rustc_result = subprocess.run(
                ['rustc', '--version'], 
                capture_output=True, 
                text=True, 
                timeout=5
            )
            cargo_result = subprocess.run(
                ['cargo', '--version'], 
                capture_output=True, 
                text=True, 
                timeout=5
            )
            return rustc_result.returncode == 0 and cargo_result.returncode == 0
        except:
            return False
            
    def check_postgresql_connection(self) -> bool:
        """检查PostgreSQL连接"""
        try:
            # 默认连接参数
            host = "127.0.0.1"
            port = 5432
            database = "users"
            username = "users"
            password = "password"
            
            # 首先检查端口是否开放
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.settimeout(5)
                    result = sock.connect_ex((host, port))
                    if result != 0:
                        self.add_result(
                            "PostgreSQL连接", False,
                            f"❌ 无法连接到PostgreSQL服务器 {host}:{port}",
                            "请确保PostgreSQL服务已启动并监听在5432端口"
                        )
                        return False
            except Exception as e:
                self.add_result(
                    "PostgreSQL连接", False,
                    f"❌ 网络连接检查失败: {e}",
                    "请检查网络配置和防火墙设置"
                )
                return False
            
            # 首先检查是否有psycopg2模块
            psycopg2_available = False
            try:
                import psycopg2
                psycopg2_available = True
            except ImportError:
                pass
            
            # 检查是否有psql命令
            psql_available = False
            try:
                result = subprocess.run(
                    ['psql', '--version'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                psql_available = result.returncode == 0
            except (FileNotFoundError, subprocess.TimeoutExpired):
                pass
            
            # 如果两者都不可用，提供安装建议
            if not psycopg2_available and not psql_available:
                self.add_result(
                    "PostgreSQL连接", False,
                    "❌ 无法测试PostgreSQL连接：缺少必要的连接工具",
                    "请选择以下方案之一：\n" +
                    "    1. 安装Python库: pip install psycopg2-binary\n" +
                    "    2. 安装PostgreSQL客户端工具（包含psql命令）\n" +
                    "    3. 运行: pip install -r requirements.txt 安装所有依赖"
                )
                return False
            
            # 尝试使用psycopg2进行数据库连接测试
            if psycopg2_available:
                try:
                    import psycopg2
                    
                    # 构建连接字符串
                    conn_string = f"host={host} port={port} dbname={database} user={username} password={password}"
                    
                    # 尝试连接
                    with psycopg2.connect(conn_string) as conn:
                        with conn.cursor() as cursor:
                            # 执行简单查询测试连接
                            cursor.execute("SELECT version();")
                            version = cursor.fetchone()[0]
                            
                            self.add_result(
                                "PostgreSQL连接", True,
                                f"✅ PostgreSQL连接成功\n    数据库: {database}@{host}:{port}\n    版本: {version[:50]}...",
                                ""
                            )
                            return True
                            
                except Exception as e:
                    error_msg = str(e)
                    if "authentication failed" in error_msg.lower():
                        suggestion = "请检查数据库用户名和密码是否正确"
                    elif "database" in error_msg.lower() and "does not exist" in error_msg.lower():
                        suggestion = "请确保数据库'users'已创建"
                    elif "connection refused" in error_msg.lower():
                        suggestion = "请确保PostgreSQL服务已启动"
                    else:
                        suggestion = "请检查PostgreSQL配置和网络连接"
                        
                    self.add_result(
                        "PostgreSQL连接", False,
                        f"❌ PostgreSQL连接失败: {error_msg}",
                        suggestion
                    )
                    return False
            
            # 如果psycopg2不可用但psql可用，使用psql命令测试
            elif psql_available:
                try:
                    # 设置环境变量避免密码提示
                    env = os.environ.copy()
                    env['PGPASSWORD'] = password
                    
                    # 执行psql命令测试连接
                    result = subprocess.run(
                        ['psql', '-h', host, '-p', str(port), '-U', username, '-d', database, '-c', 'SELECT version();'],
                        capture_output=True,
                        text=True,
                        timeout=10,
                        env=env
                    )
                    
                    if result.returncode == 0:
                        self.add_result(
                            "PostgreSQL连接", True,
                            f"✅ PostgreSQL连接成功（通过psql命令）\n    数据库: {database}@{host}:{port}",
                            "建议安装psycopg2以获得更好的连接测试: pip install psycopg2-binary"
                        )
                        return True
                    else:
                        error_msg = result.stderr.strip() if result.stderr else "未知错误"
                        self.add_result(
                            "PostgreSQL连接", False,
                            f"❌ PostgreSQL连接失败: {error_msg}",
                            "请检查数据库配置、用户权限和密码"
                        )
                        return False
                        
                except Exception as e:
                    self.add_result(
                        "PostgreSQL连接", False,
                        f"❌ 使用psql命令测试连接时出错: {e}",
                        "请检查PostgreSQL客户端工具安装"
                    )
                    return False

                
        except Exception as e:
            self.add_result(
                "PostgreSQL连接", False,
                f"❌ PostgreSQL连接检查时出错: {e}",
                "请检查系统环境和网络配置"
            )
            return False
            
    def check_rust_environment(self) -> bool:
        """检查Rust环境"""
        try:
            # 检查rustc
            rustc_result = subprocess.run(
                ['rustc', '--version'], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            
            if rustc_result.returncode == 0:
                rustc_version = rustc_result.stdout.strip()
                
                # 检查cargo
                cargo_result = subprocess.run(
                    ['cargo', '--version'], 
                    capture_output=True, 
                    text=True, 
                    timeout=10
                )
                
                if cargo_result.returncode == 0:
                    cargo_version = cargo_result.stdout.strip()
                    self.add_result(
                        "Rust环境", True, 
                        f"✅ {rustc_version}\n    {cargo_version}",
                        ""
                    )
                    return True
                else:
                    self.add_result(
                        "Rust环境", False, 
                        f"✅ {rustc_version}\n    ❌ Cargo未安装或不可用",
                        "请重新安装Rust工具链"
                    )
                    return False
            else:
                self.add_result(
                    "Rust环境", False, 
                    "❌ Rust未安装或不在PATH中",
                    "请安装Rust: https://rustup.rs/"
                )
                return False
                
        except subprocess.TimeoutExpired:
            self.add_result(
                "Rust环境", False, 
                "❌ Rust命令执行超时",
                "请检查Rust安装是否正常"
            )
            return False
        except FileNotFoundError:
            self.add_result(
                "Rust环境", False, 
                "❌ Rust未安装或不在PATH中",
                "请安装Rust: https://rustup.rs/"
            )
            return False
        except Exception as e:
            self.add_result(
                "Rust环境", False, 
                f"❌ 检查Rust环境时出错: {e}",
                "请检查Rust安装"
            )
            return False
            
    def check_release_directory(self) -> bool:
        """检查release目录和可执行文件"""
        try:
            if not self.release_dir.exists():
                self.add_result(
                    "Release目录", False, 
                    "❌ release目录不存在",
                    "请先构建服务端（菜单选项1）"
                )
                return False
                
            # 检查关键可执行文件
            required_executables = [
                "wicked-waifus-config-server.exe",
                "wicked-waifus-login-server.exe",
                "wicked-waifus-gateway-server.exe",
                "wicked-waifus-game-server.exe",
                "wicked-waifus-hotpatch-server.exe"
            ]
            
            missing_files = []
            for exe in required_executables:
                exe_path = self.release_dir / exe
                if not exe_path.exists():
                    missing_files.append(exe)
                    
            if missing_files:
                self.add_result(
                    "Release目录", False, 
                    f"❌ 缺少可执行文件: {', '.join(missing_files)}",
                    "请重新构建服务端（菜单选项1）"
                )
                return False
            else:
                self.add_result(
                    "Release目录", True, 
                    "✅ release目录存在且包含所有必要的可执行文件",
                    ""
                )
                return True
                
        except Exception as e:
            self.add_result(
                "Release目录", False, 
                f"❌ 检查release目录时出错: {e}",
                "请检查文件系统权限"
            )
            return False
            
    def check_dependencies(self) -> bool:
        """检查Python依赖"""
        try:
            required_modules = ['psutil', 'toml']
            missing_modules = []
            
            for module in required_modules:
                try:
                    __import__(module)
                except ImportError:
                    missing_modules.append(module)
                    
            if missing_modules:
                self.add_result(
                    "Python依赖", False, 
                    f"❌ 缺少Python模块: {', '.join(missing_modules)}",
                    "请运行: pip install -r requirements.txt"
                )
                return False
            else:
                self.add_result(
                    "Python依赖", True, 
                    "✅ 所有必要的Python模块已安装",
                    ""
                )
                return True
                
        except Exception as e:
            self.add_result(
                "Python依赖", False, 
                f"❌ 检查Python依赖时出错: {e}",
                "请检查Python环境"
            )
            return False
            
    def run_all_checks(self, silent: bool = False) -> Tuple[bool, List[Dict]]:
        """运行所有环境检查
        
        Args:
            silent: 是否静默模式（不输出到控制台）
            
        Returns:
            Tuple[bool, List[Dict]]: (是否全部通过, 检查结果列表)
        """
        self.check_results.clear()
        
        if not silent:
            print("\n=== 环境检查 ===")
            
        # 执行所有检查
        checks = [
            self.check_operating_system(),
            self.check_python_version(),
            self.check_dependencies(),
            self.check_source_directory(),
            self.check_rust_environment(),
            self.check_release_directory(),
            self.check_postgresql_connection()
        ]
        
        # 输出结果
        if not silent:
            for result in self.check_results:
                print(result['message'])
                if result['suggestion']:
                    print(f"    建议: {result['suggestion']}")
                    
        # 检查是否全部通过
        all_passed = all(checks)
        
        if not silent:
            if all_passed:
                print("\n✅ 环境检查通过，可以启动服务端")
            else:
                print("\n❌ 环境检查未通过，请解决上述问题后重试")
            print()
            
        return all_passed, self.check_results
        
    def check_for_startup(self) -> bool:
        """启动前的环境检查（运行时检查）
        
        Returns:
            bool: 是否可以启动服务端
        """
        print("正在检查运行环境...")
        
        # 运行时关键检查
        critical_checks = [
            self.check_python_version(),
            self.check_dependencies(),
            self.check_executables_for_runtime(),  # 运行时检查可执行文件
            self.check_postgresql_connection()     # 运行时必须检查数据库连接
        ]
        
        # 检查关键项目是否通过
        if not all(critical_checks):
            print("❌ 运行环境检查失败，请解决问题后重试")
            return False
            
        print("✅ 运行环境检查通过")
        return True
        
    def check_for_build(self) -> bool:
        """构建前的环境检查（构建时检查）
        
        Returns:
            bool: 是否可以构建服务端
        """
        print("正在检查构建环境...")
        
        # 构建时关键检查
        critical_checks = [
            self.check_python_version(),
            self.check_dependencies(),
            self.check_source_directory(),  # 构建时检查源码
            self.check_rust_environment()   # 构建时必须有Rust环境
        ]
        
        # 检查关键项目是否通过
        if not all(critical_checks):
            print("❌ 构建环境检查失败，请解决问题后重试")
            return False
            
        print("✅ 构建环境检查通过")
        return True

def main():
    """主函数 - 用于独立运行环境检查"""
    import sys
    from pathlib import Path
    
    # 获取项目根目录
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    # 创建检查器
    checker = WuWaEnvironmentChecker(project_root)
    
    # 运行检查
    all_passed, results = checker.run_all_checks()
    
    # 返回适当的退出码
    sys.exit(0 if all_passed else 1)

if __name__ == "__main__":
    main()