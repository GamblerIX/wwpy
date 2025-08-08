# 鸣潮服务端一键运行工具

> 上游问题，构建不可用，发行版运行暂时正常，详见已知问题。

> 发行版调试运行有杂乱输出是正常的，不影响运行。

## 项目介绍

这是一个用于一键构建，运行和管理wicked-waifus-rs服务端的Python项目,仅供学习和研究使用。

> 重要！由于不可抗力因素，中国大陆的用户加速器需要全程打开。

> 环境配置教程详见wwpy/docs目录下的环境配置完整指南.md。

> 如果您是技术新手，请参阅wwpy/docs目录下的小白完整使用指南.md。该指南细致地拆分了所有操作，包括环境配置和运行。

## 一键运行脚本

> 请确保您已经正确安装了Python、Rust、Protoc和PostgreSQL！
> 请确保您已经正确配置了数据库！(见下方介绍)

```
git clone https://github.com/GamblerIX/wwpy.git
cd wwpy

pip install -r py/requirements.txt
python main.py
# 小概率是：
# pip3 install -r py/requirements.txt
# python3 main.py
```

## 📁 项目结构

```
wwpy/
    ├── wicked-waifus-rs/   	# 项目源码
	├── docs/                   # 配置文档
    ├── release/            	# 构建目录
    ├── logs/               	# 日志目录
    └── temp/               	# 临时目录
    ├── py/                 	# 脚本目录
    └── README.md           	# 说明文档
```

> 构建项目时源码本身问题导致的错误将显示 [Info] ，不会输出到错误日志文件中。

## 🎮 项目功能

- **0** - 下载源码
- **1** - 构建服务端
- **2** - 运行服务端
- **3** - 停止服务端
- **4** - 完全卸载项目
- **5** - 监控服务端状态
- **6** - 调试运行 (分窗口显示)
- **7** - 环境检查
- **8** - 退出主菜单

## 🌐 服务端口

- 10001 - configserver
- 5500 - loginserver
- 10003 - gateway
- 7777 - kcpport
- 10004 - gameserver
- 10002 - hotpatch


## 🗄️ 数据库配置

```
host = "127.0.0.1:5432"
user_name = "users"
password = "password"
db_name = "users"
```

## 🛡️ 防卡死特性

- 智能资源监控
- 僵死进程检测

## 📋 构建最低要求

- **硬件配置**：
    - CPU：2核+
    - 内存：4GB+
    - 磁盘：10GB+

> 如果不能满足要求，请勿构建代码，极易导致死机和内存泄漏。

- **环境配置**：
	- rust
	- protoc
	- pgsql
    - python
    - git

- **操作系统**:
    - Windows 10+

> 理论上只要环境都对就能运行，但是现在构建出了问题，作者保留的编译版本只能在Windows 10+上运行。

## ⏱️ 构建时间说明

> 以下时间均为作者在 i5-7500@3.40GHz 4核CPU，32GB内存，金百达固态硬盘 上构建的时间，仅供参考。

服务端按以下顺序构建，各组件构建时间如下：

### 构建顺序和时间
1. **wicked-waifus-config-server** - 约 3分02秒
2. **wicked-waifus-hotpatch-server** - 约 45秒
3. **wicked-waifus-login-server** - 约 2分01秒
4. **wicked-waifus-gateway-server** - 约 6分47秒
   - 包含 **kcp v0.1.0** 外部依赖编译 (来自 https://git.xeondev.com/ReversedRoomsMisc/kcp-rs.git)
5. **wicked-waifus-game-server** - 约 7分18秒
   - 包含 **unreal-niggery-rs v0.1.0** 外部依赖编译 (来自 https://git.xeondev.com/ReversedRoomsMisc/unreal-niggery-rs.git)

### 说明
- gateway-server 和 game-server 是构建时间最长的组件
- 主要耗时来源于外部依赖库的编译
- 作者总构建时间约 19-20 分钟


> ⚠️ **注意**：构建时间因硬件配置而异

> ⚠️ **构建警告说明**：在构建 wicked-waifus-game-server 时，源码中存在一些未使用的变量、函数和字段，这些会产生编译警告且应该不会影响正常运行。这些警告来源于源码本身，属于正常现象。

## 构建已知问题（不影响发行版的运行）

> 在wicked-waifus-rs\wicked-waifus-hotpatch-server\src\main.rs第31行，路由路径定义为 "/:env:/client/:hash:/:platform:/config.json" ，这里使用了旧版本的路由语法（以冒号开头的路径参数）。新版本的axum路由器要求使用花括号格式，需要修复这个路由定义为 "/{env}/client/{hash}/{platform}/config.json"。
> 请您在git源码后手动修改源码中的路由配置。

> 上游问题，wicked-waifus-proto仓库自2025.8.8消失或私有化（2025.8.7仍然可用），静待上游修复。（本作者没有备份相关源码文件）
> Docker构建同理
> 未修复前会出现以下报错：
>     Updating git repository `https://git.xeondev.com/wickedwaifus/wicked-waifus-proto`
> error: failed to get `wicked-waifus-protocol` as a dependency of package `wicked-waifus-gateway-server v0.1.0 (C:\Users\Administrator\Downloads\wicked-waifus-rs-main\wicked-waifus-gateway-server)`
>
> Caused by:
>   failed to load source for dependency `wicked-waifus-protocol`
>
> Caused by:
>   Unable to update https://git.xeondev.com/wickedwaifus/wicked-waifus-proto
>
> Caused by:
>   failed to fetch into: C:\Users\Administrator\.cargo\git\db\wicked-waifus-proto-c02ed7b8a05f4123
>
> Caused by:
>   failed to authenticate when downloading repository
>
>   * attempted to find username/password via git's `credential.helper` support, but failed
>
>   if the git CLI succeeds then `net.git-fetch-with-cli` may help here
>   https://doc.rust-lang.org/cargo/reference/config.html#netgit-fetch-with-cli
>
> Caused by:
>   failed to acquire username/password from local configuration

## 🔗 项目地址

- **一键运行脚本**: https://github.com/GamblerIX/wwpy
- **服务端源码**: https://git.xeondev.com/wickedwaifus/wicked-waifus-rs

## 叠甲

> 本项目采用MIT协议开源，您可以在遵守协议且仅为学习和研究使用的前提下自由使用、修改和分发本项目的代码，但是并不包括wicked-waifus-rs目录下的代码。

> wicked-waifus-rs目录下的代码是第三方作者的代码，本作者不对其代码进行任何修改，不直接提供代码，也不承担因此产生的任何后果和责任。使用本项目即视为您同意且理解。