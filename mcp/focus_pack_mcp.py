import os
import sys
import argparse
import pyautogui
import time
import subprocess
import io
from datetime import datetime
import ctypes

# --- 输出使用utf-8编码 --
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# --- 全局变量 ---
LOG_HANDLE = None
LOG_NAME = None
FOCUS_PACK_PATH = None
DEBUG_MODE = None

# --- 导入MCP ---
try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    print("[致命错误] 请先运行: uv add \"mcp[cli]\" httpx", file=sys.stderr)
    sys.exit(1)

# --- 创建MCP Server ---
mcp = FastMCP("focus_pack", log_level="ERROR",port = 8888)

# --- 图片路径 ---
QUICK_SCAN_BUTTON_IMAGE = './tag_image/focus_pack/quick_scan_button.png'
QUICK_SCAN_MODE_IMAGE = './tag_image/focus_pack/quick_scan_mode.png'
QUICK_SCAN_COMPLETE_IMAGE = './tag_image/focus_pack/quick_scan_complete.png'

# --- 设备性能与等待时间 ---
DEVICE_LEVEL = 1  # 1: 低性能设备，2: 中性能设备，3: 高性能设备
SLEEP_TIME_SHORT = 1 * DEVICE_LEVEL
SLEEP_TIME_MEDIUM = 3 * DEVICE_LEVEL
SLEEP_TIME_LONG = 5 * DEVICE_LEVEL

# --- 日志函数 ---
def setup_log(log_dir = "logs"):
    # 如果不存在，则创建logs目录
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    debug_print(f"日志目录: {log_dir}")

    # 生成日志文件名（包含时间戳）
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = os.path.join(log_dir, f"focus_pack_mcp_{timestamp}.log")
    return log_filename

def close_log_file():
    """
        关闭日志文件句柄。
    """
    global LOG_HANDLE
    if LOG_HANDLE:
        LOG_HANDLE.close()
        LOG_HANDLE = None
        debug_print("日志文件已关闭。")

def debug_print(message: str):
    """
        在调试模式下，输出调试信息到标准错误流和日志文件；
        在正式运行模式下，输出到日志文件。
    """
    global LOG_HANDLE, LOG_NAME
    
    if DEBUG_MODE:
        print(message, file=sys.stderr)

    # 如果日志文件名未设置，则直接返回
    if LOG_NAME is None:
        return
    
    try:
        if LOG_HANDLE is None:
            LOG_HANDLE = open(LOG_NAME, "a", encoding="utf-8")  # 打开日志文件
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        LOG_HANDLE.write(f"[{timestamp}] {message}\n")  # 写入日志文件
        LOG_HANDLE.flush()   # 立即写入磁盘，避免数据丢失
    except Exception as e:
        print(f"[ERROR] 写入日志失败: {e}", file=sys.stderr)

# --- 权限相关函数 --- 
def is_admin():
    """
        检查当前用户是否具有管理员权限。
    """
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin(exe_path=None, params=""):
    """
        以管理员权限运行指定程序，或重启当前脚本为管理员权限。
    Args:
        exe_path: 程序的完整安装路径。如果为 None，则重启当前脚本。
        params: 程序的参数（可选）。
    """
    try:
        # if exe_path is None:
        #     exe_path = sys.executable
        #     params = f'{os.path.abspath(sys.argv[0])} --hrkill-path "{HRKILL_PATH}"'
        #     debug_print(f"尝试以管理员身份重新运行当前脚本：{params}")
        # else:
        debug_print(f"尝试以管理员身份运行指定程序：{exe_path} {params}")
        
        if ctypes.windll.shell32.ShellExecuteW(None, "runas", exe_path, params, None, 1):
            debug_print(f"[SUCCESS] 程序'{exe_path}'成功以管理员权限运行。")
            return True
        # sys.exit(0)
        # time.sleep(10)

    except Exception as e:
        debug_print(f"[ERROR] 程序启动失败：{e}")
        return False

# --- 功能函数 ---
def find_image_on_screen(image_filename, confidence_level, timeout_seconds=15, description=""):
    """
        在屏幕上查找指定的图像。
    Args:
        image_filename: 图像文件名。
        confidence_level: 图像匹配的置信度（0-1）。
        timeout_seconds: 超时时间（秒）。
        description: 图像描述（用于调试）。
    Returns:
        (x, y) 坐标元组，如果未找到则返回 None。
    """
    if not description:
        description = image_filename

    debug_print(f"正在查找图像: '{description}' (文件: {image_filename})，时间限制为{timeout_seconds}秒...")
    start_time = time.time()
    while time.time() - start_time < timeout_seconds:
        try:
            location = pyautogui.locateCenterOnScreen(image_filename, confidence=confidence_level)
            if location:
                debug_print(f"成功找到 '{description}'，坐标: {location}")
                return location
            else:
                time.sleep(SLEEP_TIME_SHORT)
        except pyautogui.ImageNotFoundException:
            time.sleep(SLEEP_TIME_SHORT)
        except FileNotFoundError:
            debug_print(f"[ERROR] 图像文件 '{image_filename}' 未找到或无法访问！")
            return None
        except Exception as e:
            if "Failed to read" in str(e) or "cannot identify image file" in str(e):
                debug_print(f"[ERROR] 无法读取或识别图像文件 '{image_filename}'。错误详情: {e}")
                return None
            debug_print(f"[ERROR] 查找图像 '{description}' 时发生其他错误: {e}")
            return None

    debug_print(f"[ERROR] 超时：在{timeout_seconds}秒内未能找到图像 '{description}',置信度为{confidence_level}。")
    return None

def click_image_at_location(location, description=""):
    """
        点击指定屏幕坐标处的图像。
    Args:
        location: 屏幕坐标元组 (x, y)。
        description: 图像描述。
    Returns:
        bool: 如果成功点击图像，返回True；否则返回False。
    """
    if location:
        pyautogui.click(location)
        debug_print(f"成功点击 '{description}'，坐标: {location}.")
        return True
    else:
        debug_print(f"[ERROR] 未能点击 '{description}'，因为未找到坐标。")
        return False

def find_and_click(image_filename, confidence_level, timeout_seconds, description):
    """
        查找屏幕上的图片并点击。若成功，则返回true，否则返回false。
    """
    img_loc = find_image_on_screen(image_filename = image_filename, confidence_level=confidence_level, timeout_seconds=timeout_seconds, description =description)
    if img_loc:
        click_image_at_location(img_loc, description)
        debug_print(f"点击{description}成功。")
        return True
    else:
        debug_print(f"[ERROR] 未找到{description}，点击失败。")
        return False

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
    
def get_scan_log(log_dir, initial_files):
    """
    获取扫描结果日志文件
    :param log_dir: 日志目录路径
    :param initial_files: 初始文件列表
    :return: 扫描结果日志文件路径
    """
    if initial_files is None:
        initial_files = set(os.listdir(log_dir))
    
    current_files = set(os.listdir(log_dir))
    new_files = current_files - initial_files
    
    if new_files:
        new_file_path = os.path.join(log_dir, new_files.pop())  
        debug_print(f"检测到新日志文件: {new_file_path}")
        return new_file_path


# --- MCP工具 ---
@mcp.tool() 
def start_app(exe_path):
    """
        以管理员身份启动软件。
    Args：
        path: 软件的完整安装路径。
    """    
    if not exe_path or not os.path.exists(exe_path):
        msg = f"[ERROR] 应用程序路径无效或不存在: {exe_path}"
        debug_print(msg)
        return False
    
    debug_print(f"正在尝试启动软件: {exe_path}")
    try:
        if not run_as_admin(exe_path):
            # 如果管理员权限运行失败，则尝试以普通用户身份运行
            debug_print(f"[WARN] 管理员权限运行失败，尝试以普通用户身份启动应用程序: {exe_path}")
            app = subprocess.Popen(exe_path)
            debug_print(f"[SUCCESS] 应用程序已成功启动，进程号为{app.pid}。")
            return True

    except Exception as e:
        msg = f"[ERROR] 启动应用程序 '{exe_path}' 时发生错误: {e}"
        debug_print(msg)
        return False
    
@mcp.tool()
def quick_scan():
    """
        执行Focus_Pack软件（忽略大小写）的快速扫描功能。
    Args：
        None
    """
    # 1. 打开Focus_Pack软件
    debug_print(f"[Step 1] 打开Focus_Pack软件")
    if start_app(FOCUS_PACK_PATH) is False:
        return "[ERROR] 启动Focus_Pack软件失败，请检查路径或权限。"
    time.sleep(SLEEP_TIME_LONG)
    debug_print(f"Focus_Pack软件已启动，请确保处于首页，否则后续可能执行失败。")

    # 获取当前用户的AppData\Roaming目录
    appdata_roaming = os.path.expanduser('~\\AppData\\Roaming')
    # 获取扫描前的目录
    focus_logs_path = os.path.join(appdata_roaming, 'FocusLogs')
    initial_files = get_initial_files(focus_logs_path)
    
    # 2. 点击 “ 快速扫描 ” 按钮
    debug_print(f"[Step 2] 点击 “ 快速扫描 ” 按钮")
    if not find_and_click(QUICK_SCAN_BUTTON_IMAGE, confidence_level=0.8, timeout_seconds=15, description="快速扫描按钮"):
        return "[ERROR] 未能找到快速扫描按钮，或点击失败，请查看最新操作日志溯源。"
    time.sleep(SLEEP_TIME_LONG)

    # 3. 检测是否正在扫描
    debug_print(f"[Step 3] 检测是否正在扫描")
    if find_image_on_screen(QUICK_SCAN_MODE_IMAGE, confidence_level=0.8, timeout_seconds=15, description="快速扫描模式"):
        debug_print("正在执行快速扫描。")
    else:
        msg = "[ERROR] 未成功执行快速扫描，请查看最新操作日志溯源。"
        debug_print(msg)
        return msg
    time.sleep(SLEEP_TIME_LONG)

    # 4. 检测是否扫描完成（时长可调节）
    interval = 600   
    debug_print(f"[Step 4] 检测是否扫描完成（时长为{interval}s,可调节）")
    start_time = time.time()
    img_loc = find_image_on_screen(QUICK_SCAN_COMPLETE_IMAGE, confidence_level=0.8, timeout_seconds=interval, description="快速查杀完成")
    if img_loc:
        msg = f"[SUCCESS] 检测到快速扫描完成标志(坐标为{img_loc}, 用时{time.time() - start_time}秒)，快速扫描已完成。"
        debug_print(msg)
    
    # 5. 获取扫描结果日志
    debug_print(f"[Step 5] 获取扫描结果日志")
    debug_print(f"扫描结果日志目录: {focus_logs_path}")
    scan_log = get_scan_log(focus_logs_path, initial_files)
    if scan_log:
        msg = f"[SUCCESS] 扫描新结果日志文件: {scan_log}，请用户自主查看。"
        debug_print(msg)
        return msg
    else:
        msg = "[WARN] 快速扫描完成，但未成功获取扫描结果日志。"
        debug_print(msg)
        return msg

# --- 主函数 ---
def main():
    """
        根据是否处于调试模式，执行不同的操作。
    """
    # 获取参数
    global FOCUS_PACK_PATH, DEBUG_MODE, LOG_NAME
    parser = argparse.ArgumentParser(description="Focus_Pack MCP工具")
    parser.add_argument('--focus-pack-path', type=str, required=True, help='Focus_Pack软件的完整路径')
    parser.add_argument('--debug', action='store_true', help='调试模式')
    args = parser.parse_args()
    FOCUS_PACK_PATH = args.focus_pack_path
    DEBUG_MODE = args.debug
    LOG_NAME = setup_log("logs/focus_pack")
    
    # 1. 检查VS code权限
    debug_print("--- VS code 管理员权限检查 ---")
    if not is_admin():
        msg = "未检测到管理员权限，为了使用Focus_Pack MCP，请以管理员身份打开VS Code。"
        debug_print(msg)
        print(msg, file=sys.stderr)
        return msg
    else:
        debug_print("当前已具备管理员权限。")

    # 2. 运行
    if DEBUG_MODE:
        print("--- 当前处于调试模式 ---")
        quick_scan()
    else:
        print("--- 当前处于正式运行模式 ---")
        mcp.run(transport='stdio')

# --- 主程序入口 ---
if __name__ == "__main__":
    try:
        main()
    finally:
        close_log_file()
