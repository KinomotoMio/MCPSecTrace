#!/usr/bin/env python3
"""
测试工具类功能
重构后代码测试脚本 - 工具功能测试
"""

import sys
import tempfile
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def test_logging_setup():
    """测试日志配置功能"""
    print("🔍 测试日志配置功能...")
    try:
        from src.mcpsectrace.utils.logging_setup import (
            get_timestamped_filename,
            setup_logger,
        )

        # 测试基本日志设置
        logger = setup_logger("test_logger")
        logger.info("测试日志消息")
        logger.warning("测试警告消息")

        # 测试带文件的日志设置
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".log") as tmp:
            file_logger = setup_logger("file_logger", tmp.name)
            file_logger.error("测试错误消息")

        # 清理临时文件
        os.unlink(tmp.name)

        # 测试文件名生成
        filename = get_timestamped_filename("test", "log")
        assert "test_" in filename
        assert filename.endswith(".log")

        print("✅ 日志配置功能正常")
        return True
    except Exception as e:
        print(f"❌ 日志配置测试失败: {e}")
        return False


def test_image_recognition():
    """测试图像识别类基础功能"""
    print("🔍 测试图像识别类...")
    try:
        from src.mcpsectrace.utils.image_recognition import ImageRecognition

        # 测试类初始化
        img_rec = ImageRecognition()
        assert img_rec.confidence_threshold == 0.8

        # 测试自定义资源目录
        custom_img_rec = ImageRecognition("custom/path")
        assert str(custom_img_rec.assets_dir) == "custom/path"

        print("✅ 图像识别类初始化正常")
        return True
    except Exception as e:
        print(f"❌ 图像识别类测试失败: {e}")
        return False


def test_base_automation():
    """测试自动化基类"""
    print("🔍 测试自动化基类...")
    try:
        from src.mcpsectrace.core.base_automation import BaseAutomation

        # 创建测试子类
        class TestAutomation(BaseAutomation):
            def start_scan(self):
                return True

            def wait_for_completion(self, timeout=300):
                return True

            def export_results(self, output_path=None):
                return True

        # 测试基类功能
        test_auto = TestAutomation("test_tool")
        assert test_auto.tool_name == "test_tool"
        assert not test_auto.is_running

        # 测试抽象方法实现
        assert test_auto.start_scan() == True
        assert test_auto.wait_for_completion() == True
        assert test_auto.export_results() == True

        print("✅ 自动化基类测试成功")
        return True
    except Exception as e:
        print(f"❌ 自动化基类测试失败: {e}")
        return False


def test_module_attributes():
    """测试模块属性和文档字符串"""
    print("🔍 测试模块属性...")
    try:
        modules_to_check = [
            "src.mcpsectrace.utils.logging_setup",
            "src.mcpsectrace.utils.image_recognition",
            "src.mcpsectrace.core.base_automation",
        ]

        for module_name in modules_to_check:
            module = __import__(module_name, fromlist=[""])

            # 检查模块是否有文档字符串
            if module.__doc__:
                print(f"✅ {module_name} 有文档字符串")
            else:
                print(f"⚠️ {module_name} 缺少文档字符串")

        return True
    except Exception as e:
        print(f"❌ 模块属性测试失败: {e}")
        return False


def test_dependency_imports():
    """测试关键依赖的导入"""
    print("🔍 测试关键依赖导入...")
    try:
        # 测试GUI自动化相关依赖
        import cv2
        import pyautogui

        print(f"✅ OpenCV版本: {cv2.__version__}")
        print(f"✅ PyAutoGUI版本: {pyautogui.__version__}")

        # 测试其他核心依赖
        import httpx
        import pydantic

        print(f"✅ Pydantic版本: {pydantic.VERSION}")
        print(f"✅ HTTPX版本: {httpx.__version__}")

        return True
    except ImportError as e:
        print(f"❌ 依赖导入失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 依赖测试异常: {e}")
        return False


def test_file_structure():
    """测试文件结构完整性"""
    print("🔍 测试文件结构...")
    try:
        required_dirs = [
            "src/mcpsectrace/core",
            "src/mcpsectrace/automation",
            "src/mcpsectrace/mcp_servers",
            "src/mcpsectrace/utils",
            "assets/screenshots",
            "tools",
            "external_mcp",
            "scripts",
            "docs/development",
        ]

        missing_dirs = []
        for dir_path in required_dirs:
            full_path = project_root / dir_path
            if not full_path.exists():
                missing_dirs.append(dir_path)
            else:
                print(f"✅ {dir_path}")

        if missing_dirs:
            print(f"❌ 缺少目录: {', '.join(missing_dirs)}")
            return False

        print("✅ 文件结构完整")
        return True
    except Exception as e:
        print(f"❌ 文件结构测试失败: {e}")
        return False


def main():
    """运行所有工具测试"""
    print("🚀 开始工具功能测试")
    print("=" * 40)

    tests = [
        test_dependency_imports,
        test_file_structure,
        test_logging_setup,
        test_image_recognition,
        test_base_automation,
        test_module_attributes,
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
        print("🎉 所有工具功能测试通过！")
        return 0
    else:
        print("⚠️ 部分测试失败，请检查工具实现")
        return 1


if __name__ == "__main__":
    sys.exit(main())
