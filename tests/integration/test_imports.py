#!/usr/bin/env python3
"""
验证所有模块的导入功能
重构后代码测试脚本 - 模块导入测试
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def test_core_modules():
    """测试核心模块导入"""
    print("🔍 测试核心模块导入...")
    try:
        from src.mcpsectrace.core import (
            base_automation,
            browser_forensics,
            sysmon_collector,
        )

        print("✅ 核心模块导入成功")
        return True
    except ImportError as e:
        print(f"❌ 核心模块导入失败: {e}")
        return False


def test_automation_modules():
    """测试自动化模块导入"""
    print("🔍 测试自动化模块导入...")
    try:
        from src.mcpsectrace.automation import focus_pack, hrkill, huorong

        print("✅ 自动化模块导入成功")
        return True
    except ImportError as e:
        print(f"❌ 自动化模块导入失败: {e}")
        return False


def test_mcp_modules():
    """测试MCP服务器模块导入"""
    print("🔍 测试MCP服务器模块导入...")
    try:
        from src.mcpsectrace.mcp_servers import (
            browser_mcp,
            focus_pack_mcp,
            hrkill_mcp,
            huorong_mcp,
        )

        print("✅ MCP服务器模块导入成功")
        return True
    except ImportError as e:
        print(f"❌ MCP服务器模块导入失败: {e}")
        return False


def test_utils_modules():
    """测试工具模块导入"""
    print("🔍 测试工具模块导入...")
    try:
        from src.mcpsectrace.utils import image_recognition, logging_setup

        print("✅ 工具模块导入成功")
        return True
    except ImportError as e:
        print(f"❌ 工具模块导入失败: {e}")
        return False


def test_package_structure():
    """测试包结构"""
    print("🔍 测试包结构...")
    try:
        import src.mcpsectrace

        print(f"✅ 主包导入成功: {src.mcpsectrace.__file__}")

        # 测试子包
        from src.mcpsectrace import automation, core, mcp_servers, utils

        print("✅ 所有子包导入成功")
        return True
    except ImportError as e:
        print(f"❌ 包结构测试失败: {e}")
        return False


def main():
    """运行所有导入测试"""
    print("🚀 开始模块导入测试")
    print("=" * 40)

    tests = [
        test_package_structure,
        test_core_modules,
        test_automation_modules,
        test_mcp_modules,
        test_utils_modules,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1
        print()

    print("=" * 40)
    print(f"📊 测试结果: {passed}/{total} 通过")

    if passed == total:
        print("🎉 所有模块导入测试通过！")
        return 0
    else:
        print("⚠️ 部分测试失败，请检查模块结构")
        return 1


if __name__ == "__main__":
    sys.exit(main())