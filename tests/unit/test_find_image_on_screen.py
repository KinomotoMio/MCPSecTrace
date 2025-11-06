#!/usr/bin/env python3
"""
测试修改后的 find_image_on_screen() 函数
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.mcpsectrace.mcp_servers.huorong_mcp import find_image_on_screen


def test_find_image_on_screen():
    """测试相对位置定位功能（基于前台窗口）"""
    print("🔍 测试 find_image_on_screen() 基于窗口的相对位置定位...")

    test_cases = [
        (0.5, 0.5, "窗口中心"),
        (0.0, 0.0, "窗口左上角"),
        (1.0, 1.0, "窗口右下角"),
        (0.4, 0.3, "火绒快速查杀按钮"),
    ]

    all_passed = True
    for x_ratio, y_ratio, description in test_cases:
        try:
            result = find_image_on_screen(
                x_ratio=x_ratio,
                y_ratio=y_ratio,
                timeout_seconds=1,
                description=description,
            )

            if result:
                abs_x, abs_y = result
                print(f"✅ {description}")
                print(f"   相对位置: ({x_ratio:.2f}, {y_ratio:.2f})")
                print(f"   绝对坐标: ({abs_x}, {abs_y})")

                # 简单的合理性检查：坐标应该是整数且合理
                if isinstance(abs_x, int) and isinstance(abs_y, int):
                    print(f"   ✅ 坐标类型正确")
                else:
                    print(f"   ❌ 坐标类型错误")
                    all_passed = False
            else:
                print(f"⚠️ {description} - 返回 None")

        except Exception as e:
            print(f"❌ {description} - 异常: {e}")
            all_passed = False

        print()

    return all_passed


def test_config_reading():
    """测试从配置文件读取相对位置"""
    print("\n🔍 测试从配置文件读取相对位置...")

    try:
        from src.mcpsectrace.config import get_config_value

        # 测试读取配置
        quick_scan_pos = get_config_value(
            "positions.huorong.quick_scan_button", default=[0.4, 0.3]
        )
        print(f"✅ 快速查杀按钮位置: {quick_scan_pos}")

        pause_button_pos = get_config_value(
            "positions.huorong.pause_button", default=[0.5, 0.5]
        )
        print(f"✅ 暂停按钮位置: {pause_button_pos}")

        complete_button_pos = get_config_value(
            "positions.huorong.complete_button", default=[0.5, 0.7]
        )
        print(f"✅ 完成按钮位置: {complete_button_pos}")

        return True

    except Exception as e:
        print(f"❌ 读取配置失败: {e}")
        return False


def main():
    """运行所有测试"""
    print("🚀 开始 find_image_on_screen() 测试")
    print("=" * 50)

    test1_result = test_find_image_on_screen()
    test2_result = test_config_reading()

    print("\n" + "=" * 50)
    if test1_result and test2_result:
        print("🎉 所有测试通过！")
        return 0
    else:
        print("⚠️ 部分测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
