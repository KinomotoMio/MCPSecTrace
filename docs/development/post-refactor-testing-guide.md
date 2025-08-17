# 重构后代码测试指南

本文档为MCPSecTrace项目重构后提供系统性的测试方法，确保新的模块化架构正常工作。

## 📋 目录

- [快速验证清单](#快速验证清单)
- [环境配置测试](#环境配置测试)
- [模块导入测试](#模块导入测试)
- [核心功能测试](#核心功能测试)
- [MCP服务器测试](#mcp服务器测试)
- [GUI自动化测试](#gui自动化测试)
- [集成测试](#集成测试)
- [性能和兼容性测试](#性能和兼容性测试)
- [文档和工具验证](#文档和工具验证)

## ⚡ 快速验证清单

首次重构后必须验证的关键项目：

```bash
# 1. 依赖安装验证
uv sync

# 2. 基本导入测试
python -c "import src.mcpsectrace; print('✅ 模块导入成功')"

# 3. 命令行工具验证
python scripts/run_browser_forensics.py --help

# 4. 项目结构检查
find src/ -name "*.py" -exec python -m py_compile {} \;

# 5. 代码格式检查
uv run black --check src/
uv run isort --check-only src/
```

**期望结果：** 所有命令无错误执行

## 🔧 环境配置测试

### 1. 依赖管理验证

```bash
# 检查虚拟环境状态
uv --version

# 安装项目依赖
uv sync

# 验证关键依赖
python -c "
import cv2, pyautogui, pydantic, httpx
print('✅ 核心依赖导入成功')
print(f'OpenCV: {cv2.__version__}')
print(f'PyAutoGUI: {pyautogui.__version__}')
"

# 安装开发依赖
uv sync --extra dev

# 验证开发工具
uv run black --version
uv run mypy --version
uv run pytest --version
```

### 2. 项目配置验证

```bash
# 检查pyproject.toml语法
python -c "
import tomllib
with open('pyproject.toml', 'rb') as f:
    config = tomllib.load(f)
print('✅ pyproject.toml 配置有效')
print(f'项目名: {config[\"project\"][\"name\"]}')
print(f'版本: {config[\"project\"][\"version\"]}')
"

# 验证命令行入口点
pip show mcpsectrace 2>/dev/null || echo "⚠️ 需要安装项目包: pip install -e ."
```

### 3. 目录结构验证

```bash
# 检查必要目录是否存在
for dir in src/mcpsectrace/{core,automation,mcp_servers,utils} \
           external_mcp scripts tests docs/development \
           assets/screenshots tools config data; do
    if [ -d "$dir" ]; then
        echo "✅ $dir"
    else
        echo "❌ 缺少目录: $dir"
    fi
done

# 验证__init__.py文件
find src/ -type d -exec test -f {}/__init__.py \; -print | \
while read dir; do
    echo "✅ $dir/__init__.py"
done
```

## 📦 模块导入测试

### 1. 基础模块测试

```python
# tests/integration/test_imports.py
"""验证所有模块的导入功能"""

def test_core_modules():
    """测试核心模块导入"""
    try:
        from src.mcpsectrace.core import browser_forensics
        from src.mcpsectrace.core import sysmon_collector
        from src.mcpsectrace.core import base_automation
        print("✅ 核心模块导入成功")
    except ImportError as e:
        print(f"❌ 核心模块导入失败: {e}")

def test_automation_modules():
    """测试自动化模块导入"""
    try:
        from src.mcpsectrace.automation import huorong
        from src.mcpsectrace.automation import hrkill
        from src.mcpsectrace.automation import focus_pack
        print("✅ 自动化模块导入成功")
    except ImportError as e:
        print(f"❌ 自动化模块导入失败: {e}")

def test_mcp_modules():
    """测试MCP服务器模块导入"""
    try:
        from src.mcpsectrace.mcp_servers import browser_mcp
        from src.mcpsectrace.mcp_servers import huorong_mcp
        from src.mcpsectrace.mcp_servers import hrkill_mcp
        from src.mcpsectrace.mcp_servers import focus_pack_mcp
        print("✅ MCP服务器模块导入成功")
    except ImportError as e:
        print(f"❌ MCP服务器模块导入失败: {e}")

def test_utils_modules():
    """测试工具模块导入"""
    try:
        from src.mcpsectrace.utils import logging_setup
        from src.mcpsectrace.utils import image_recognition
        print("✅ 工具模块导入成功")
    except ImportError as e:
        print(f"❌ 工具模块导入失败: {e}")

if __name__ == "__main__":
    test_core_modules()
    test_automation_modules()
    test_mcp_modules()
    test_utils_modules()
```

### 2. 循环导入检查

```python
# tests/integration/test_circular_imports.py  
"""检查循环导入问题"""

import sys
import importlib

def check_circular_imports():
    """检查是否存在循环导入"""
    modules_to_test = [
        'src.mcpsectrace.core.browser_forensics',
        'src.mcpsectrace.core.sysmon_collector',
        'src.mcpsectrace.automation.huorong',
        'src.mcpsectrace.automation.hrkill',
        'src.mcpsectrace.automation.focus_pack',
        'src.mcpsectrace.utils.logging_setup',
        'src.mcpsectrace.utils.image_recognition',
    ]
    
    for module_name in modules_to_test:
        try:
            # 清除模块缓存
            if module_name in sys.modules:
                del sys.modules[module_name]
            
            # 重新导入
            module = importlib.import_module(module_name)
            print(f"✅ {module_name}")
        except Exception as e:
            print(f"❌ {module_name}: {e}")

if __name__ == "__main__":
    check_circular_imports()
```

## 🔍 核心功能测试

### 1. 浏览器取证功能测试

```python
# tests/unit/test_browser_forensics.py
"""测试浏览器取证功能"""

def test_browser_forensics():
    """测试浏览器取证基本功能"""
    from src.mcpsectrace.core.browser_forensics import main
    
    # 创建测试参数
    import sys
    original_argv = sys.argv[:]
    
    try:
        # 模拟命令行参数（只测试帮助信息）
        sys.argv = ['browser_forensics.py', '--help']
        
        # 这里可能会抛出SystemExit，这是正常的
        try:
            main()
        except SystemExit:
            pass
        
        print("✅ 浏览器取证模块基础功能正常")
    except Exception as e:
        print(f"❌ 浏览器取证模块测试失败: {e}")
    finally:
        sys.argv = original_argv

if __name__ == "__main__":
    test_browser_forensics()
```

### 2. 基础工具类测试

```python
# tests/unit/test_utils.py
"""测试工具类功能"""

def test_logging_setup():
    """测试日志配置功能"""
    from src.mcpsectrace.utils.logging_setup import setup_logger
    
    try:
        logger = setup_logger("test_logger")
        logger.info("测试日志消息")
        print("✅ 日志配置功能正常")
    except Exception as e:
        print(f"❌ 日志配置测试失败: {e}")

def test_image_recognition():
    """测试图像识别类基础功能"""
    from src.mcpsectrace.utils.image_recognition import ImageRecognition
    
    try:
        img_rec = ImageRecognition()
        # 只测试类初始化
        print("✅ 图像识别类初始化正常")
    except Exception as e:
        print(f"❌ 图像识别类测试失败: {e}")

if __name__ == "__main__":
    test_logging_setup()
    test_image_recognition()
```

## 🔗 MCP服务器测试

### 1. MCP服务器启动测试

```python
# tests/integration/test_mcp_servers.py
"""测试MCP服务器基础功能"""

import subprocess
import time
import signal
import os

def test_mcp_server_startup():
    """测试MCP服务器启动"""
    mcp_servers = [
        'src/mcpsectrace/mcp_servers/browser_mcp.py',
        'src/mcpsectrace/mcp_servers/huorong_mcp.py',
        'src/mcpsectrace/mcp_servers/hrkill_mcp.py',
        'src/mcpsectrace/mcp_servers/focus_pack_mcp.py',
    ]
    
    for server_path in mcp_servers:
        try:
            # 启动服务器进程
            process = subprocess.Popen(
                ['python', server_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # 等待一秒钟
            time.sleep(1)
            
            # 检查进程是否还在运行
            if process.poll() is None:
                print(f"✅ {server_path} 启动成功")
                # 终止进程
                process.terminate()
                process.wait(timeout=5)
            else:
                stdout, stderr = process.communicate()
                print(f"❌ {server_path} 启动失败")
                if stderr:
                    print(f"错误: {stderr.decode()}")
                    
        except Exception as e:
            print(f"❌ {server_path} 测试异常: {e}")

if __name__ == "__main__":
    test_mcp_server_startup()
```

### 2. 批量启动脚本测试

```bash
# 测试MCP服务器批量启动脚本（在scripts/test_all.sh中）
timeout 10 python scripts/start_mcp_servers.py &
SERVER_PID=$!

sleep 5

if kill -0 $SERVER_PID 2>/dev/null; then
    echo "✅ MCP服务器批量启动脚本正常工作"
    kill $SERVER_PID
else
    echo "❌ MCP服务器批量启动脚本测试失败"
fi
```

## 🖱️ GUI自动化测试

### 1. 图像识别测试

```python
# test_gui_automation.py
"""测试GUI自动化功能（不需要实际GUI）"""

def test_image_assets():
    """验证GUI自动化所需的图像资源"""
    import os
    
    tools = ['huorong', 'hrkill', 'focus_pack']
    base_path = 'assets/screenshots'
    
    for tool in tools:
        tool_path = os.path.join(base_path, tool)
        if os.path.exists(tool_path):
            images = [f for f in os.listdir(tool_path) if f.endswith('.png')]
            print(f"✅ {tool}: {len(images)} 个截图文件")
        else:
            print(f"❌ 缺少 {tool} 截图目录")

def test_automation_base_class():
    """测试自动化基类"""
    from src.mcpsectrace.core.base_automation import BaseAutomation
    
    try:
        # 创建测试子类
        class TestAutomation(BaseAutomation):
            def start_scan(self):
                return True
            def wait_for_completion(self, timeout=300):
                return True
            def export_results(self, output_path=None):
                return True
        
        test_auto = TestAutomation("test_tool")
        print("✅ 自动化基类测试成功")
    except Exception as e:
        print(f"❌ 自动化基类测试失败: {e}")

if __name__ == "__main__":
    test_image_assets()
    test_automation_base_class()
```

## 🧪 集成测试

### 1. 端到端工作流测试

```python
# test_integration.py
"""集成测试"""

def test_full_workflow():
    """测试完整工作流程"""
    from src.mcpsectrace.utils.logging_setup import setup_logger
    from src.mcpsectrace.utils.image_recognition import ImageRecognition
    
    try:
        # 1. 日志系统
        logger = setup_logger("integration_test")
        logger.info("开始集成测试")
        
        # 2. 图像识别系统
        img_rec = ImageRecognition()
        
        # 3. 自动化基类
        from src.mcpsectrace.core.base_automation import BaseAutomation
        
        logger.info("集成测试完成")
        print("✅ 集成测试通过")
        
    except Exception as e:
        print(f"❌ 集成测试失败: {e}")

if __name__ == "__main__":
    test_full_workflow()
```

### 2. 外部依赖测试

```python
# test_external_deps.py
"""测试外部依赖"""

def test_external_mcp_servers():
    """测试外部MCP服务器可用性"""
    import os
    
    external_servers = [
        'external_mcp/ThreatMCP',
        'external_mcp/winlog-mcp',
        'external_mcp/fdp-mcp-server',
        'external_mcp/mcp-everything-search'
    ]
    
    for server in external_servers:
        if os.path.exists(server):
            main_files = [
                'run_server.py',
                'src/main.py', 
                '__main__.py'
            ]
            
            found_main = False
            for main_file in main_files:
                if os.path.exists(os.path.join(server, main_file)):
                    found_main = True
                    break
            
            if found_main:
                print(f"✅ {server}")
            else:
                print(f"⚠️ {server} (找不到主文件)")
        else:
            print(f"❌ 缺少: {server}")

if __name__ == "__main__":
    test_external_mcp_servers()
```

## ⚡ 性能和兼容性测试

### 1. 启动时间测试

```python
# test_performance.py
"""性能测试"""

import time
import importlib

def test_import_performance():
    """测试模块导入性能"""
    modules = [
        'src.mcpsectrace.core.browser_forensics',
        'src.mcpsectrace.automation.huorong',
        'src.mcpsectrace.utils.image_recognition'
    ]
    
    for module_name in modules:
        start_time = time.time()
        try:
            importlib.import_module(module_name)
            end_time = time.time()
            import_time = (end_time - start_time) * 1000
            print(f"✅ {module_name}: {import_time:.2f}ms")
        except Exception as e:
            print(f"❌ {module_name}: {e}")

if __name__ == "__main__":
    test_import_performance()
```

### 2. 内存使用测试

```python
# test_memory.py
"""内存使用测试"""

import psutil
import os

def test_memory_usage():
    """测试内存使用情况"""
    process = psutil.Process(os.getpid())
    
    # 基线内存
    baseline_memory = process.memory_info().rss / 1024 / 1024  # MB
    
    # 导入所有模块
    from src.mcpsectrace.core import browser_forensics
    from src.mcpsectrace.automation import huorong
    from src.mcpsectrace.utils import image_recognition
    
    # 测量内存增长
    after_import_memory = process.memory_info().rss / 1024 / 1024  # MB
    memory_increase = after_import_memory - baseline_memory
    
    print(f"基线内存: {baseline_memory:.2f} MB")
    print(f"导入后内存: {after_import_memory:.2f} MB")
    print(f"内存增长: {memory_increase:.2f} MB")
    
    if memory_increase < 100:  # 100MB阈值
        print("✅ 内存使用正常")
    else:
        print("⚠️ 内存使用较高")

if __name__ == "__main__":
    test_memory_usage()
```

## 📚 文档和工具验证

### 1. 代码质量检查

```bash
# 代码格式检查
echo "🔍 检查代码格式..."
uv run black --check src/ || echo "❌ 代码格式问题"
uv run isort --check-only src/ || echo "❌ 导入排序问题"

# 类型检查
echo "🔍 类型检查..."
uv run mypy src/ || echo "⚠️ 类型检查警告"

# 代码复杂度检查
echo "🔍 代码复杂度检查..."
find src/ -name "*.py" -exec wc -l {} + | tail -n 1
```

### 2. 文档完整性检查

```bash
# 检查文档文件
echo "📚 检查文档完整性..."
for doc in README.md CLAUDE.md docs/development/github-collaboration-guide.md docs/development/post-refactor-testing-guide.md; do
    if [ -f "$doc" ]; then
        echo "✅ $doc"
    else
        echo "❌ 缺少: $doc"
    fi
done

# 检查模块文档字符串
python -c "
import src.mcpsectrace.core.browser_forensics as bf
import src.mcpsectrace.utils.logging_setup as ls

modules = [bf, ls]
for module in modules:
    if module.__doc__:
        print(f'✅ {module.__name__} 有文档字符串')
    else:
        print(f'⚠️ {module.__name__} 缺少文档字符串')
"
```

## 📝 测试报告模板

### 自动化测试报告

```bash
#!/bin/bash
# test_all.sh - 运行所有测试并生成报告

echo "🚀 MCPSecTrace 重构后测试报告"
echo "================================"
echo "测试时间: $(date)"
echo "Python版本: $(python --version)"
echo "uv版本: $(uv --version)"
echo ""

# 环境测试
echo "📦 环境配置测试"
echo "----------------"
uv sync && echo "✅ 依赖安装成功" || echo "❌ 依赖安装失败"

# 模块导入测试
echo ""
echo "📂 模块导入测试"
echo "----------------"
python docs/development/test_imports.py

# 功能测试
echo ""
echo "🔧 功能测试"
echo "------------"
python docs/development/test_utils.py

# 性能测试
echo ""
echo "⚡ 性能测试"
echo "----------"
python docs/development/test_performance.py

# 代码质量
echo ""
echo "✨ 代码质量检查"
echo "---------------"
uv run black --check src/ && echo "✅ 代码格式正确" || echo "❌ 代码格式需要修复"

echo ""
echo "🎉 测试完成"
```

## 🆘 故障排除指南

### 常见问题解决

1. **导入错误**
   ```bash
   # 如果遇到模块导入错误，检查Python路径
   python -c "import sys; print('\n'.join(sys.path))"
   
   # 确保在项目根目录运行
   pwd
   ```

2. **依赖问题**
   ```bash
   # 重新安装依赖
   uv sync --force
   
   # 检查特定包
   uv tree | grep -E "(opencv|pyautogui|pydantic)"
   ```

3. **权限问题**
   ```bash
   # 检查文件权限
   find src/ -name "*.py" ! -perm -644 -ls
   
   # 修复权限
   find src/ -name "*.py" -exec chmod 644 {} \;
   ```

### 回滚策略

如果重构后的代码有严重问题：

```bash
# 1. 创建测试分支保存当前状态
git checkout -b refactor-issues

# 2. 回到重构前的状态（如果需要）
git checkout HEAD~1

# 3. 或者选择性修复问题
git cherry-pick <specific-fix-commit>
```

---

## 🎯 测试成功标准

**通过标准：**
- ✅ 所有模块成功导入
- ✅ 基础功能脚本正常运行
- ✅ MCP服务器能够启动
- ✅ 代码格式检查通过
- ✅ 无循环导入问题
- ✅ 内存使用合理

**警告条件：**
- ⚠️ 部分外部依赖不可用（但不影响核心功能）
- ⚠️ 性能略有下降（但在可接受范围内）
- ⚠️ 文档需要更新

遇到问题时，请参考[GitHub协作开发指南](github-collaboration-guide.md)中的问题解决章节，或提交Issue寻求帮助。

---

*本测试指南随项目发展持续更新。建议在每次重大重构后执行完整测试流程。*