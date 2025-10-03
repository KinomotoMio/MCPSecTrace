import os
import subprocess
import time

import pyautogui
import pygetwindow as gw


class HuorongController:
    def __init__(self, huorong_path):
        self.huorong_path = huorong_path
        self.window_title = "火绒安全"  # 火绒窗口标题可能包含的关键字
        self.window = None

    def start_huorong(self):
        """启动火绒安全软件"""
        try:
            if not os.path.exists(self.huorong_path):
                print(f"错误：找不到火绒安全软件路径: {self.huorong_path}")
                return False

            print("正在启动火绒安全软件...")
            subprocess.Popen([self.huorong_path])
            return True

        except Exception as e:
            print(f"启动火绒安全软件失败: {e}")
            return False

    def wait_for_window(self, timeout=30):
        """等待火绒窗口出现"""
        print("等待火绒窗口加载...")
        start_time = time.time()

        while time.time() - start_time < timeout:
            # 尝试多种可能的窗口标题
            possible_titles = ["火绒", "Huorong", "安全", "HipsMain"]

            for title in possible_titles:
                windows = gw.getWindowsWithTitle(title)
                if windows:
                    for window in windows:
                        # 确认是火绒窗口（通过进程名或窗口大小）
                        if (
                            window.width > 800 and window.height > 500
                        ):  # 火绒窗口通常比较大
                            self.window = window
                            print(f"找到火绒窗口: {window.title}")
                            return True

            time.sleep(1)

        print("等待窗口超时")
        return False

    def activate_window(self):
        """激活火绒窗口"""
        if self.window:
            try:
                self.window.activate()
                time.sleep(2)  # 等待窗口完全激活
                print("火绒窗口已激活")
                return True
            except Exception as e:
                print(f"激活窗口失败: {e}")
                return False
        return False

    def calculate_relative_position(self):
        """计算相对位置：宽度1/5，高度1/2"""
        if not self.window:
            return None

        # 计算相对坐标
        relative_x = self.window.width // 5
        relative_y = self.window.height // 2

        # 计算绝对坐标
        absolute_x = self.window.left + relative_x
        absolute_y = self.window.top + relative_y

        print(f"窗口尺寸: {self.window.width} x {self.window.height}")
        print(f"相对位置: ({relative_x}, {relative_y})")
        print(f"绝对位置: ({absolute_x}, {absolute_y})")

        return (absolute_x, absolute_y)

    def click_calculated_position(self):
        """点击计算出的位置"""
        position = self.calculate_relative_position()
        if position:
            try:
                # 先移动鼠标到位置（可视化反馈）
                pyautogui.moveTo(position[0], position[1], duration=1)
                print("鼠标已移动到目标位置")
                time.sleep(1)

                # 执行点击
                pyautogui.click()
                print("点击完成！")
                return True

            except Exception as e:
                print(f"点击操作失败: {e}")
                return False
        return False

    def run(self):
        """主执行流程"""
        print("=== 火绒安全软件自动化操作 ===")

        # 1. 启动火绒
        if not self.start_huorong():
            return False

        # 2. 等待窗口出现
        if not self.wait_for_window():
            return False

        # 3. 激活窗口
        if not self.activate_window():
            return False

        # 4. 点击目标位置
        if not self.click_calculated_position():
            return False

        print("操作完成！")
        return True


# 增强版：带调试功能的控制器
class DebugHuorongController(HuorongController):
    def debug_window_info(self):
        """调试信息：显示所有相关窗口"""
        print("\n=== 窗口调试信息 ===")
        all_windows = gw.getAllWindows()
        for i, window in enumerate(all_windows):
            if window.title:  # 只显示有标题的窗口
                print(
                    f"{i+1}. 标题: '{window.title}' | 位置: {window.left},{window.top} | 尺寸: {window.width}x{window.height}"
                )

    def interactive_position_test(self):
        """交互式位置测试"""
        print("\n=== 交互式位置测试 ===")
        print("将鼠标移动到窗口左上角，按Enter记录...")
        input()
        left, top = pyautogui.position()

        print("将鼠标移动到窗口右下角，按Enter记录...")
        input()
        right, bottom = pyautogui.position()

        width = right - left
        height = bottom - top

        # 计算目标位置
        target_x = left + (width // 5)
        target_y = top + (height // 2)

        print(f"计算出的点击位置: ({target_x}, {target_y})")

        # 可视化演示
        pyautogui.moveTo(target_x, target_y, duration=2)
        print("鼠标已移动到计算位置，确认是否正确？")

        response = input("是否执行点击？(y/n): ")
        if response.lower() == "y":
            pyautogui.click()
            print("点击执行完成！")

    def screenshot_analysis(self):
        """截图分析当前窗口"""
        if self.window:
            print("正在截取窗口截图...")
            try:
                # 截取窗口区域
                screenshot = pyautogui.screenshot(
                    region=(
                        self.window.left,
                        self.window.top,
                        self.window.width,
                        self.window.height,
                    )
                )
                screenshot.save("huorong_window.png")
                print("窗口截图已保存为 'huorong_window.png'")

                # 标记目标点击位置
                target_x = self.window.width // 5
                target_y = self.window.height // 2
                print(f"截图上的目标位置: ({target_x}, {target_y})")

            except Exception as e:
                print(f"截图失败: {e}")


# 使用示例
def main():
    # 火绒安全软件路径（根据你的实际路径修改）
    huorong_path = r"D:\HuoRong\Sysdiag\bin\HipsMain.exe"

    # 创建控制器实例
    controller = DebugHuorongController(huorong_path)

    print("选择操作模式:")
    print("1. 自动执行完整流程")
    print("2. 调试模式（显示窗口信息）")
    print("3. 交互式位置测试")

    choice = input("请输入选择 (1/2/3): ")

    if choice == "1":
        # 自动执行
        controller.run()

    elif choice == "2":
        # 调试模式
        controller.debug_window_info()
        if controller.wait_for_window(10):
            controller.screenshot_analysis()

    elif choice == "3":
        # 交互式测试
        if controller.wait_for_window(10):
            controller.interactive_position_test()

    else:
        print("无效选择")


# 简单直接执行版本
def simple_execution():
    """简化版执行（如果确定路径正确）"""
    huorong_path = r"D:\HuoRong\Sysdiag\bin\HipsMain.exe"

    controller = HuorongController(huorong_path)
    success = controller.run()

    if success:
        print("✅ 操作成功完成！")
    else:
        print("❌ 操作失败，请检查路径和窗口标题")


if __name__ == "__main__":
    # 直接运行简单版本
    simple_execution()

    # 或者运行交互式版本
    # main()
