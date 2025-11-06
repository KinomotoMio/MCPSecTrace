#!/usr/bin/env python3
"""
测试火绒MCP从配置文件读取配置的功能
"""

import io
import os
import sys
from pathlib import Path

# 设置输出编码为UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.mcpsectrace.config import get_config_value


def test_read_huorong_path():
    """测试从配置文件读取火绒路径"""
    print("🔍 测试读取火绒路径配置...")

    try:
        huorong_path = get_config_value("paths.huorong_exe", default="")

        if huorong_path:
            print(f"✅ 成功读取火绒路径: {huorong_path}")

            # 检查路径是否存在
            if os.path.exists(huorong_path):
                print(f"✅ 火绒路径存在")
                return True
            else:
                print(f"⚠️ 火绒路径不存在: {huorong_path}")
                print(f"   请在 config/user_settings.toml 中设置正确的路径")
                return None
        else:
            print(f"❌ 未配置火绒路径")
            print(f"   请在 config/user_settings.toml 中设置 paths.huorong_exe")
            return False

    except Exception as e:
        print(f"❌ 读取配置时出错: {e}")
        return False


def test_read_other_configs():
    """测试读取其他配置项"""
    print("\n🔍 测试读取其他配置项...")

    configs_to_test = [
        ("debug_mode", False),
        ("device_level", 2),
        ("automation.default_confidence", 0.8),
        ("automation.find_timeout", 15),
    ]

    all_passed = True

    for config_key, expected_default in configs_to_test:
        try:
            value = get_config_value(config_key, default=expected_default)
            print(f"✅ {config_key} = {value}")
        except Exception as e:
            print(f"❌ 读取 {config_key} 失败: {e}")
            all_passed = False

    return all_passed


def main():
    """运行所有测试"""
    print("🚀 开始火绒配置读取测试")
    print("=" * 50)

    tests = [
        ("读取火绒路径", test_read_huorong_path),
        ("读取其他配置", test_read_other_configs),
    ]

    passed = 0
    skipped = 0
    failed = 0

    for test_name, test_func in tests:
        print(f"\n📌 测试: {test_name}")
        print("-" * 50)
        try:
            result = test_func()
            if result is True:
                passed += 1
            elif result is None:
                skipped += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ 测试异常: {e}")
            failed += 1

    print("\n" + "=" * 50)
    total = len(tests)
    print(f"📊 测试结果: {passed}/{total} 通过, {skipped} 跳过, {failed} 失败")

    if failed == 0:
        print("🎉 所有测试通过！")
        return 0
    else:
        print("⚠️ 部分测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
