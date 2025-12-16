# MCPSecTrace 部署运维指南

> **文档版本**: 2.0
> **更新日期**: 2025年12月11日
> **适用对象**: 甲方企业技术人员、安全运维人员

---

## 📋 目录

1. [项目概述](#1-项目概述)
2. [项目架构](#2-项目架构)
3. [原理介绍](#3-原理介绍)
4. [部署流程](#4-部署流程)
5. [功能测试](#5-功能测试)
6. [常见问题](#6-常见问题)

---

## 1. 项目概述

### 1.1 什么是 MCPSecTrace?

MCPSecTrace 是一个**综合性安全监控与分析工具包**,专为企业内部安全团队设计。它通过 AI 助手实现智能化的安全告警溯源和分析,大幅提升安全事件响应效率。

### 1.2 核心能力

#### 🔍 **浏览器取证**
从 Chrome、Edge、Firefox 等主流浏览器提取用户活动历史、下载记录等关键取证信息,支持跨平台操作。

**典型应用场景**:
- 内网失陷主机浏览器历史溯源
- 可疑下载行为追踪
- 用户访问记录审计

#### 📊 **系统监控**
自动收集和分析 Windows Sysmon 日志,支持进程创建、网络连接、文件操作等多种事件类型的结构化分析。

**典型应用场景**:
- 异常进程行为检测
- 攻击链路还原
- 横向移动追踪

#### 🤖 **安全工具自动化**
通过 GUI 自动化技术,实现对火绒、HRKill、Focus Pack 等常用安全工具的自动化操作。

**支持的工具**:
- **火绒安全** - 自动扫描、导出日志
- **HRKill** - 病毒查杀工具自动化
- **Focus Pack** - 应急响应工具包自动化

**典型应用场景**:
- 批量主机扫描
- 自动化应急响应
- 安全工具批量部署

#### 🌐 **威胁情报集成**
集成微步在线等威胁情报源,支持 IP、域名、文件哈希等 IOC 的自动化查询和分析。

**典型应用场景**:
- 可疑 IP 快速研判
- 恶意文件关联分析
- 威胁情报自动关联

#### 🧠 **AI 辅助分析**
通过 MCP 协议将所有工具能力统一暴露给 AI 助手,实现自然语言驱动的安全分析操作。

**典型应用场景**:
```
用户: "帮我分析这台主机 192.168.1.100 是否失陷"
AI: [自动调用浏览器取证] → [查询威胁情报] → [分析 Sysmon 日志] → [生成溯源报告]
```

### 1.3 技术特点

| 特性 | 说明 |
|-----|------|
| 🚀 **一键部署** | 提供自动化部署脚本,简化环境配置 |
| 🔧 **模块化设计** | 核心功能独立封装,易于扩展和维护 |
| 🎯 **MCP 标准** | 基于 Anthropic MCP 协议,实现 AI 工具标准化集成 |
| 📦 **跨平台支持** | 核心功能支持 Windows/Linux/macOS |
| 🔒 **安全可控** | 所有操作本地执行,数据不出网 |

### 1.4 适用场景

✅ **适用于**:
- 企业内部安全运营中心 (SOC)
- 应急响应团队
- 安全事件溯源分析
- 自动化安全巡检
- 威胁狩猎 (Threat Hunting)

❌ **不适用于**:
- 攻击性安全测试 (本工具仅用于防御)
- 未授权的系统监控
- 个人隐私侵犯场景

---

## 2. 项目架构

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                       AI 助手层 (Cline)                       │
│              通过 MCP 协议与工具层交互                          │
└─────────────────────────────────────────────────────────────┘
                              ▲
                              │ MCP 协议 (JSON-RPC)
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      MCP 服务器层                             │
├─────────────────────────────────────────────────────────────┤
│  browser_mcp    │  huorong_mcp  │  hrkill_mcp              │
│  浏览器取证      │  火绒自动化     │  HRKill自动化             │
├─────────────────────────────────────────────────────────────┤
│  focus_pack_mcp │  ioc_mcp      │  winlog_mcp              │
│  应急工具自动化   │  威胁情报查询   │  Windows日志分析          │
└─────────────────────────────────────────────────────────────┘
                              ▲
                              │ Python API
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                       核心功能层                              │
├─────────────────────────────────────────────────────────────┤
│  browser_forensics  │  sysmon_collector  │  automation     │
│  浏览器取证核心      │  Sysmon日志收集     │  GUI自动化基类    │
└─────────────────────────────────────────────────────────────┘
                              ▲
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      外部工具和数据源                          │
├─────────────────────────────────────────────────────────────┤
│  火绒安全  │  HRKill  │  Focus Pack  │  微步在线  │  Sysmon  │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 目录结构

```
MCPSecTrace/
├── src/mcpsectrace/              # 核心 Python 包
│   ├── core/                     # 核心功能模块
│   │   ├── browser_forensics.py  # 浏览器取证引擎
│   │   ├── sysmon_collector.py   # Sysmon 日志收集器
│   │   └── automation_base.py    # GUI 自动化基类
│   ├── automation/               # 安全工具自动化
│   │   ├── huorong.py            # 火绒自动化
│   │   ├── hrkill.py             # HRKill 自动化
│   │   └── focus_pack.py         # Focus Pack 自动化
│   ├── mcp_servers/              # MCP 服务器实现
│   │   ├── browser_mcp.py        # 浏览器取证 MCP
│   │   ├── huorong_mcp.py        # 火绒 MCP
│   │   ├── hrkill_mcp.py         # HRKill MCP
│   │   ├── focus_pack_mcp.py     # Focus Pack MCP
│   │   └── ioc_mcp.py            # 威胁情报 MCP
│   └── utils/                    # 工具和实用程序
│       ├── config.py             # 配置管理
│       ├── logger.py             # 日志系统
│       └── image_utils.py        # 图像识别工具
├── external_mcp/                 # 外部 MCP 服务器
│   └── winlog-mcp/               # Windows 日志分析 MCP
├── config/                       # 配置文件
│   ├── defaults/                 # 系统默认配置
│   │   ├── base.toml             # 基础配置
│   │   ├── browser.toml          # 浏览器取证配置
│   │   ├── automation.toml       # 自动化配置
│   │   └── ioc.toml              # IOC 配置
│   ├── custom/                   # 用户自定义配置
│   └── user_settings.toml        # 用户核心配置 ⭐
├── assets/                       # 资源文件
│   └── screenshots/              # GUI 自动化截图模板
│       ├── huorong/              # 火绒界面截图
│       ├── hrkill/               # HRKill 界面截图
│       └── focus_pack/           # Focus Pack 界面截图
├── tools/                        # 外部工具存放目录
│   ├── chrome-win64/             # Chrome 浏览器
│   ├── chromedriver-win64/       # ChromeDriver
│   ├── Focus_Pack.exe            # Focus Pack 工具
│   └── hrkill-1.0.0.86.exe       # HRKill 工具
├── data/                         # 数据文件
│   └── logs/                     # 日志输出目录
│       ├── ioc/                  # IOC 查询结果
│       └── browser/              # 浏览器取证结果
├── scripts/                      # 脚本工具
│   ├── start_mcp_servers.py      # MCP 服务器启动脚本
│   └── run_browser_forensics.py  # 浏览器取证脚本
├── tests/                        # 测试文件
│   └── deployment_test.py        # 部署测试脚本
├── pyproject.toml                # 项目配置和依赖
├── README.md                     # 项目说明
├── CLAUDE.md                     # AI 助手使用说明
└── uv.lock                       # 依赖锁定文件
```

### 2.3 核心组件说明

#### 核心功能层 (Core)

| 组件 | 功能 | 输入 | 输出 |
|------|------|------|------|
| `browser_forensics` | 浏览器取证 | 浏览器类型、最大记录数 | JSON 格式的历史记录 |
| `sysmon_collector` | Sysmon 日志收集 | 日志路径、过滤条件 | 结构化日志数据 |
| `automation_base` | GUI 自动化基类 | 截图模板、操作序列 | 自动化执行结果 |

#### MCP 服务器层

每个 MCP 服务器都封装了对应的核心功能,通过 MCP 协议暴露给 AI 助手:

```python
# 示例: browser_mcp.py 的服务暴露
@mcp.tool()
def get_chrome_history(max_items: int = 100):
    """获取 Chrome 浏览器历史记录"""
    # 调用 core.browser_forensics 模块
    return browser_forensics.get_chrome_history(max_items)
```

#### 自动化工具层

基于 PyAutoGUI 和图像识别技术,实现安全工具的 GUI 自动化:

```python
# 火绒自动化示例流程
1. 启动火绒安全软件
2. 图像识别定位"安全日志"按钮
3. 点击进入日志界面
4. 导出日志到指定目录
5. 返回执行结果
```

---

## 3. 原理介绍

### 3.1 MCP 协议原理

#### 什么是 MCP?

MCP (Model Context Protocol,模型上下文协议) 是 Anthropic 推出的开源标准协议,用于实现 AI 工具与外部系统的标准化集成。

**类比理解**: MCP 就像 USB 接口
- **传统方式**: 每个 AI 工具需要单独开发与各种系统的连接 (M×N 复杂度)
- **MCP 方式**: 统一接口标准,简化为 M+N 复杂度

#### MCP 通信流程

```
┌─────────┐                    ┌─────────┐                    ┌─────────┐
│ AI 助手  │                    │  MCP    │                    │  安全   │
│ (Cline) │                    │  服务器  │                    │  工具   │
└─────────┘                    └─────────┘                    └─────────┘
     │                              │                              │
     │  1. 发现可用工具              │                              │
     ├──────── discover ──────────>│                              │
     │<──── tool_list ─────────────┤                              │
     │                              │                              │
     │  2. 调用工具                 │                              │
     ├──── call_tool(params) ─────>│                              │
     │                              │  3. 执行实际操作              │
     │                              ├────────────────────────────>│
     │                              │<─────── result ─────────────┤
     │<──── result ────────────────┤                              │
     │                              │                              │
```

#### MCP 配置示例

```json
{
  "mcpServers": {
    "browser_mcp": {
      "command": "uv",
      "args": [
        "--directory",
        "D:/MCPSecTrace/",
        "run",
        "python",
        "-m",
        "mcpsectrace.mcp_servers.browser_mcp"
      ]
    }
  }
}
```

### 3.2 浏览器取证原理

#### 数据源位置

| 浏览器 | 历史记录数据库 | 时间戳格式 |
|--------|---------------|-----------|
| Chrome | `%USERPROFILE%\AppData\Local\Google\Chrome\User Data\Default\History` | WebKit 时间戳 (1601-01-01 起的微秒数) |
| Edge | `%USERPROFILE%\AppData\Local\Microsoft\Edge\User Data\Default\History` | WebKit 时间戳 |
| Firefox | `%APPDATA%\Mozilla\Firefox\Profiles\*.default\places.sqlite` | Unix 时间戳 (1970-01-01 起的微秒数) |

#### 取证流程

```python
# 1. 检测浏览器进程是否运行
if is_browser_running("chrome.exe"):
    print("警告: Chrome 正在运行,建议关闭后再取证")

# 2. 复制数据库文件(避免文件锁定)
shutil.copy(history_db, temp_db)

# 3. 查询历史记录
conn = sqlite3.connect(temp_db)
cursor = conn.execute("""
    SELECT url, title, visit_count, last_visit_time
    FROM urls
    ORDER BY last_visit_time DESC
    LIMIT ?
""", (max_items,))

# 4. 转换时间戳格式
chrome_time = row['last_visit_time']
datetime_obj = datetime(1601, 1, 1) + timedelta(microseconds=chrome_time)

# 5. 输出 JSON 格式结果
```

### 3.3 GUI 自动化原理

#### 图像识别技术

MCPSecTrace 使用 PyAutoGUI 库实现 GUI 自动化,核心技术是**模板匹配**:

```python
# 1. 截取屏幕
screenshot = pyautogui.screenshot()

# 2. 在屏幕上查找目标图像
location = pyautogui.locateCenterOnScreen(
    'button_template.png',
    confidence=0.85  # 相似度阈值
)

# 3. 点击找到的位置
if location:
    pyautogui.click(location.x, location.y)
```

#### 自动化流程

```
┌─────────────────────────────────────────────────────────┐
│  1. 启动目标程序                                          │
│     subprocess.Popen(tool_path)                         │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│  2. 等待界面加载                                          │
│     time.sleep(load_wait_time)                          │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│  3. 图像识别定位元素                                      │
│     location = pyautogui.locateOnScreen(template)       │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│  4. 模拟点击操作                                          │
│     pyautogui.click(location)                           │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│  5. 等待操作完成                                          │
│     等待下一个界面元素出现                                 │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│  6. 循环执行步骤 3-5,直到完成所有操作                       │
└─────────────────────────────────────────────────────────┘
```

#### 关键技术参数

| 参数 | 说明 | 推荐值 |
|------|------|--------|
| `confidence` | 图像匹配置信度 | 0.8-0.9 |
| `timeout` | 查找超时时间 | 10-30 秒 |
| `retry_count` | 失败重试次数 | 3 次 |
| `wait_time` | 操作间隔时间 | 根据设备性能动态调整 |

### 3.4 威胁情报查询原理

#### Selenium 自动化流程

```python
# 1. 启动 Chrome 浏览器
options = webdriver.ChromeOptions()
options.add_argument(f'--user-data-dir={user_data_dir}')  # 使用已登录的 Profile
driver = webdriver.Chrome(service=Service(chromedriver_path), options=options)

# 2. 访问威胁情报平台
driver.get(f'https://x.threatbook.com/v5/ip/{ioc}')

# 3. 等待页面加载
WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.CSS_SELECTOR, '.threat-score'))
)

# 4. 提取威胁情报数据
threat_score = driver.find_element(By.CSS_SELECTOR, '.threat-score').text
threat_tags = driver.find_elements(By.CSS_SELECTOR, '.threat-tag')

# 5. 截图保存
driver.save_screenshot('ioc_report.png')

# 6. 生成结构化报告
report = {
    'ioc': ioc,
    'threat_score': threat_score,
    'tags': [tag.text for tag in threat_tags],
    'screenshot': 'ioc_report.png'
}
```

#### 保持登录会话

通过指定 Chrome 用户数据目录,复用已登录的浏览器会话:

```
chrome_user_data_dir = "C:\Users\User\AppData\Local\Google\Chrome for Testing\User Data"
```

---

## 4. 部署流程

### 4.1 系统要求

#### 硬件要求

| 组件 | 最低配置 | 推荐配置 |
|------|---------|---------|
| CPU | 4 核心 | 8 核心+ |
| 内存 | 8GB | 16GB+ |
| 硬盘 | 20GB 可用空间 | 50GB+ SSD |
| 显示器 | 1920×1080 | 1920×1080+ |

#### 软件要求

| 软件 | 版本要求 | 说明 |
|------|---------|------|
| 操作系统 | Windows 10/11 (64位) | GUI 自动化功能需要 Windows |
| Python | 3.13+ | 核心运行环境 |
| VSCode | 最新版 | AI 助手集成环境 |
| Cline 插件 | 最新版 | AI 助手插件 |

#### 权限要求

- ✅ **管理员权限** (部分功能需要,如 Sysmon 日志收集)
- ✅ **防火墙例外** (MCP 服务器通信)
- ✅ **网络访问** (威胁情报查询)

### 4.2 快速部署 (推荐)

#### 方式一: 一键部署脚本 (即将推出)

> ⚠️ **注意**: 一键部署脚本正在开发中,当前请使用方式二进行部署。

未来将提供 `deploy.exe` 一键部署工具,自动完成所有环境配置:

```powershell
# 1. 下载部署包
# 2. 解压到 D:\MCPSecTrace\
# 3. 右键以管理员身份运行 deploy.exe
# 4. 按照向导完成部署
```

部署脚本将自动完成:
- ✅ Python 环境检测和安装
- ✅ uv 包管理器安装
- ✅ 项目依赖安装
- ✅ 外部工具路径自动扫描
- ✅ 配置文件自动生成
- ✅ MCP 服务器配置
- ✅ 部署测试验证

#### 方式二: 手动部署

##### 步骤 1: 安装 uv 包管理器

**Windows 用户**:

以管理员身份打开 PowerShell,执行:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Linux 用户**:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**验证安装**:

```powershell
uv --version
# 输出: uv 0.x.x
```

##### 步骤 2: 解压项目文件

将 `MCPSecTrace.zip` 和 `MCPTools.zip` 解压到 `D:\` 盘:

```
D:\MCPSecTrace\       # 项目源码
D:\MCPTools\          # 外部工具
```

`MCPTools` 目录结构:

```
D:\MCPTools\
├── chrome-win64\               # Chrome 浏览器
│   └── chrome.exe
├── chromedriver-win64\         # ChromeDriver
│   └── chromedriver.exe
├── Everything\                 # Everything 搜索工具
│   └── Everything-1.4.1.1024.x64\
│       ├── Everything.exe
│       └── es.exe              # 命令行工具
├── Focus_Pack.exe              # Focus Pack 应急工具
└── hrkill-1.0.0.86.exe         # HRKill 病毒查杀工具
```

##### 步骤 3: 安装项目依赖

打开命令行,进入项目目录:

```powershell
cd D:\MCPSecTrace
uv sync
```

等待依赖安装完成 (首次安装约需 3-5 分钟)。

##### 步骤 4: 配置工具路径

编辑 [config/user_settings.toml](config/user_settings.toml) 文件:

```toml
[paths]
# Everything 搜索工具根目录 (必填)
everything_root = "D:\\MCPTools\\Everything"

# 火绒安全软件主程序路径 (根据实际安装路径修改)
huorong_exe = "C:\\Program Files (x86)\\Huorong\\ESEndpoint\\bin\\HipsMain.exe"

# HRKill 工具程序路径
hrkill_exe = "D:\\MCPTools\\hrkill-1.0.0.86.exe"

# Focus Pack 工具程序路径
focus_pack_exe = "D:\\MCPTools\\Focus_Pack.exe"

# Chrome 浏览器程序路径
chrome_exe = "D:\\MCPTools\\chrome-win64\\chrome.exe"

# ChromeDriver 程序路径
chromedriver_exe = "D:\\MCPTools\\chromedriver-win64\\chromedriver.exe"

# Chrome 用户数据目录 (需要根据实际情况修改)
chrome_user_data_dir = "C:\\Users\\YourUsername\\AppData\\Local\\Google\\Chrome for Testing\\User Data"
```

**如何获取 Chrome 用户数据目录**:

1. 打开 `D:\MCPTools\chrome-win64\chrome.exe`
2. 在地址栏输入 `chrome://version/`
3. 查找"个人资料路径",复制路径
4. **删除路径末尾的 `\Default`**,填入配置文件

示例:
```
个人资料路径: C:\Users\User\AppData\Local\Google\Chrome for Testing\User Data\Default
配置文件填写: C:\Users\User\AppData\Local\Google\Chrome for Testing\User Data
```

5. 使用该 Chrome 登录微步云平台 (https://x.threatbook.com),登录后关闭浏览器

##### 步骤 5: 验证部署

运行部署测试脚本:

```powershell
cd D:\MCPSecTrace
uv run python tests/deployment_test.py
```

如果看到以下输出,说明部署成功:

```
✅ MCPSecTrace 部署测试通过!
✅ Python 版本: 3.13.x
✅ 依赖包安装正常
✅ 配置文件加载成功
✅ MCP 服务器可以正常启动
```

### 4.3 配置 VSCode + Cline

#### 步骤 1: 安装 VSCode

1. 运行 `VSCodeUserSetup-x64-1.104.x.exe` (配套文件中提供)
2. 安装过程中勾选:
   - ☑ 创建桌面快捷方式
   - ☑ 将 Code 注册为支持的文件类型的编辑器
   - ☑ 添加到 PATH

#### 步骤 2: 安装 Cline 插件

1. 打开 VSCode
2. 点击左侧**扩展**(Extensions)图标
3. 搜索 `Cline`,点击**安装**
4. 安装完成后,左侧会出现 Cline 图标

#### 步骤 3: 安装中文语言包 (可选)

1. 扩展搜索 `Chinese (Simplified)`
2. 安装 Microsoft 官方中文语言包
3. 重启 VSCode 应用中文界面

#### 步骤 4: 配置 Cline API

1. 点击左侧 Cline 图标
2. 点击右上角⚙️**设置**按钮
3. 选择 **API Configuration**

**配置 DeepSeek API** (推荐,性价比高):

```
API Provider: DeepSeek
DeepSeek API Key: sk-xxxxxxxxxxxxxxxxxxxxxxxx
Model: deepseek-chat
```

> 💡 **如何获取 DeepSeek API Key**:
> 1. 访问 https://platform.deepseek.com/
> 2. 注册并登录
> 3. 进入"API Keys"页面创建密钥

**配置 Plan Mode 和 Act Mode**:

Plan Mode 和 Act Mode 都使用相同的 DeepSeek 配置。

4. 选择 **General Settings**,设置:

```
Preferred Language: Simplified Chinese - 简体中文
```

5. 点击 **Done** 保存配置

#### 步骤 5: 配置 MCP 服务器

1. 右键以**管理员身份**打开 VSCode
2. 打开项目文件夹: `D:\MCPSecTrace`
3. 点击 Cline 图标,选择 **MCP Servers** → **Configure MCP Servers**
4. 在右侧打开的 `cline_mcp_settings.json` 中,粘贴以下配置:

```json
{
  "mcpServers": {
    "browser_mcp": {
      "disabled": false,
      "timeout": 60,
      "type": "stdio",
      "command": "uv",
      "args": [
        "--directory",
        "D:/MCPSecTrace/",
        "run",
        "python",
        "-m",
        "mcpsectrace.mcp_servers.browser_mcp"
      ]
    },
    "huorong_mcp": {
      "disabled": false,
      "timeout": 120,
      "type": "stdio",
      "command": "uv",
      "args": [
        "--directory",
        "D:/MCPSecTrace/",
        "run",
        "python",
        "-m",
        "mcpsectrace.mcp_servers.huorong_mcp"
      ]
    },
    "hrkill_mcp": {
      "disabled": false,
      "timeout": 120,
      "type": "stdio",
      "command": "uv",
      "args": [
        "--directory",
        "D:/MCPSecTrace/",
        "run",
        "python",
        "-m",
        "mcpsectrace.mcp_servers.hrkill_mcp"
      ]
    },
    "focus_pack_mcp": {
      "disabled": false,
      "timeout": 120,
      "type": "stdio",
      "command": "uv",
      "args": [
        "--directory",
        "D:/MCPSecTrace/",
        "run",
        "python",
        "-m",
        "mcpsectrace.mcp_servers.focus_pack_mcp"
      ]
    },
    "ioc_mcp": {
      "disabled": false,
      "timeout": 180,
      "type": "stdio",
      "command": "uv",
      "args": [
        "--directory",
        "D:/MCPSecTrace/",
        "run",
        "python",
        "-m",
        "mcpsectrace.mcp_servers.ioc_mcp"
      ]
    }
  }
}
```

> ⚠️ **注意**: 如果项目不在 `D:\MCPSecTrace\`,请修改所有 `--directory` 参数为实际路径。

5. 保存文件 (Ctrl+S)
6. 检查 MCP 服务器状态:每个服务器左侧的指示灯应该变为**绿色**✅

如果指示灯为**红色**❌,请检查:
- 项目路径是否正确
- 是否以管理员身份运行 VSCode
- Python 依赖是否安装完成

#### 步骤 6: 测试 AI 助手

在 Cline 对话框中输入:

```
测试一下 MCPSecTrace 的部署状态
```

AI 应该能够自动调用 MCP 工具并返回部署信息。

---

## 5. 功能测试

部署完成后,建议按照以下顺序测试各项功能。

### 5.1 浏览器取证测试

**测试命令**:

```
帮我提取 Chrome 浏览器的最近 50 条历史记录
```

**预期结果**:

AI 助手会自动:
1. 调用 `browser_mcp` 服务
2. 读取 Chrome 历史数据库
3. 返回 JSON 格式的历史记录
4. 包含 URL、标题、访问次数、访问时间等信息

**示例输出**:

```json
[
  {
    "url": "https://github.com/",
    "title": "GitHub",
    "visit_count": 15,
    "last_visit_time": "2025-12-11T10:30:45.123Z"
  },
  ...
]
```

### 5.2 火绒自动化测试

> ⚠️ **前提条件**: 需要已安装火绒安全软件

**测试命令**:

```
测试火绒软件 MCP 功能
```

**预期结果**:

1. 火绒安全软件自动启动
2. AI 助手返回启动成功信息,包含进程 PID

**示例输出**:

```
✅ 火绒启动成功,进程ID: 12345
```

### 5.3 HRKill 工具测试

> ⚠️ **前提条件**: 需要 HRKill 工具文件

**测试命令**:

```
测试 HRKill 工具启动功能
```

**预期结果**:

1. HRKill 工具自动启动
2. 显示 HRKill 主界面

### 5.4 Focus Pack 工具测试

**测试命令**:

```
测试 Focus_Pack 工具启动功能
```

**预期结果**:

1. Focus Pack 工具自动启动
2. 显示工具主界面

### 5.5 威胁情报查询测试

> ⚠️ **前提条件**: 需要已登录微步云平台

**测试命令**:

```
测试 IOC 威胁情报查询的浏览器访问功能
```

**预期结果**:

1. Chrome 浏览器自动启动
2. 自动访问微步云平台
3. 页面显示已登录状态

**完整查询测试**:

```
帮我查询 IP 地址 8.8.8.8 的威胁情报
```

**预期结果**:

1. 自动访问微步云平台
2. 查询指定 IP 的威胁情报
3. 截图保存查询结果
4. 返回结构化的威胁情报数据

### 5.6 综合场景测试

**测试命令**:

```
帮我分析这台主机的安全状况:
1. 提取 Chrome 浏览器最近 100 条历史记录
2. 检查是否访问过可疑网站
3. 如果发现可疑 IP,查询威胁情报
```

**预期结果**:

AI 助手会自动:
1. 调用浏览器取证功能
2. 分析历史记录中的 IP 和域名
3. 对可疑 IP 调用威胁情报查询
4. 生成综合分析报告

---

## 6. 常见问题

### 6.1 部署相关

#### Q1: uv 安装失败怎么办?

**A**:

1. 检查网络连接是否正常
2. 尝试使用代理:
   ```powershell
   $env:HTTPS_PROXY="http://proxy.example.com:8080"
   irm https://astral.sh/uv/install.ps1 | iex
   ```
3. 手动下载安装:访问 https://github.com/astral-sh/uv/releases

#### Q2: uv sync 依赖安装失败?

**A**:

常见原因和解决方案:

| 错误信息 | 原因 | 解决方案 |
|---------|------|---------|
| `Failed to download` | 网络问题 | 配置 PyPI 镜像源 |
| `Permission denied` | 权限不足 | 以管理员身份运行 |
| `Python version mismatch` | Python 版本过低 | 升级到 Python 3.13+ |

**配置 PyPI 镜像源**:

```powershell
# 使用清华镜像源
$env:UV_INDEX_URL="https://pypi.tuna.tsinghua.edu.cn/simple"
uv sync
```

#### Q3: 项目路径包含中文或空格怎么办?

**A**:

**不推荐**使用包含中文或空格的路径,可能导致各种问题。

如果必须使用,请在 MCP 配置中使用**双反斜杠**转义:

```json
"args": [
  "--directory",
  "D:\\用户文档\\MCPSecTrace\\"
]
```

### 6.2 MCP 服务器相关

#### Q4: MCP 服务器启动失败 (红色指示灯)?

**A**:

**诊断步骤**:

1. **检查路径配置**:
   ```json
   // 确保路径正确且使用正斜杠 / 或双反斜杠 \\
   "args": ["--directory", "D:/MCPSecTrace/"]
   ```

2. **手动测试服务器**:
   ```powershell
   cd D:\MCPSecTrace
   uv run python -m mcpsectrace.mcp_servers.browser_mcp
   ```

   如果出现错误,查看错误信息进行排查。

3. **检查 VSCode 是否以管理员身份运行**:
   - 右键 VSCode 图标 → 以管理员身份运行

4. **查看 Cline 日志**:
   - Cline 设置 → Advanced MCP Settings → View Logs

#### Q5: MCP 服务器超时 (timeout)?

**A**:

部分操作(如 GUI 自动化)可能需要较长时间,可以增加超时时间:

```json
{
  "mcpServers": {
    "huorong_mcp": {
      "timeout": 300,  // 增加到 5 分钟
      ...
    }
  }
}
```

#### Q6: Cline 调用 MCP 工具失败?

**A**:

1. **检查工具是否启用**:
   ```json
   "disabled": false  // 确保为 false
   ```

2. **检查 Auto-approve 设置**:
   - Cline 界面底部 → Auto-approve: ☑ Enabled

3. **手动测试命令**:
   ```powershell
   uv --directory D:/MCPSecTrace/ run python -m mcpsectrace.mcp_servers.browser_mcp
   ```

### 6.3 功能使用相关

#### Q7: 浏览器取证提示数据库被锁定?

**A**:

**原因**: 浏览器正在运行,数据库文件被占用。

**解决方案**:
1. 关闭所有 Chrome/Edge 浏览器进程
2. 重新执行取证命令

#### Q8: GUI 自动化无法识别界面元素?

**A**:

**可能原因**:

1. **屏幕分辨率或 DPI 设置不匹配**:
   - 截图模板基于 1920×1080 分辨率
   - 如果使用其他分辨率,需要重新截图

2. **界面语言不匹配**:
   - 默认截图基于中文界面
   - 英文界面需要重新制作截图模板

3. **图像识别置信度设置过高**:
   - 修改 [config/user_settings.toml](config/user_settings.toml):
     ```toml
     [performance]
     automation_confidence = 0.7  # 降低到 0.7 试试
     ```

4. **界面元素加载未完成**:
   - 增加等待时间:
     ```toml
     [performance]
     device_level = 1  # 使用更长的等待时间
     ```

**重新制作截图模板**:

```python
# 1. 手动打开目标软件
# 2. 进入目标界面
# 3. 运行截图脚本
python scripts/capture_ui_elements.py
```

#### Q9: 威胁情报查询提示未登录?

**A**:

**原因**: Chrome 用户数据目录配置不正确或会话已过期。

**解决方案**:

1. **重新登录微步云平台**:
   ```powershell
   # 使用配置的 Chrome 打开微步云平台
   & "D:\MCPTools\chrome-win64\chrome.exe" --user-data-dir="C:\Users\User\AppData\Local\Google\Chrome for Testing\User Data" https://x.threatbook.com
   ```

2. **登录后不要退出登录**,直接关闭浏览器即可保存会话

3. **重新测试 IOC 查询功能**

#### Q10: 火绒/HRKill 路径配置不正确?

**A**:

**使用 Everything 搜索工具自动查找**:

```powershell
cd D:\MCPSecTrace
uv run python scripts/find_tools.py
```

脚本会自动搜索系统中的工具,并输出配置路径。

或手动查找:

```powershell
# 查找火绒
Get-ChildItem -Path "C:\Program Files" -Recurse -Filter "HipsMain.exe" -ErrorAction SilentlyContinue

# 查找 HRKill
Get-ChildItem -Path "D:\" -Recurse -Filter "hrkill*.exe" -ErrorAction SilentlyContinue
```

### 6.4 性能优化

#### Q11: 工具执行速度太慢?

**A**:

1. **提升设备性能等级**:
   ```toml
   [performance]
   device_level = 3  # 高性能设备
   ```

2. **减少等待时间**:
   ```toml
   [performance]
   automation_timeout = 10  # 减少超时时间
   ioc_page_load_wait = 5   # 减少页面等待时间
   ```

3. **禁用不需要的功能**:
   ```toml
   [security]
   enable_screenshots = false  # 禁用自动截图
   ```

#### Q12: 内存占用过高?

**A**:

1. **限制浏览器取证的历史记录数量**:
   ```
   帮我提取 Chrome 最近 20 条历史记录  # 而不是 100 条
   ```

2. **及时关闭不需要的 MCP 服务器**:
   ```json
   "disabled": true  // 禁用不常用的服务
   ```

### 6.5 日志和调试

#### Q13: 如何查看详细的执行日志?

**A**:

1. **启用调试模式**:
   ```toml
   [app]
   environment = "dev"

   [mcp]
   log_level = "DEBUG"
   ```

2. **查看日志文件**:
   ```
   data/logs/
   ├── browser_mcp.log      # 浏览器取证日志
   ├── huorong_mcp.log      # 火绒自动化日志
   ├── ioc_mcp.log          # IOC查询日志
   └── ...
   ```

3. **Cline 日志**:
   - Cline 设置 → Advanced MCP Settings → View Logs

#### Q14: 如何报告问题?

**A**:

提交 Issue 时,请提供以下信息:

1. **系统信息**:
   - 操作系统版本
   - Python 版本 (`python --version`)
   - uv 版本 (`uv --version`)

2. **错误信息**:
   - 完整的错误堆栈
   - 相关日志文件

3. **复现步骤**:
   - 详细的操作步骤
   - 使用的命令或提示词

4. **配置文件**:
   - [config/user_settings.toml](config/user_settings.toml) (敏感信息请脱敏)
   - `cline_mcp_settings.json`

---

## 附录 A: 配置文件参考

### user_settings.toml 完整示例

```toml
[app]
name = "MCPSecTrace"
environment = "prod"  # dev/prod/test

[paths]
# Everything 搜索工具根目录
everything_root = "D:\\MCPTools\\Everything"

# 火绒安全软件主程序路径
huorong_exe = "C:\\Program Files (x86)\\Huorong\\ESEndpoint\\bin\\HipsMain.exe"

# HRKill 工具程序路径
hrkill_exe = "D:\\MCPTools\\hrkill-1.0.0.86.exe"

# Focus Pack 工具程序路径
focus_pack_exe = "D:\\MCPTools\\Focus_Pack.exe"

# Chrome 浏览器程序路径
chrome_exe = "D:\\MCPTools\\chrome-win64\\chrome.exe"

# ChromeDriver 程序路径
chromedriver_exe = "D:\\MCPTools\\chromedriver-win64\\chromedriver.exe"

# Chrome 用户数据目录
chrome_user_data_dir = "C:\\Users\\User\\AppData\\Local\\Google\\Chrome for Testing\\User Data"

[images]
base_dir = "./assets/screenshots"
huorong_dir = "huorong"
hrkill_dir = "hrkill"
focus_pack_dir = "focus_pack"

[output]
logs_dir = "data/logs"
ioc_html_dir = "data/logs/ioc"
ioc_pics_dir = "data/logs/ioc/ioc_pic"

[performance]
device_level = 2                  # 1=低配 2=中配 3=高配
network_timeout = 30              # 网络请求超时(秒)
automation_confidence = 0.8       # 图像识别置信度(0.1-1.0)
automation_timeout = 15           # 自动化查找超时(秒)
ioc_page_load_wait = 10           # IOC页面加载等待(秒)

[security]
threatbook_api_key = ""           # 微步在线API密钥(可选)
enable_screenshots = true         # 是否启用自动截图
auto_open_reports = true          # 是否自动打开报告目录

[mcp]
log_level = "ERROR"               # DEBUG/INFO/WARNING/ERROR
browser_port = 8801
huorong_port = 8802
hrkill_port = 8803
focus_pack_port = 8804
ioc_port = 8805
```

---

## 附录 B: MCP 配置文件参考

### cline_mcp_settings.json 完整示例

```json
{
  "mcpServers": {
    "browser_mcp": {
      "disabled": false,
      "timeout": 60,
      "type": "stdio",
      "command": "uv",
      "args": [
        "--directory",
        "D:/MCPSecTrace/",
        "run",
        "python",
        "-m",
        "mcpsectrace.mcp_servers.browser_mcp"
      ]
    },
    "huorong_mcp": {
      "disabled": false,
      "timeout": 120,
      "type": "stdio",
      "command": "uv",
      "args": [
        "--directory",
        "D:/MCPSecTrace/",
        "run",
        "python",
        "-m",
        "mcpsectrace.mcp_servers.huorong_mcp"
      ]
    },
    "hrkill_mcp": {
      "disabled": false,
      "timeout": 120,
      "type": "stdio",
      "command": "uv",
      "args": [
        "--directory",
        "D:/MCPSecTrace/",
        "run",
        "python",
        "-m",
        "mcpsectrace.mcp_servers.hrkill_mcp"
      ]
    },
    "focus_pack_mcp": {
      "disabled": false,
      "timeout": 120,
      "type": "stdio",
      "command": "uv",
      "args": [
        "--directory",
        "D:/MCPSecTrace/",
        "run",
        "python",
        "-m",
        "mcpsectrace.mcp_servers.focus_pack_mcp"
      ]
    },
    "ioc_mcp": {
      "disabled": false,
      "timeout": 180,
      "type": "stdio",
      "command": "uv",
      "args": [
        "--directory",
        "D:/MCPSecTrace/",
        "run",
        "python",
        "-m",
        "mcpsectrace.mcp_servers.ioc_mcp"
      ]
    },
    "winlog_mcp": {
      "disabled": false,
      "timeout": 60,
      "type": "stdio",
      "command": "uv",
      "args": [
        "--directory",
        "D:/MCPSecTrace/external_mcp/winlog-mcp/",
        "run",
        "python",
        "src/main.py",
        "--storage-path",
        "D:/MCPSecTrace/data/logs/"
      ]
    }
  }
}
```

---

## 附录 C: AI 提示词参考

### 浏览器取证

```
# 基础取证
帮我提取 Chrome 浏览器的历史记录

# 指定数量
帮我提取 Chrome 最近 100 条历史记录

# 分析可疑访问
分析 Chrome 历史记录中是否有访问恶意网站的记录

# 导出结果
提取 Chrome 历史记录并保存为 CSV 文件
```

### 威胁情报查询

```
# IP 查询
查询 IP 地址 8.8.8.8 的威胁情报

# 批量查询
查询以下 IP 的威胁情报: 1.1.1.1, 8.8.8.8, 114.114.114.114

# 域名查询
查询域名 example.com 的威胁情报

# 文件哈希查询
查询文件哈希 d41d8cd98f00b204e9800998ecf8427e 的威胁情报
```

### 安全工具自动化

```
# 启动工具
启动火绒安全软件

# 执行扫描
使用火绒扫描 C:\Users\Public 目录

# 导出日志
导出火绒的安全日志
```

### 综合分析

```
# 失陷主机分析
帮我分析这台主机是否失陷:
1. 提取浏览器历史记录
2. 检查是否访问过恶意网站
3. 查询可疑 IP 的威胁情报
4. 生成溯源报告

# 应急响应
协助我对主机 192.168.1.100 进行应急响应:
1. 启动 HRKill 工具进行病毒查杀
2. 使用 Focus Pack 收集系统信息
3. 分析浏览器历史是否有异常访问
4. 生成应急响应报告
```

---

## 附录 D: 更新日志

### v2.0 (2025-12-11)

- ✨ 重写部署指南,简化部署流程
- ✨ 新增详细的架构说明和原理介绍
- ✨ 新增完整的常见问题解答
- ✨ 新增 AI 提示词参考
- 🔧 优化配置文件示例
- 📝 完善测试流程说明

### v1.0 (2025-09-17)

- 🎉 初始版本发布
- 📝 基础部署流程说明
- 🔧 基础配置指导

---

## 附录 E: 获取帮助

### 技术支持

- 📧 **Email**: support@mcpsectrace.example.com
- 💬 **Issue**: https://github.com/your-org/MCPSecTrace/issues
- 📖 **文档**: https://docs.mcpsectrace.example.com

### 参考资源

- [MCP 官方文档](https://modelcontextprotocol.io/)
- [Cline 插件文档](https://github.com/cline/cline)
- [PyAutoGUI 文档](https://pyautogui.readthedocs.io/)
- [Selenium 文档](https://selenium-python.readthedocs.io/)

---

**文档结束**

> 💡 **提示**: 本文档会持续更新,请定期查看最新版本。
> 📅 **最后更新**: 2025年12月11日
