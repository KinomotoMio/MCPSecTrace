# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**重要说明：在此项目中请始终使用中文回复用户。**

## 项目概述

MCPSecTrace 是一个综合性的安全监控与分析工具包，集成了自动化安全工具、系统监控、浏览器取证以及威胁情报的 MCP（模型上下文协议）服务器。该项目主要使用 Python 编写，包含多种适用于 Windows 系统的安全实用工具。

## 核心组件（重构后的模块化架构）

### 核心功能模块 (`src/mcpsectrace/core/`)
- **browser_forensics.py**: 浏览器取证工具，从 Chrome、Edge 和 Firefox 提取历史记录和下载记录
- **sysmon_collector.py**: Sysmon 日志收集器，安装 Sysmon 并导出事件日志为 JSON 格式
- **base_automation.py**: GUI 自动化工具基类，提供统一的自动化框架

### GUI 自动化模块 (`src/mcpsectrace/automation/`)
- **huorong.py**: 火绒杀毒软件 GUI 自动化安全日志导出
- **hrkill.py**: HRKill 恶意软件扫描工具的 GUI 自动化
- **focus_pack.py**: Focus Pack 安全扫描工具的 GUI 自动化

### MCP 服务器模块 (`src/mcpsectrace/mcp_servers/`)
- **browser_mcp.py**: 浏览器取证功能的 MCP 包装器
- **huorong_mcp.py**: 火绒自动化的 MCP 包装器
- **hrkill_mcp.py**: HRKill 自动化的 MCP 包装器
- **focus_pack_mcp.py**: Focus Pack 自动化的 MCP 包装器

### 外部威胁情报服务 (`external_mcp/`)
#### ThreatMCP（主要威胁情报）
- **位置**: `external_mcp/ThreatMCP/`
- **用途**: 微步在线威胁情报 API 的完整 MCP 服务器
- **功能**: 15 个安全分析工具，包括 IP 信誉、域名分析、文件分析、URL 扫描和漏洞情报
- **配置**: 需要 `THREATBOOK_API_KEY` 环境变量

#### 其他外部MCP服务器
- **WinLog-MCP**: Windows Sysmon 日志摄取和查询 (`external_mcp/winlog-mcp/`)
- **FDP-MCP**: 奇安信 XLab 网络安全数据访问 (`external_mcp/fdp-mcp-server/`)
- **Everything Search**: 文件搜索功能 (`external_mcp/mcp-everything-search/`)

### 工具和实用程序 (`src/mcpsectrace/utils/`)
- **logging_setup.py**: 统一的日志配置工具
- **image_recognition.py**: GUI 自动化图像识别和处理工具

## 开发命令

### 依赖管理
```bash
# 使用 uv 安装依赖
uv sync

# 安装开发依赖
uv sync --extra dev

# 安装特定包
uv add <package-name>
```

### 代码质量检查
```bash
# 代码格式化
uv run black src/ tests/
uv run isort src/ tests/

# 类型检查
uv run mypy src/

# 运行测试
uv run pytest
uv run pytest --cov=src/mcpsectrace
```

### 运行安全工具（新的模块化方式）
```bash
# 使用新的脚本启动器
python scripts/run_browser_forensics.py

# 或使用安装后的命令行工具
mcpsectrace-browser    # 浏览器取证
mcpsectrace-sysmon     # Sysmon日志收集（需要管理员权限）
mcpsectrace-huorong    # 火绒自动化
mcpsectrace-hrkill     # HRKill自动化
mcpsectrace-focus      # Focus Pack自动化
```

### MCP 服务器操作
```bash
# 批量启动所有MCP服务器
python scripts/start_mcp_servers.py

# 启动特定的MCP服务器
python src/mcpsectrace/mcp_servers/browser_mcp.py
python src/mcpsectrace/mcp_servers/huorong_mcp.py
python src/mcpsectrace/mcp_servers/hrkill_mcp.py
python src/mcpsectrace/mcp_servers/focus_pack_mcp.py

# 启动外部威胁情报MCP服务器
export THREATBOOK_API_KEY="your_api_key"
python external_mcp/ThreatMCP/run_server.py

# 启动WinLog MCP服务器
python external_mcp/winlog-mcp/src/main.py --storage-path ./data/logs/
```

## 架构说明

### 重构后的GUI自动化框架
所有GUI自动化工具都继承自 `BaseAutomation` 基类，使用统一的架构：
- 截图资源存储在 `assets/screenshots/` 目录中，按工具分类
- 统一的图像识别和点击逻辑（`ImageRecognition` 类）
- 基于置信度的图像匹配和超时机制
- 统一的日志记录和错误处理
- 模块化的自动化流程：启动扫描 → 等待完成 → 导出结果

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

### 重构后的目录结构
```
src/mcpsectrace/           # 核心Python包
├── core/                  # 核心功能模块
├── automation/            # GUI自动化工具
├── mcp_servers/           # MCP服务器包装器
└── utils/                 # 共享工具和实用程序

external_mcp/              # 外部MCP服务器
├── ThreatMCP/             # 威胁情报服务
├── winlog-mcp/            # Windows日志服务
├── fdp-mcp-server/        # FDP安全数据服务
└── mcp-everything-search/ # 文件搜索服务

tools/                     # 外部可执行工具
├── executables/           # 安全扫描工具(.exe文件)
└── sysmon/                # Sysmon配置文件

assets/screenshots/        # GUI自动化截图资源
data/                      # 数据文件
├── browser_exports/       # 浏览器取证输出
└── logs/                  # 各种工具的日志文件

config/                    # 配置文件
scripts/                   # 启动脚本和工具
tests/                     # 测试文件
docs/                      # 文档
```

## 重要注意事项

### 管理员权限
多个工具在 Windows 上需要管理员权限：
- `src/mcpsectrace/core/sysmon_collector.py`（Sysmon 安装和日志访问）
- `external_mcp/winlog-mcp/`（Windows 事件日志访问）

### API 密钥和认证
- ThreatMCP 需要有效的微步在线 API 密钥
- FDP-MCP 在生产环境使用时需要奇安信 XLab 凭据

### 平台要求
- 主要目标：Windows 系统
- 浏览器取证：跨平台（Windows、macOS、Linux）
- GUI 自动化：使用 PyAutoGUI 的 Windows 专用功能

### 安全和伦理
本工具包专为防御性安全分析和事件响应而设计。所有组件都应在授权环境中使用，并具备适当的安全监控和威胁分析权限。