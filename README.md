# MCPSecTrace

**综合性安全监控与分析工具包**

MCPSecTrace 是一个集成了自动化安全工具、系统监控、浏览器取证以及威胁情报的 MCP（模型上下文协议）服务器工具包。

## ✨ 主要特性

- 🔍 **浏览器取证**: 从Chrome、Edge、Firefox提取历史记录和下载记录
- 📊 **系统监控**: Sysmon日志收集和分析
- 🤖 **GUI自动化**: 火绒、HRKill、Focus Pack等安全工具的自动化
- 🌐 **威胁情报**: 集成微步在线等多个威胁情报源
- 🔧 **MCP服务器**: 通过模型上下文协议提供程序化访问
- 📦 **模块化架构**: 清晰的代码组织和易于维护的结构

## 🚀 快速开始

### 安装依赖

```bash
# 克隆项目
git clone <repository-url>
cd MCPSecTrace

# 安装依赖
uv sync

# 安装开发依赖（可选）
uv sync --extra dev
```

### 运行工具

```bash
# 浏览器取证
mcpsectrace-browser

# Sysmon日志收集（需要管理员权限）
mcpsectrace-sysmon

# GUI自动化工具
mcpsectrace-huorong    # 火绒
mcpsectrace-hrkill     # HRKill
mcpsectrace-focus      # Focus Pack
```

### 启动MCP服务器

```bash
# 批量启动所有MCP服务器
python scripts/start_mcp_servers.py

# 或启动特定服务器
python src/mcpsectrace/mcp_servers/browser_mcp.py
```

## 📁 项目结构

```
MCPSecTrace/
├── src/mcpsectrace/           # 核心Python包
│   ├── core/                  # 核心功能模块
│   ├── automation/            # GUI自动化工具
│   ├── mcp_servers/           # MCP服务器包装器
│   └── utils/                 # 共享工具和实用程序
├── external_mcp/              # 外部MCP服务器
├── tools/                     # 外部可执行工具
├── assets/screenshots/        # GUI自动化截图资源
├── data/                      # 数据文件
├── config/                    # 配置文件
├── scripts/                   # 启动脚本和工具
└── tests/                     # 测试文件
```

## 🛠️ 开发

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

## ⚠️ 重要说明

### 系统要求
- Python 3.13+
- Windows 系统（GUI自动化功能）
- 管理员权限（部分功能需要）

### 安全考虑
本工具包专为**防御性安全分析**和事件响应而设计。请在授权环境中使用，并具备适当的安全监控和威胁分析权限。

### API配置
- ThreatMCP需要微步在线API密钥：设置环境变量 `THREATBOOK_API_KEY`
- FDP-MCP在生产环境需要奇安信XLab凭据

## 📖 文档

详细的使用说明和开发指南请参考 [CLAUDE.md](CLAUDE.md)。

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交Issue和Pull Request！