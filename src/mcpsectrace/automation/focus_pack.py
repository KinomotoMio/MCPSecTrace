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

def wait_for_new_log_file(log_dir, initial_files=None, check_interval=8, timeout=900):
    """
    等待新日志文件出现在指定目录中
    :param log_dir: 日志目录路径
    :param initial_files: 初始时目录中的文件列表
    :param timeout: 最大等待时间（秒）
    :return: 新文件的完整路径，若超时或无新文件则返回 None
    """
    print("⏳ 正在等待新日志文件出现...")
    start_time = time.time()
    if initial_files is None:
        initial_files = set(os.listdir(log_dir))
    
    while time.time() - start_time < timeout:
        current_files = set(os.listdir(log_dir))
        new_files = current_files - initial_files
        
        if new_files:
            new_file_path = os.path.join(log_dir, new_files.pop())  
            print(f"🎉 检测到新日志文件: {new_file_path}")
            return new_file_path
        
        time.sleep(check_interval)
    
    print("⏰ 超时：未检测到新日志文件。")
    return None

def get_initial_files(log_dir):
    """
    获取指定目录下的初始文件列表
    :param log_dir: 日志目录路径
    :return: 文件名集合
    """
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)  # 如果目录不存在，则创建它
        return set()
    else:
        return set(os.listdir(log_dir))

# ================== 主程序入口 ==================
if __name__ == "__main__":
    # 配置项
    exe_to_run = "tool\\Focus_Pack.exe"
    start_button_image = "tag_image\\focus_pack\\quick_scan.png"

    # 获取当前用户的 AppData\Roaming 目录
    appdata_roaming = os.path.expanduser('~\\AppData\\Roaming')
    focus_logs_path = os.path.join(appdata_roaming, 'FocusLogs')
    print(f"日志目录: {focus_logs_path}")

    # 1. 检查权限
    if not is_admin():
        print("未检测到管理员权限，正在请求权限...")
        run_as_admin()
    else:
        print("当前已具备管理员权限")

        # 2. 启动程序
        run_exe(exe_to_run)
        print("程序已启动")

        # 3.获取初始状态下的文件列表
        initial_files = get_initial_files(focus_logs_path)

        # 5. 等待界面加载完成（根据实际需要调整）
        time.sleep(8)

        # 6. 点击“快速扫描”按钮
        if click_start_scan_button(start_button_image):
            # 7. 等待扫描完成
            new_log_file = wait_for_new_log_file(focus_logs_path, initial_files)
            if new_log_file:
                print("扫描过程结束，成功获取日志文件。")
                # print(f"✅ 已找到最新日志文件: {new_log_file}")
                # ......
            else:
                print("扫描未完成或未能及时获取日志文件，可能需要人工干预。")
        else:
            print("由于找不到开始扫描按钮，无法进行扫描。")

        input("程序已结束，按回车键退出...")