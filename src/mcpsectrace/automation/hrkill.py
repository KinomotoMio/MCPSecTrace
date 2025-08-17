import ctypes
import sys
import subprocess
import os
import time
import pyautogui

# ================== 权限检查 ==================
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, os.path.abspath(sys.argv[0]), None, 1)
    sys.exit()

# ================== 启动程序 ==================
def run_exe(exe_path):
    """以管理员权限运行 exe"""
    subprocess.Popen(exe_path)
    print(f"已尝试启动程序: {exe_path}")
    time.sleep(3)  # 等待窗口加载
    return os.path.basename(exe_path)

# ================== 自动化操作 ==================
def click_start_scan_button(image_path, confidence=0.8):
    """
    查找并点击“开始扫描”按钮
    :param image_path: 按钮截图路径
    :param confidence: 匹配置信度
    """
    print("正在查找 '开始扫描' 按钮...")
    try:
        location = pyautogui.locateOnScreen(image_path, confidence=confidence)
        if location:
            center = pyautogui.center(location)
            pyautogui.click(center)
            print("✅ 已点击 '开始扫描' 按钮")
        else:
            print("❌ 未找到 '开始扫描' 按钮，请确认截图是否准确、按钮是否已显示")
            return False
    except pyautogui.ImageNotFoundException:
        print("💥 图像识别失败：未能找到与提供的图像匹配的区域，请确保图像正确无误，并且目标界面可见。")
        return False
    return True

def wait_for_scan_complete(complete_image_path, timeout=900, check_interval=8, confidence=0.7):
    """
    等待扫描完成
    :param complete_image_path: 扫描完成标志的截图路径
    :param timeout: 最大等待时间（秒）
    :param check_interval: 每次检查间隔（秒）
    :param confidence: 匹配置信度
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            location = pyautogui.locateOnScreen(complete_image_path, confidence=confidence)
            if location:
                print("🎉 扫描已完成！")
                return True
        except pyautogui.ImageNotFoundException:
            pass
        time.sleep(check_interval)
    print("⌛ 扫描未在指定时间内完成或无法找到完成标志。")
    return False

# ================== 主程序入口 ==================
if __name__ == "__main__":
    # 配置项
    exe_to_run = "tool\\hrkill-1.0.0.86.exe"       # 火绒程序路径
    start_button_image = "tag_image\\hr\\start_scan_button.png"     # “开始扫描”按钮截图文件
    complete_button_image = "tag_image\\hr\\scan_complete.png"     # 扫描完成标志截图文件

    # 1. 检查权限
    if not is_admin():
        print("未检测到管理员权限，正在请求权限...")
        run_as_admin()
    else:
        print("当前已具备管理员权限")

        # 2. 启动程序
        run_exe(exe_to_run)
        print("程序已启动")

        # 5. 等待界面加载完成（根据实际需要调整）
        time.sleep(3)

        # 6. 点击“开始扫描”按钮
        if click_start_scan_button(start_button_image):
            # 7. 等待扫描完成
            if wait_for_scan_complete(complete_button_image):
                print("扫描过程结束，可以继续后续步骤。")
            else:
                print("扫描未完成，可能需要人工干预。")
        else:
            print("由于找不到开始扫描按钮，无法进行扫描。")

        # input("程序已结束，按回车键退出...")