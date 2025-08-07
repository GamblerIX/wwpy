#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
鸣潮服务器一键部署工具 - 主入口脚本

功能：
- 1 - 构建服务端
- 2 - 运行服务端
- 3 - 完全卸载项目
- 4 - 监控服务端状态
- 5 - 输出日志所在目录
"""

import os
import sys
import time
import platform
from pathlib import Path

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from build import WuWaBuild
    from run import WuWaRun
    from status import WuWaStatus
    from logs import WuWaLogs
    from uninstall import WuWaUninstall
    from git import WuWaGit
except ImportError as e:
    print(f"导入模块失败: {e}")
    print("请确保所有必要的Python文件都存在")
    sys.exit(1)

class WuWaManager:
    """鸣潮服务器管理器主类"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.wicked_waifus_path = self.project_root / "wicked-waifus-rs"
        self.logs_dir = self.project_root / "logs"
        self.release_dir = self.project_root / "release"
        self.temp_dir = self.project_root / "temp"
        
        # 确保日志目录存在
        self.logs_dir.mkdir(exist_ok=True)
        
        # 初始化各个模块
        self.builder = WuWaBuild(self.project_root)
        self.runner = WuWaRun(self.project_root)
        self.status_checker = WuWaStatus(self.project_root)
        self.log_manager = WuWaLogs(self.project_root)
        self.uninstaller = WuWaUninstall(self.project_root)
        self.git_manager = WuWaGit(self.project_root)
        
        # 初始化主程序日志
        self.setup_main_logging()
        
    def setup_main_logging(self):
        """设置主程序日志"""
        self.main_log_file = self.logs_dir / "main.log"
        
    def log_message(self, message, log_type="INFO"):
        """记录日志消息"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{log_type}] {message}"
        
        # 输出到控制台
        print(log_entry)
        
        # 写入日志文件
        with open(self.main_log_file, "a", encoding="utf-8") as f:
            f.write(log_entry + "\n")
        
    def check_system_requirements(self):
        """检查系统要求"""
        print("\n=== 系统要求检查 ===")
        
        # 检查操作系统
        os_name = platform.system()
        if os_name == "Windows":
            print(f"✅ 操作系统: Windows {platform.release()}")
        elif os_name == "Linux":
            print(f"✅ 操作系统: Linux")
        elif os_name == "Darwin":
            print(f"✅ 操作系统: macOS")
        else:
            print(f"✅ 操作系统: {os_name}")
        print("ℹ️  本工具支持多种操作系统，如遇问题请检查依赖环境")
            
        # 检查Python版本
        python_version = sys.version_info
        if python_version.major >= 3 and python_version.minor >= 8:
            print(f"✅ Python版本: {python_version.major}.{python_version.minor}.{python_version.micro}")
        else:
            print(f"❌ Python版本过低: {python_version.major}.{python_version.minor}.{python_version.micro} (需要3.8+)")
            
        # 检查必要目录
        if self.wicked_waifus_path.exists():
            print("✅ wicked-waifus-rs 源码目录存在")
        else:
            print("❌ wicked-waifus-rs 源码目录不存在")
            
        print()
        
    def show_banner(self):
        """显示程序横幅"""
        banner = """
════════════════════════════════════════════════
鸣潮服务器一键部署工具
项目地址: https://github.com/GamblerIX/wwpy
服务器源码: https://git.xeondev.com/wickedwaifus/
════════════════════════════════════════════════
        """
        print(banner)
        
    def show_menu(self):
        """显示主菜单"""
        menu = """
=== 主菜单 ===
0. 下载源码
1. 构建服务端
2. 运行服务端
3. 完全卸载项目
4. 监控服务端状态
5. 输出日志所在目录
6. 退出程序

请选择操作 (0-6): """
        return input(menu).strip()
        
    def show_server_info(self):
        """显示服务器信息"""
        info = """
=== 服务端口信息 ===
• 10001 - 配置服务器 (config-server)
• 10002 - 登录服务器 (login-server)
• 10003 - 网关服务器 (gateway-server)
• 10004 - 游戏服务器 (game-server)
• 10005 - 热更新服务器 (hotpatch-server)

⚠️  注意: 端口范围为 10001-10005，实际服务对应的端口顺序可能有所不同

=== 数据库配置 ===
• 主机: 127.0.0.1:5432
• 数据库名: users
• 用户: users
• 密码: password
        """
        print(info)
        
    def handle_build(self):
        """处理构建服务端"""
        print("\n=== 构建服务端 ===")
        try:
            success = self.builder.build_servers()
            if success:
                print("✅ 服务端构建完成")
            else:
                print("❌ 服务端构建失败")
        except Exception as e:
            print(f"❌ 构建过程中发生错误: {e}")
            
    def handle_run(self):
        """处理运行服务端"""
        print("\n=== 运行服务端 ===")
        self.show_server_info()
        try:
            # 使用新的配置修改逻辑启动服务器
            success = self.runner.start_all_servers_with_config_modification()
            if success:
                print("✅ 所有服务器启动完成")
                print("\n服务器正在运行中...")
                print("按 Ctrl+C 停止所有服务器")
                self.runner.wait_for_servers()
            else:
                print("❌ 服务器启动失败")
        except KeyboardInterrupt:
            print("\n\n=== 正在停止服务器 ===")
            self.runner.stop_all_servers()
            print("✅ 所有服务器已停止")
        except Exception as e:
            print(f"❌ 运行过程中发生错误: {e}")
            
    def handle_uninstall(self):
        """处理卸载项目"""
        print("\n=== 完全卸载项目 ===")
        confirm = input("⚠️  警告: 这将删除所有构建文件和日志，确定要继续吗？(y/N): ").strip().lower()
        if confirm in ['y', 'yes']:
            try:
                success = self.uninstaller.uninstall_all()
                if success:
                    print("✅ 项目卸载完成")
                else:
                    print("❌ 项目卸载失败")
            except Exception as e:
                print(f"❌ 卸载过程中发生错误: {e}")
        else:
            print("取消卸载操作")
            
    def handle_status(self):
        """处理监控服务端状态"""
        print("\n=== 监控服务端状态 ===")
        try:
            self.status_checker.show_status()
        except Exception as e:
            print(f"❌ 状态检查过程中发生错误: {e}")
            
    def handle_logs(self):
        """处理日志输出"""
        print("\n=== 日志目录信息 ===")
        try:
            self.log_manager.show_logs_info()
        except Exception as e:
            print(f"❌ 日志处理过程中发生错误: {e}")
            
    def handle_download_source(self):
        """处理源码下载"""
        print("\n=== 下载源码 ===")
        try:
            success = self.git_manager.download_source()
            if success:
                print("✅ 源码下载完成")
            else:
                print("❌ 源码下载失败")
        except Exception as e:
            print(f"❌ 下载过程中发生错误: {e}")
            
    def run(self):
        """运行主程序"""
        try:
            # 记录程序启动
            self.log_message("=== 鸣潮服务器一键部署工具启动 ===")
            
            # 清屏
            os.system('cls' if os.name == 'nt' else 'clear')
            
            # 显示横幅
            self.show_banner()
            
            # 检查系统要求
            self.check_system_requirements()
            
            # 主循环
            while True:
                try:
                    choice = self.show_menu()
                    
                    if choice == '6':
                        print("\n感谢使用鸣潮服务器一键部署工具！")
                        break
                    elif choice == '0':
                        self.handle_download_source()
                    elif choice == '1':
                        self.handle_build()
                    elif choice == '2':
                        self.handle_run()
                    elif choice == '3':
                        self.handle_uninstall()
                    elif choice == '4':
                        self.handle_status()
                    elif choice == '5':
                        self.handle_logs()
                    else:
                        print("❌ 无效选择，请输入 0-6 之间的数字")
                        
                    if choice != '6':
                        input("\n按回车键继续...")
                        
                except KeyboardInterrupt:
                    print("\n\n程序被用户中断")
                    break
                except Exception as e:
                    print(f"\n❌ 发生未知错误: {e}")
                    input("按回车键继续...")
                    
        except Exception as e:
            print(f"程序启动失败: {e}")
            sys.exit(1)

def main():
    """主函数"""
    manager = WuWaManager()
    manager.run()

if __name__ == "__main__":
    main()