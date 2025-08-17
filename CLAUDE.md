# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**重要说明：在此项目中请始终使用中文回复用户。**

## 项目概述

MCPSecTrace 是一个综合性的安全监控与分析工具包，集成了自动化安全工具、系统监控、浏览器取证以及威胁情报的 MCP（模型上下文协议）服务器。该项目主要使用 Python 编写，包含多种适用于 Windows 系统的安全实用工具。

## 核心组件

### 安全分析工具
- **browser_data.py**: 用于从 Chrome、Edge 和 Firefox 提取浏览器历史记录和下载记录的取证工具
- **sysmon.py**: Sysmon 日志收集器，可安装 Sysmon 并将事件日志导出为 JSON 格式
- **huorong.py**: 使用 PyAutoGUI 对火绒杀毒软件进行 GUI 自动化安全日志导出
- **hrkill.py**: HRKill 恶意软件扫描工具的 GUI 自动化
- **focus_pack.py**: Focus Pack 安全扫描工具的 GUI 自动化

### MCP 服务器和威胁情报
`mcp/` 目录包含多个提供安全和威胁情报功能的 MCP 服务器：

#### ThreatMCP（主要威胁情报）
- **位置**: `mcp/ThreatMCP/`
- **用途**: 微步在线威胁情报 API 的完整 MCP 服务器
- **功能**: 15 个安全分析工具，包括 IP 信誉、域名分析、文件分析、URL 扫描和漏洞情报
- **配置**: 需要 `THREATBOOK_API_KEY` 环境变量
- **启动**: `python mcp/ThreatMCP/run_server.py`

#### 其他 MCP 服务器
- **WinLog-MCP**: Windows Sysmon 日志摄取和查询 (`mcp/winlog-mcp-main/`)
- **FDP-MCP**: 奇安信 XLab 网络安全数据访问 (`mcp/fdp-mcp-server-master/`)
- **Everything Search**: 文件搜索功能 (`mcp/mcp-everything-search-main/`)

### 独立 MCP 服务
- **browser_mcp.py**: 浏览器取证功能的 MCP 包装器
- **huorong_mcp.py**: 火绒自动化的 MCP 包装器
- **hrkill_mcp.py**: HRKill 自动化的 MCP 包装器
- **focus_pack_mcp.py**: Focus Pack 自动化的 MCP 包装器

## 开发命令

### 依赖管理
```bash
# 使用 uv 安装依赖
uv sync

# 安装特定包
uv add <package-name>
```

### 运行安全工具
```bash
# 运行浏览器数据提取
python browser_data.py

# 运行 Sysmon 日志收集（需要管理员权限）
python sysmon.py

# 运行火绒自动化（Windows GUI 自动化）
python huorong.py

# 运行安全工具自动化
python hrkill.py
python focus_pack.py
```

### MCP 服务器操作
```bash
# 启动 ThreatMCP 服务器（主要威胁情报）
export THREATBOOK_API_KEY="your_api_key"
python mcp/ThreatMCP/run_server.py

# 启动 WinLog MCP 服务器
python mcp/winlog-mcp-main/src/main.py --storage-path ./logs/

# 启动独立 MCP 服务
python mcp/browser_mcp.py
python mcp/huorong_mcp.py
python mcp/hrkill_mcp.py
python mcp/focus_pack_mcp.py
```

## 架构说明

### GUI 自动化框架
所有 GUI 自动化工具（huorong.py、hrkill.py、focus_pack.py）都使用 PyAutoGUI 配合图像识别：
- 截图存储在按工具组织的 `tag_image/` 目录中
- 基于置信度的图像匹配和超时机制
- 自动化安全工具交互和日志导出

### MCP 集成模式
每个安全工具都有独立版本和 MCP 服务器版本：
- 独立工具用于直接执行
- MCP 包装器通过模型上下文协议提供程序化访问
- 所有 MCP 服务的日志记录和错误处理保持一致

### 安全工具链
项目支持完整的安全分析工作流程：
1. **数据收集**: 浏览器取证、Sysmon 日志、安全工具扫描
2. **威胁情报**: 与多个威胁情报源集成
3. **分析**: 通过 MCP 服务器进行自动化关联和报告
4. **导出**: JSON 格式的结构化数据输出

### 目录结构
- `/tool/`: 包含安全可执行文件（HRKill、Focus Pack、Sysmon）
- `/tag_image/`: 按工具组织的 GUI 自动化截图
- `/logs/`: 各种安全工具的输出日志
- `/browser_data_collection/`: 浏览器取证输出
- `/mcp/`: 所有 MCP 服务器和相关配置

## 重要注意事项

### 管理员权限
多个工具在 Windows 上需要管理员权限：
- `sysmon.py`（Sysmon 安装和日志访问）
- `mcp/winlog-mcp-main/`（Windows 事件日志访问）

### API 密钥和认证
- ThreatMCP 需要有效的微步在线 API 密钥
- FDP-MCP 在生产环境使用时需要奇安信 XLab 凭据

### 平台要求
- 主要目标：Windows 系统
- 浏览器取证：跨平台（Windows、macOS、Linux）
- GUI 自动化：使用 PyAutoGUI 的 Windows 专用功能

### 安全和伦理
本工具包专为防御性安全分析和事件响应而设计。所有组件都应在授权环境中使用，并具备适当的安全监控和威胁分析权限。