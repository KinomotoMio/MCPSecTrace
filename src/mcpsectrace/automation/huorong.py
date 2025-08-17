import pyautogui
import time
import subprocess
import os
from datetime import datetime  # 新增导入 for 获取当前时间

# --- 用户配置 ---
# HUORONG_PATH = r"C:\Program Files (x86)\Huorong\Sysdiag\bin\HipsTray.exe" # 示例
HUORONG_PATH = "D:\\HuoRong\\Sysdiag\\bin\\HipsMain.exe"  # 用户提供的路径

# 用于图像识别的截图文件名 (请确保这些文件与脚本在同一目录下)
MENU_ICON_IMAGE = './tag_image/huorong/huorong_menu_icon.png'
SECURITY_LOG_IMAGE = './tag_image/huorong/huorong_security_log.png'

# 新增图片文件名
EXPORT_LOG_BUTTON_IMAGE = './tag_image/huorong/huorong_export_log_button.png'
FILENAME_INPUT_BOX_IMAGE = 'tag_image/huorong/huorong_filename_input_box.png'
SAVE_BUTTON_IMAGE = './tag_image/huorong/huorong_save_button.png'


# --- 用户配置结束 ---

def start_application(path):
    """尝试启动一个应用程序"""
    try:
        if not path or not os.path.exists(path):
            print(f"错误：应用程序路径 '{path}' 无效或不存在。")
            print("请确保 HUORONG_PATH 变量已正确设置为火绒安全的启动程序路径。")
            print("脚本将尝试在不启动新进程的情况下继续（假设火绒已打开）。")
            return None
        print(f"正在尝试启动应用程序: {path}")
        app = subprocess.Popen(path)
        print(f"应用程序已启动 (进程ID: {app.pid})。等待几秒钟让其主窗口加载...")
        time.sleep(6)  # 等待应用程序加载
        return app
    except Exception as e:
        print(f"启动应用程序 '{path}' 时发生错误: {e}")
        print("脚本将尝试在不启动新进程的情况下继续（假设火绒已打开）。")
        return None


def click_image_on_screen(image_filename, confidence_level=0.85, timeout_seconds=15, description=""):
    """
    在屏幕上查找指定的图像并点击其中心。
    """
    if not description:
        description = image_filename

    print(f"正在查找图像: '{description}' (文件: {image_filename})，超时时间: {timeout_seconds}秒...")
    start_time = time.time()
    location = None  # 初始化 location
    while time.time() - start_time < timeout_seconds:
        try:
            location = pyautogui.locateCenterOnScreen(image_filename, confidence=confidence_level)
            if location:
                pyautogui.click(location)
                print(f"成功点击 '{description}' 在坐标: {location}")
                return True
            else:
                time.sleep(0.5)
        except pyautogui.ImageNotFoundException:
            time.sleep(0.5)
        except FileNotFoundError:  # PyAutoGUI 内部也可能因图片文件问题抛出此异常
            print(f"严重错误：图像文件 '{image_filename}' 未找到或无法访问！请确保它在脚本的同一目录下且格式正确。")
            return False
        except Exception as e:
            if "Failed to read" in str(e) or "cannot identify image file" in str(e) or isinstance(e,
                                                                                                  pyautogui.ImageNotFoundException):
                print(
                    f"错误: PyAutoGUI无法读取或识别图像文件 '{image_filename}'。请确保文件存在、未损坏且为支持的格式(如PNG)。错误详情: {e}")
                return False
            print(f"查找或点击图像 '{description}' 时发生其他错误: {e}")
            return False

    print(f"超时：在 {timeout_seconds} 秒内未能找到图像 '{description}'。")
    return False


def main_automation_flow():
    """执行主要的自动化操作流程"""
    print("请确保火绒安全的主窗口是当前活动窗口，或者至少是可见的。")
    time.sleep(2)

    # 步骤 1: 点击菜单图标
    if not click_image_on_screen(MENU_ICON_IMAGE, confidence_level=0.8, timeout_seconds=20, description="火绒菜单图标"):
        print(f"未能点击火绒菜单图标。请检查 '{MENU_ICON_IMAGE}' 图像。")
        return
    time.sleep(1.5)  # 等待菜单展开

    # 步骤 2: 点击"安全日志"
    if not click_image_on_screen(SECURITY_LOG_IMAGE, confidence_level=0.8, timeout_seconds=15,
                                 description="安全日志选项"):
        print(f"未能点击安全日志选项。请检查 '{SECURITY_LOG_IMAGE}' 图像。")
        return

    print("安全日志界面已打开。")
    time.sleep(2.5)  # 等待安全日志界面完全加载

    # 新增步骤：导出日志
    # 步骤 3: 点击“导出本页日志”按钮
    print("尝试点击“导出本页日志”...")
    if not click_image_on_screen(EXPORT_LOG_BUTTON_IMAGE, confidence_level=0.8, timeout_seconds=15,
                                 description="导出本页日志按钮"):
        print(f"未能点击“导出本页日志”按钮。请检查 '{EXPORT_LOG_BUTTON_IMAGE}' 图像是否准确，以及按钮是否可见。")
        return
    time.sleep(2.5)  # 等待“另存为”对话框出现，根据实际情况调整

    # 步骤 4: 点击文件名输入框
    print("尝试点击文件名输入框...")
    # 注意：文件名输入框的截图可能需要精确，或者可以考虑点击 "文件名：" 标签右侧固定偏移量（更复杂）
    if not click_image_on_screen(FILENAME_INPUT_BOX_IMAGE, confidence_level=0.8, timeout_seconds=15,
                                 description="文件名输入框"):
        print(f"未能点击文件名输入框。请检查 '{FILENAME_INPUT_BOX_IMAGE}' 图像是否准确。")
        return
    time.sleep(0.5)  # 给输入框获取焦点的时间

    # (可选) 清空文件名输入框中的现有内容
    # 有时对话框会预填内容，或者默认全选。如果直接输入会追加，则需要先清空。
    # pyautogui.hotkey('ctrl', 'a') # 全选
    # time.sleep(0.1)
    # pyautogui.press('delete') # 删除
    # time.sleep(0.1)
    # 或者根据实际情况多次按 backspace
    # for _ in range(20): # 假设最多有20个字符需要删除
    #     pyautogui.press('backspace')
    # time.sleep(0.1)

    # 步骤 5: 输入当前时间作为文件名
    # 使用北京时间 (CST, UTC+8)
    # 注意：如果你的系统时区不是CST，datetime.now()会使用系统本地时间。
    # 为确保是北京时间，可以使用更复杂的方法，但通常 .now() 对大部分中国用户是准确的。
    current_time_str = datetime.now().strftime("%Y-%m-%d-%H-%M-%S") + "-huoronglog"
    print(f"准备输入文件名: {current_time_str}")
    pyautogui.typewrite(current_time_str, interval=0.05)  # interval 控制打字速度
    time.sleep(0.5)

    # 步骤 6: 点击“保存”按钮
    print("尝试点击“保存”按钮...")
    time.sleep(0.5)
    if not click_image_on_screen(SAVE_BUTTON_IMAGE, confidence_level=0.8, timeout_seconds=15, description="保存按钮"):
        print(f"未能点击“保存”按钮。请检查 '{SAVE_BUTTON_IMAGE}' 图像是否准确。")
        return

    print("日志导出流程（尝试）执行完毕。")
    time.sleep(1)  # 等待保存操作完成

    print("整体自动化流程执行完毕。")


if __name__ == "__main__":
    print("--------------------------------------------------------------------")
    print("PyAutoGUI 自动化脚本：启动火绒 -> 菜单 -> 安全日志 -> 导出日志")
    print("--------------------------------------------------------------------")
    print("重要准备工作：")
    print(f"1. 火绒安全软件的完整安装路径。")
    print(f"2. “菜单图标”截图: '{MENU_ICON_IMAGE}'")
    print(f"3. “安全日志”选项截图: '{SECURITY_LOG_IMAGE}'")
    print(f"4. (新增) “导出本页日志”按钮截图: '{EXPORT_LOG_BUTTON_IMAGE}'")
    print(f"5. (新增) “文件名”输入框截图: '{FILENAME_INPUT_BOX_IMAGE}'")
    print(f"6. (新增) “保存”按钮截图: '{SAVE_BUTTON_IMAGE}'")
    print("   请将所有 .png 截图文件与此 Python 脚本放在同一目录下。")
    print("   截图提示：区域尽量小且特征明显，避免包含过多背景。")
    print("--------------------------------------------------------------------")

    missing_files = False
    required_images = [MENU_ICON_IMAGE, SECURITY_LOG_IMAGE, EXPORT_LOG_BUTTON_IMAGE, FILENAME_INPUT_BOX_IMAGE,
                       SAVE_BUTTON_IMAGE]
    for img_file in required_images:
        if not os.path.exists(img_file):
            print(f"错误：必需的图像文件 '{img_file}' 未在脚本目录中找到！")
            missing_files = True

    if missing_files:
        print("\n请先按照上述说明准备好所有必需的图像文件。脚本将不会执行。")
    else:
        # 获取火绒路径
        # default_path_suggestion = r"D:\HuoRong\Sysdiag\bin\HipsMain.exe" # 已在顶部HUORONG_PATH配置
        user_path_input = input(f"请输入火绒的完整路径 (当前配置为 '{HUORONG_PATH}', 直接回车使用此配置):\n")
        if user_path_input.strip():
            HUORONG_PATH = user_path_input.strip()
        else:
            # HUORONG_PATH = default_path_suggestion # 已在顶部配置，此处无需重复赋值
            print(f"使用已配置路径: {HUORONG_PATH}")

        print("\n脚本将在几秒后开始执行自动化操作...")
        print("你有5秒钟时间切换到桌面或准备环境。要中途停止脚本，请快速将鼠标移动到屏幕的任一角落。")
        time.sleep(5)

        if HUORONG_PATH:
            start_application(HUORONG_PATH)
        else:
            print("未配置火绒路径，假设火绒软件已手动打开。")
            time.sleep(2)

        main_automation_flow()