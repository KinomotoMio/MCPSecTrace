# MCPSecTrace 架构图 - Mermaid 版本

本文档包含《MCPSecTrace部署运维指南》中所有图表的 Mermaid 代码。

---

## 1. 整体架构图

```mermaid
flowchart TB
    subgraph AI["AI 助手层 (Cline)"]
        AI_Client[AI 客户端<br/>通过 MCP 协议与工具层交互]
    end

    subgraph MCP["MCP 服务器层"]
        Browser[browser_mcp<br/>浏览器取证]
        Huorong[huorong_mcp<br/>火绒自动化]
        HRKill[hrkill_mcp<br/>HRKill自动化]
        FocusPack[focus_pack_mcp<br/>应急工具自动化]
        IOC[ioc_mcp<br/>威胁情报查询]
        WinLog[winlog_mcp<br/>Windows日志分析]
    end

    subgraph Core["核心功能层"]
        BrowserCore[browser_forensics<br/>浏览器取证核心]
        SysmonCore[sysmon_collector<br/>Sysmon日志收集]
        AutoCore[automation<br/>GUI自动化基类]
    end

    subgraph External["外部工具和数据源"]
        Tool1[火绒安全]
        Tool2[HRKill]
        Tool3[Focus Pack]
        Tool4[微步在线]
        Tool5[Sysmon]
    end

    AI_Client <-->|MCP 协议<br/>JSON-RPC| Browser
    AI_Client <-->|MCP 协议<br/>JSON-RPC| Huorong
    AI_Client <-->|MCP 协议<br/>JSON-RPC| HRKill
    AI_Client <-->|MCP 协议<br/>JSON-RPC| FocusPack
    AI_Client <-->|MCP 协议<br/>JSON-RPC| IOC
    AI_Client <-->|MCP 协议<br/>JSON-RPC| WinLog

    Browser -->|Python API| BrowserCore
    Huorong -->|Python API| AutoCore
    HRKill -->|Python API| AutoCore
    FocusPack -->|Python API| AutoCore
    IOC -->|Python API| BrowserCore
    WinLog -->|Python API| SysmonCore

    AutoCore --> Tool1
    AutoCore --> Tool2
    AutoCore --> Tool3
    BrowserCore --> Tool4
    SysmonCore --> Tool5

    style AI fill:#e1f5ff
    style MCP fill:#fff4e1
    style Core fill:#f0f0f0
    style External fill:#e8f5e9
```

---

## 2. MCP 通信流程图

```mermaid
sequenceDiagram
    participant AI as AI 助手<br/>(Cline)
    participant MCP as MCP<br/>服务器
    participant Tool as 安全<br/>工具

    Note over AI,Tool: 1. 发现可用工具
    AI->>MCP: discover
    MCP-->>AI: tool_list

    Note over AI,Tool: 2. 调用工具
    AI->>MCP: call_tool(params)

    Note over MCP,Tool: 3. 执行实际操作
    MCP->>Tool: 执行操作
    Tool-->>MCP: result

    MCP-->>AI: result
```

---

## 3. 浏览器取证流程图

```mermaid
flowchart TD
    Start([开始浏览器取证]) --> Check{检测浏览器<br/>进程是否运行}
    Check -->|运行中| Warn[警告: 建议关闭浏览器]
    Check -->|已关闭| Copy[复制数据库文件<br/>避免文件锁定]
    Warn --> Copy

    Copy --> Connect[连接临时数据库]
    Connect --> Query[执行 SQL 查询<br/>提取历史记录]

    Query --> Parse[解析查询结果]
    Parse --> Convert[转换时间戳格式<br/>Chrome: 1601-01-01 起<br/>Firefox: 1970-01-01 起]

    Convert --> Format[格式化为 JSON]
    Format --> Return([返回结果])

    style Start fill:#e1f5ff
    style Return fill:#e1f5ff
    style Warn fill:#fff3cd
```

---

## 4. GUI 自动化流程图

```mermaid
flowchart TD
    Start([开始 GUI 自动化]) --> Launch[启动目标程序<br/>subprocess.Popen]

    Launch --> Wait1[等待界面加载<br/>time.sleep]

    Wait1 --> Locate[图像识别定位元素<br/>pyautogui.locateOnScreen]

    Locate --> Found{找到元素?}
    Found -->|是| Click[模拟点击操作<br/>pyautogui.click]
    Found -->|否| Timeout{超时?}

    Timeout -->|是| Error([返回错误])
    Timeout -->|否| Wait2[等待一段时间]
    Wait2 --> Locate

    Click --> Wait3[等待操作完成<br/>等待下一个界面元素]

    Wait3 --> More{还有更多<br/>操作?}
    More -->|是| Locate
    More -->|否| Success([返回成功])

    style Start fill:#e1f5ff
    style Success fill:#d4edda
    style Error fill:#f8d7da
```

---

## 5. 威胁情报查询流程图

```mermaid
flowchart TD
    Start([开始 IOC 查询]) --> Init[启动 Chrome 浏览器<br/>使用已登录的 Profile]

    Init --> Navigate[访问威胁情报平台<br/>threatbook.com]

    Navigate --> Wait[等待页面加载<br/>WebDriverWait]

    Wait --> CheckLogin{检查登录<br/>状态}
    CheckLogin -->|未登录| LoginError([返回错误:<br/>需要登录])
    CheckLogin -->|已登录| Extract[提取威胁情报数据<br/>threat_score, tags]

    Extract --> Screenshot[截图保存<br/>driver.save_screenshot]

    Screenshot --> Generate[生成结构化报告<br/>JSON 格式]

    Generate --> Close[关闭浏览器]
    Close --> Return([返回报告])

    style Start fill:#e1f5ff
    style Return fill:#d4edda
    style LoginError fill:#f8d7da
```

---

## 6. 部署流程图

```mermaid
flowchart TD
    Start([开始部署]) --> Choice{选择部署方式}

    Choice -->|方式一| OneClick[一键部署脚本<br/>即将推出]
    Choice -->|方式二| Manual[手动部署]

    OneClick --> AutoInstall[自动安装环境<br/>Python, uv, 依赖]
    AutoInstall --> AutoConfig[自动配置<br/>工具路径, MCP]
    AutoConfig --> AutoTest[自动测试验证]
    AutoTest --> VSCode

    Manual --> InstallUV[安装 uv 包管理器]
    InstallUV --> Extract[解压项目文件<br/>MCPSecTrace + MCPTools]
    Extract --> InstallDeps[安装项目依赖<br/>uv sync]
    InstallDeps --> ConfigPath[配置工具路径<br/>user_settings.toml]
    ConfigPath --> TestDeploy[验证部署<br/>deployment_test.py]
    TestDeploy --> VSCode

    VSCode[配置 VSCode + Cline]
    VSCode --> InstallVSCode[安装 VSCode]
    InstallVSCode --> InstallCline[安装 Cline 插件]
    InstallCline --> ConfigAPI[配置 API<br/>DeepSeek]
    ConfigAPI --> ConfigMCP[配置 MCP 服务器<br/>cline_mcp_settings.json]
    ConfigMCP --> TestAI[测试 AI 助手]
    TestAI --> Done([部署完成])

    style Start fill:#e1f5ff
    style Done fill:#d4edda
    style OneClick fill:#fff3cd
```

---

## 7. 功能测试流程图

```mermaid
flowchart TD
    Start([开始功能测试]) --> Test1[浏览器取证测试]

    Test1 --> Check1{测试通过?}
    Check1 -->|是| Test2[火绒自动化测试]
    Check1 -->|否| Fix1[排查问题:<br/>浏览器进程<br/>数据库路径]
    Fix1 --> Test1

    Test2 --> Check2{测试通过?}
    Check2 -->|是| Test3[HRKill 工具测试]
    Check2 -->|否| Fix2[排查问题:<br/>火绒路径<br/>管理员权限]
    Fix2 --> Test2

    Test3 --> Check3{测试通过?}
    Check3 -->|是| Test4[Focus Pack 测试]
    Check3 -->|否| Fix3[排查问题:<br/>HRKill 路径<br/>截图模板]
    Fix3 --> Test3

    Test4 --> Check4{测试通过?}
    Check4 -->|是| Test5[威胁情报查询测试]
    Check4 -->|否| Fix4[排查问题:<br/>Focus Pack 路径]
    Fix4 --> Test4

    Test5 --> Check5{测试通过?}
    Check5 -->|是| Test6[综合场景测试]
    Check5 -->|否| Fix5[排查问题:<br/>登录状态<br/>Chrome 配置]
    Fix5 --> Test5

    Test6 --> Check6{测试通过?}
    Check6 -->|是| Complete([所有测试通过<br/>可以正式使用])
    Check6 -->|否| Fix6[排查综合问题]
    Fix6 --> Test6

    style Start fill:#e1f5ff
    style Complete fill:#d4edda
    style Fix1 fill:#fff3cd
    style Fix2 fill:#fff3cd
    style Fix3 fill:#fff3cd
    style Fix4 fill:#fff3cd
    style Fix5 fill:#fff3cd
    style Fix6 fill:#fff3cd
```

---

## 8. 问题诊断流程图

```mermaid
flowchart TD
    Problem([遇到问题]) --> Category{问题类型}

    Category -->|部署相关| Deploy
    Category -->|MCP服务器| MCP
    Category -->|功能使用| Function
    Category -->|性能问题| Performance

    Deploy[部署问题]
    Deploy --> D1{uv 安装失败?}
    D1 -->|是| D1S[检查网络<br/>使用代理<br/>手动下载]
    D1 -->|否| D2{依赖安装失败?}
    D2 -->|是| D2S[配置镜像源<br/>管理员权限<br/>检查 Python 版本]
    D2 -->|否| D3{路径问题?}
    D3 -->|是| D3S[避免中文空格<br/>使用双反斜杠]

    MCP[MCP服务器问题]
    MCP --> M1{启动失败?}
    M1 -->|是| M1S[检查路径配置<br/>手动测试<br/>管理员权限<br/>查看日志]
    M1 -->|否| M2{超时?}
    M2 -->|是| M2S[增加超时时间<br/>timeout: 300]
    M2 -->|否| M3{调用失败?}
    M3 -->|是| M3S[检查 disabled<br/>启用 Auto-approve<br/>手动测试命令]

    Function[功能使用问题]
    Function --> F1{数据库锁定?}
    F1 -->|是| F1S[关闭浏览器进程]
    F1 -->|否| F2{GUI识别失败?}
    F2 -->|是| F2S[检查分辨率<br/>检查语言<br/>降低置信度<br/>重做截图模板]
    F2 -->|否| F3{未登录?}
    F3 -->|是| F3S[重新登录<br/>检查 user_data_dir]

    Performance[性能问题]
    Performance --> P1{执行太慢?}
    P1 -->|是| P1S[提升 device_level<br/>减少等待时间<br/>禁用截图]
    P1 -->|否| P2{内存占用高?}
    P2 -->|是| P2S[限制记录数量<br/>禁用不用的服务]

    D1S --> Resolve([问题解决])
    D2S --> Resolve
    D3S --> Resolve
    M1S --> Resolve
    M2S --> Resolve
    M3S --> Resolve
    F1S --> Resolve
    F2S --> Resolve
    F3S --> Resolve
    P1S --> Resolve
    P2S --> Resolve

    style Problem fill:#f8d7da
    style Resolve fill:#d4edda
```

---

## 9. 数据流图 - 浏览器取证

```mermaid
flowchart LR
    User[用户] -->|自然语言指令| AI[AI 助手]
    AI -->|MCP 调用| BrowserMCP[browser_mcp]
    BrowserMCP -->|Python 调用| CoreModule[browser_forensics]

    CoreModule -->|读取| DB1[(Chrome<br/>History DB)]
    CoreModule -->|读取| DB2[(Edge<br/>History DB)]
    CoreModule -->|读取| DB3[(Firefox<br/>places.sqlite)]

    CoreModule -->|SQL 查询| Query[历史记录数据]
    Query -->|时间戳转换| Processed[处理后数据]
    Processed -->|JSON 格式化| Result[取证结果]

    Result -->|返回| BrowserMCP
    BrowserMCP -->|返回| AI
    AI -->|展示| User

    style User fill:#e1f5ff
    style AI fill:#fff4e1
    style Result fill:#d4edda
```

---

## 10. 数据流图 - 威胁情报查询

```mermaid
flowchart LR
    User[用户] -->|IOC 查询请求| AI[AI 助手]
    AI -->|MCP 调用| IOCMCP[ioc_mcp]
    IOCMCP -->|Selenium 启动| Chrome[Chrome<br/>浏览器]

    Chrome -->|HTTP 请求| ThreatBook[微步在线<br/>威胁情报平台]
    ThreatBook -->|返回页面| Chrome

    Chrome -->|页面解析| Parser[数据提取器]
    Parser -->|提取| Score[威胁评分]
    Parser -->|提取| Tags[威胁标签]
    Parser -->|提取| Info[详细信息]

    Chrome -->|截图| Screenshot[IOC 截图]

    Score -->|汇总| Report[威胁情报报告]
    Tags -->|汇总| Report
    Info -->|汇总| Report
    Screenshot -->|附加| Report

    Report -->|返回| IOCMCP
    IOCMCP -->|返回| AI
    AI -->|展示| User

    style User fill:#e1f5ff
    style AI fill:#fff4e1
    style ThreatBook fill:#f0f0f0
    style Report fill:#d4edda
```

---

## 11. 配置文件层次结构

```mermaid
flowchart TD
    Config[配置系统]

    Config --> Layer1[用户核心配置<br/>user_settings.toml<br/>优先级: 最高]
    Config --> Layer2[自定义默认配置<br/>config/custom/*.toml<br/>优先级: 中]
    Config --> Layer3[系统默认配置<br/>config/defaults/*.toml<br/>优先级: 最低]

    Layer1 --> Merge[配置合并引擎]
    Layer2 --> Merge
    Layer3 --> Merge

    Merge --> Final[最终配置]

    Final --> App[应用程序使用]

    Layer3 -.->|升级时覆盖| Update[系统升级]
    Layer2 -.->|升级时保留| Update
    Layer1 -.->|升级时保留| Update

    style Layer1 fill:#d4edda
    style Layer2 fill:#fff3cd
    style Layer3 fill:#f0f0f0
    style Final fill:#e1f5ff
```

---

## 12. MCP 服务器启动流程

```mermaid
flowchart TD
    Start([启动 MCP 服务器管理器]) --> LoadConfig[加载服务器配置列表]

    LoadConfig --> Loop{遍历服务器列表}

    Loop -->|有下一个| CheckPath{检查脚本<br/>是否存在?}
    Loop -->|结束| Summary[显示启动摘要]

    CheckPath -->|存在| StartServer[启动服务器进程<br/>subprocess.Popen]
    CheckPath -->|不存在| Skip[跳过该服务器<br/>显示警告]

    StartServer --> WaitStart[等待1秒<br/>让服务器启动]

    WaitStart --> CheckStatus{检查进程<br/>状态}

    CheckStatus -->|运行中| Success[✓ 启动成功<br/>记录 PID]
    CheckStatus -->|已退出| Failed[✗ 启动失败<br/>显示错误]

    Success --> Loop
    Failed --> Loop
    Skip --> Loop

    Summary --> Monitor[监控运行<br/>等待 Ctrl+C]

    Monitor --> Interrupt{收到中断<br/>信号?}
    Interrupt -->|否| Monitor
    Interrupt -->|是| StopAll[停止所有服务器]

    StopAll --> Terminate[依次终止进程<br/>terminate + wait]
    Terminate --> Cleanup[清理资源]
    Cleanup --> End([所有服务器已停止])

    style Start fill:#e1f5ff
    style Success fill:#d4edda
    style Failed fill:#f8d7da
    style End fill:#e1f5ff
```

---

## 使用说明

### 如何在 Markdown 中使用这些图表

1. **复制对应的 Mermaid 代码块**
2. **粘贴到 Markdown 文件中**
3. **确保使用 ` ```mermaid ` 代码块包裹**

### 支持的平台

- ✅ GitHub (原生支持)
- ✅ GitLab (原生支持)
- ✅ VSCode (需安装 Mermaid 预览插件)
- ✅ Typora (原生支持)
- ✅ Obsidian (原生支持)
- ✅ Notion (部分支持)

### 在线编辑器

如需调整图表,可使用:
- https://mermaid.live/ - 官方在线编辑器
- https://mermaid-js.github.io/mermaid-live-editor/ - 实时预览

---

## 图表索引

| 编号 | 图表名称 | 所在章节 | 类型 |
|------|---------|---------|------|
| 1 | 整体架构图 | 2.1 | flowchart |
| 2 | MCP 通信流程图 | 3.1 | sequenceDiagram |
| 3 | 浏览器取证流程图 | 3.2 | flowchart |
| 4 | GUI 自动化流程图 | 3.3 | flowchart |
| 5 | 威胁情报查询流程图 | 3.4 | flowchart |
| 6 | 部署流程图 | 4.2 | flowchart |
| 7 | 功能测试流程图 | 5 | flowchart |
| 8 | 问题诊断流程图 | 6 | flowchart |
| 9 | 数据流图 - 浏览器取证 | - | flowchart |
| 10 | 数据流图 - 威胁情报查询 | - | flowchart |
| 11 | 配置文件层次结构 | - | flowchart |
| 12 | MCP 服务器启动流程 | - | flowchart |

---

**文档版本**: 1.0
**创建日期**: 2025年12月11日
