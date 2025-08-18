# CLAUDE.md

**重要说明：在此项目中请始终使用中文回复用户。**

## 项目概述

MCPSecTrace 是一个综合性安全监控与分析工具包，集成了自动化安全工具、系统监控、浏览器取证以及威胁情报的 MCP 服务器。专为防御性安全分析和事件响应设计。

## 项目结构

```
src/mcpsectrace/           # 核心Python包
├── core/                  # 核心功能（浏览器取证、Sysmon收集、自动化基类）
├── automation/            # GUI自动化工具（火绒、HRKill、Focus Pack）
├── mcp_servers/           # MCP服务器包装器
└── utils/                 # 工具和实用程序

external_mcp/              # 外部MCP服务器（威胁情报、日志服务等）
tools/                     # 外部可执行工具和配置
scripts/                   # 启动脚本和管理工具
tests/                     # 测试文件
docs/development/          # 开发文档
```

## 快速开始

### 环境设置
```bash
# 安装依赖
uv sync

# 运行测试验证安装
bash scripts/test_all.sh
```

### 常用命令
```bash
# 浏览器取证
python scripts/run_browser_forensics.py

# 启动MCP服务器
python scripts/start_mcp_servers.py

# 代码质量检查
uv run black src/ tests/
uv run pytest
```

## 重要说明

### 安全性
- 本工具专为**防御性安全分析**设计
- 所有组件需在授权环境中使用
- 部分功能需要管理员权限（Sysmon、Windows日志）

### 平台支持
- 主要目标：Windows系统
- 浏览器取证：跨平台支持
- GUI自动化：Windows专用

### API配置
- ThreatMCP需要微步在线API密钥：`THREATBOOK_API_KEY`
- 详细配置请参考 `docs/development/` 目录

## 开发指南

详细的开发文档位于 `docs/development/` 目录：
- GitHub协作指南
- 重构后测试指南
- 项目架构说明

## 联系和支持

遇到问题请参考开发文档或提交Issue。