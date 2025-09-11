# MCPSecTrace 配置系统说明

MCPSecTrace 采用分层TOML配置系统，支持灵活的配置管理和用户自定义。

## 配置层次结构

```
config/
├── defaults/           # 系统默认配置（升级时会被覆盖）
│   ├── base.toml      # 基础系统配置
│   ├── browser.toml   # 浏览器取证配置
│   ├── automation.toml # GUI自动化配置  
│   └── ioc.toml       # 威胁情报查询配置
├── custom/            # 用户自定义默认配置（升级时保留）
│   └── README.md      # 使用说明
└── user_settings.toml # 用户核心配置（升级时保留）
```

## 配置优先级

**用户核心配置 > 自定义默认配置 > 系统默认配置**

系统会自动合并所有配置，高优先级的配置会覆盖低优先级的相同配置项。

## 核心用户配置 (user_settings.toml)

这是最重要的配置文件，包含用户最常需要修改的设置：

```toml
# 设备性能等级：1=低性能 2=中性能 3=高性能
device_level = 2

# 调试模式开关
debug_mode = false

# 输出路径配置
output_path = "./logs/ioc"
screenshot_path = "./logs/ioc/ioc_pic"

# Chrome浏览器配置
[chrome]
exe_path = ""           # Chrome可执行文件路径（可选）
driver_path = ""        # ChromeDriver路径（可选）  
user_data_dir = ""      # Chrome用户数据目录（可选）
```

## 配置文件说明

### base.toml - 基础系统配置
- 系统编码、临时目录
- 支持的操作系统
- 输出格式配置
- MCP服务默认设置

### browser.toml - 浏览器取证配置
- 历史记录和下载记录查询数量
- SQL查询模板
- 浏览器数据库路径模式
- 时间戳转换设置

### automation.toml - GUI自动化配置
- 操作重试次数和超时时间
- 图像识别置信度
- 等待时间基数（会根据device_level调整）
- 各工具的图像文件路径映射

### ioc.toml - 威胁情报查询配置
- 浏览器窗口尺寸和启动选项
- 页面等待时间配置
- CSS选择器配置
- 查询URL模板
- 文件名特殊字符替换规则

## 使用方法

### 1. 修改核心配置
直接编辑 `config/user_settings.toml`：

```toml
# 提升设备性能等级加快执行速度
device_level = 3

# 启用调试模式查看详细日志
debug_mode = true

# 自定义输出路径
output_path = "D:/security_logs"
```

### 2. 自定义默认配置
如需修改更多技术参数：

```bash
# 复制默认配置到自定义目录
cp config/defaults/browser.toml config/custom/browser.toml

# 编辑自定义配置
# 修改 config/custom/browser.toml 中的参数
```

### 3. 在代码中使用配置

```python
from mcpsectrace.config import get_config_value

# 获取配置值，支持点号路径和默认值
max_items = get_config_value("browser.max_history_items", default=100)
device_level = get_config_value("device_level", default=2)
window_size = get_config_value("ioc.window_size", default=[1920, 1200])

# 获取完整配置模块
browser_config = get_config("browser")
```

## 配置项说明

### 设备性能等级 (device_level)
影响所有等待时间的倍数：
- `1`: 低性能设备（等待时间 × 1）
- `2`: 中性能设备（等待时间 × 2）  
- `3`: 高性能设备（等待时间 × 3）

### 调试模式 (debug_mode)
- `true`: 输出详细调试信息到stderr
- `false`: 仅输出到日志文件

### 路径配置
所有路径支持相对路径和绝对路径：
- 相对路径：基于项目根目录
- 绝对路径：直接使用指定路径
- 空字符串：使用系统默认（如PATH中的工具）

## 升级兼容性

- **系统默认配置** (`config/defaults/`): 升级时会被覆盖，不要直接修改
- **自定义配置** (`config/custom/`): 升级时保留，安全的自定义位置  
- **用户核心配置** (`user_settings.toml`): 升级时保留，最重要的配置

## 故障排除

### 配置未生效
1. 检查配置文件语法是否正确（TOML格式）
2. 确认配置项路径是否正确（如 `browser.max_history_items`）
3. 重启应用程序使配置生效

### 找不到配置文件
配置系统会自动查找项目根目录（包含pyproject.toml的目录），确保从正确的目录启动程序。

### 图像识别失败
检查 `automation.toml` 中的图像文件路径是否正确，确保图像文件存在。

## 配置示例

查看 `src/mcpsectrace/config/examples.py` 获取详细的配置使用示例。