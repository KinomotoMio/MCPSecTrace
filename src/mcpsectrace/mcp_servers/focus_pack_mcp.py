import ctypes
import io
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import pyautogui
import win32gui

# --- 输出使用utf-8编码（仅在非测试环境） --
if "pytest" not in sys.modules:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

from mcpsectrace.config import get_config_value
from mcpsectrace.utils.image_recognition import ImageRecognition

# --- 全局变量 ---
LOG_HANDLE = None
LOG_NAME = None
FOCUS_PACK_PATH = None

# --- 导入MCP ---
try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    print('[致命错误] 请先运行: uv add "mcp[cli]" httpx', file=sys.stderr)
    sys.exit(1)

# --- 创建MCP Server ---
mcp = FastMCP("focus_pack", log_level="ERROR", port=8888)


def get_sleep_time(base_type: str) -> float:
    """根据设备性能等级和基础时间类型计算实际等待时间"""
    device_level = get_config_value("device_level", default=2)

    base_times = {
        "short": get_config_value("automation.sleep_short_base", default=1),
        "medium": get_config_value("automation.sleep_medium_base", default=3),
        "long": get_config_value("automation.sleep_long_base", default=5),
    }

    base_time = base_times.get(base_type, 1)
    return base_time * device_level


# --- 日志函数 ---
def setup_log():
    # 计算项目根目录(向上3层)
    project_root = Path(__file__).parent.parent.parent.parent
    log_dir = project_root / "logs" / "focus_pack"

    # 如果不存在，则创建目录
    log_dir.mkdir(parents=True, exist_ok=True)
    debug_print(f"日志目录: {log_dir}")

    # 生成日志文件名（包含时间戳）
    timestamp = datetime.now().strftime("%Y%m%d")
    log_filename = log_dir / f"focus_pack_mcp_{timestamp}.log"
    return str(log_filename)


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

    debug_mode = get_config_value("debug_mode", default=False)
    if debug_mode:
        print(message, file=sys.stderr)

    # 如果日志文件名未设置，则直接返回
    if LOG_NAME is None:
        return

    try:
        if LOG_HANDLE is None:
            LOG_HANDLE = open(LOG_NAME, "a", encoding="utf-8")  # 打开日志文件

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        LOG_HANDLE.write(f"[{timestamp}] {message}\n")  # 写入日志文件
        LOG_HANDLE.flush()  # 立即写入磁盘，避免数据丢失
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

        if ctypes.windll.shell32.ShellExecuteW(
            None, "runas", exe_path, params, None, 1
        ):
            debug_print(f"[SUCCESS] 程序'{exe_path}'成功以管理员权限运行。")
            return True
        # sys.exit(0)
        # time.sleep(10)

    except Exception as e:
        debug_print(f"[ERROR] 程序启动失败：{e}")
        return False


# --- 功能函数 ---
def find_image_on_screen(
    image_filename, confidence_level, timeout_seconds=15, description=""
):
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

    debug_print(
        f"正在查找图像: '{description}' (文件: {image_filename})，时间限制为{timeout_seconds}秒..."
    )
    start_time = time.time()
    while time.time() - start_time < timeout_seconds:
        try:
            location = pyautogui.locateCenterOnScreen(
                image_filename, confidence=confidence_level
            )
            if location:
                debug_print(f"成功找到 '{description}'，坐标: {location}")
                return location
            else:
                time.sleep(get_sleep_time("short"))
        except pyautogui.ImageNotFoundException:
            time.sleep(get_sleep_time("short"))
        except FileNotFoundError:
            debug_print(f"[ERROR] 图像文件 '{image_filename}' 未找到或无法访问！")
            return None
        except Exception as e:
            if "Failed to read" in str(e) or "cannot identify image file" in str(e):
                debug_print(
                    f"[ERROR] 无法读取或识别图像文件 '{image_filename}'。错误详情: {e}"
                )
                return None
            debug_print(f"[ERROR] 查找图像 '{description}' 时发生其他错误: {e}")
            return None

    debug_print(
        f"[ERROR] 超时：在{timeout_seconds}秒内未能找到图像 '{description}',置信度为{confidence_level}。"
    )
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
    img_loc = find_image_on_screen(
        image_filename=image_filename,
        confidence_level=confidence_level,
        timeout_seconds=timeout_seconds,
        description=description,
    )
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


def find_image_on_screen_by_ratio(
    x_ratio, y_ratio, timeout_seconds=None, description=""
):
    """
    基于相对位置定位元素（基于前台窗口）。

    Args:
        x_ratio: X轴相对位置（0.0 - 1.0，0表示窗口最左边，1表示最右边）
        y_ratio: Y轴相对位置（0.0 - 1.0，0表示窗口最上边，1表示最下边）
        timeout_seconds: 超时时间（秒）。
        description: 元素描述（用于调试）。
    Returns:
        (x, y) 绝对屏幕坐标元组。
    """
    if timeout_seconds is None:
        timeout_seconds = get_config_value("automation.find_timeout", default=15)

    if not description:
        description = f"位置({x_ratio:.2f}, {y_ratio:.2f})"

    debug_print(
        f"正在定位元素: '{description}' (相对位置: {x_ratio:.2f}, {y_ratio:.2f})，时间限制为{timeout_seconds}秒..."
    )
    start_time = time.time()
    while time.time() - start_time < timeout_seconds:
        try:
            # 获取前台窗口句柄
            hwnd = win32gui.GetForegroundWindow()
            if not hwnd:
                debug_print("未找到前台窗口，重试中...")
                time.sleep(get_sleep_time("short"))
                continue

            # 获取窗口位置和大小
            rect = win32gui.GetWindowRect(hwnd)
            win_left, win_top, win_right, win_bottom = rect
            win_width = win_right - win_left
            win_height = win_bottom - win_top

            # 计算绝对坐标（基于窗口）
            abs_x = int(win_left + win_width * x_ratio)
            abs_y = int(win_top + win_height * y_ratio)
            location = (abs_x, abs_y)

            debug_print(f"找到 '{description}'，绝对坐标: {location}")
            debug_print(
                f"窗口信息: 位置({win_left}, {win_top}), 大小 {win_width}x{win_height}"
            )
            return location

        except Exception as e:
            debug_print(f"定位元素 '{description}' 时发生错误: {e}")
            time.sleep(get_sleep_time("short"))

    debug_print(f"超时：在 {timeout_seconds} 秒内未能定位元素 '{description}'。")
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
        # 先将鼠标移动到目标位置（可见的移动，便于调试）
        pyautogui.moveTo(location[0], location[1], duration=0.5)
        time.sleep(0.2)  # 等待鼠标位置稳定
        # 再点击
        pyautogui.click()
        debug_print(f"成功点击 '{description}' 在坐标: {location}")
        return True
    else:
        debug_print(f"未能点击 '{description}'，因为未找到坐标。")
        return False


def capture_window_region(
    x_start_ratio=0.5,
    y_start_ratio=0.0,
    x_end_ratio=1.0,
    y_end_ratio=1.0,
    save_path=None,
):
    """
    截取前台窗口的指定区域

    Args:
        x_start_ratio: 起始X坐标比例（0.0-1.0）
        y_start_ratio: 起始Y坐标比例（0.0-1.0）
        x_end_ratio: 结束X坐标比例（0.0-1.0）
        y_end_ratio: 结束Y坐标比例（0.0-1.0）
        save_path: 保存路径，如果为None则不保存

    Returns:
        PIL.Image 对象或 None
    """
    try:
        # 获取前台窗口句柄
        hwnd = win32gui.GetForegroundWindow()
        if not hwnd:
            debug_print("未找到前台窗口")
            return None

        # 获取窗口位置和大小
        rect = win32gui.GetWindowRect(hwnd)
        win_left, win_top, win_right, win_bottom = rect
        win_width = win_right - win_left
        win_height = win_bottom - win_top

        # 计算区域坐标
        crop_left = int(win_left + win_width * x_start_ratio)
        crop_top = int(win_top + win_height * y_start_ratio)
        crop_right = int(win_left + win_width * x_end_ratio)
        crop_bottom = int(win_top + win_height * y_end_ratio)

        # 截取屏幕
        screenshot = pyautogui.screenshot()
        cropped = screenshot.crop((crop_left, crop_top, crop_right, crop_bottom))

        # 保存截图
        if save_path:
            cropped.save(save_path)
            debug_print(f"截图已保存到: {save_path}")

        return cropped

    except Exception as e:
        debug_print(f"截取窗口区域时出错: {e}")
        return None


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
            debug_print(
                f"[WARN] 管理员权限运行失败，尝试以普通用户身份启动应用程序: {exe_path}"
            )
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
    time.sleep(get_sleep_time("long"))
    debug_print(f"Focus_Pack软件已启动，请确保处于首页，否则后续可能执行失败。")

    # 获取当前用户的AppData\Roaming目录
    appdata_roaming = os.path.expanduser("~\\AppData\\Roaming")
    # 获取扫描前的目录
    focus_logs_path = os.path.join(appdata_roaming, "FocusLogs")
    initial_files = get_initial_files(focus_logs_path)

    # 创建日志目录
    log_dir = Path(__file__).parent / "artifacts" / "focus_pack"
    log_dir.mkdir(parents=True, exist_ok=True)

    # 2. 点击'快速扫描'按钮（使用相对位置定位）
    debug_print(f"[Step 2] 点击'快速扫描'按钮")
    quick_scan_pos = get_config_value(
        "positions.focus_pack.start_scan_button", default=[0.1, 0.128]
    )
    img_loc = find_image_on_screen_by_ratio(
        x_ratio=quick_scan_pos[0],
        y_ratio=quick_scan_pos[1],
        timeout_seconds=15,
        description="快速扫描按钮",
    )
    if img_loc:
        click_image_at_location(img_loc, description="快速扫描按钮")
        debug_print("点击快速扫描按钮成功。")
    else:
        debug_print("点击快速扫描按钮失败。")
        return "点击快速扫描按钮失败。"
    time.sleep(get_sleep_time("long"))

    # 3. 检测是否正在扫描（使用OCR识别"扫描中"字符串）
    debug_print(f"[Step 3] 检测是否正在扫描")
    screenshot_path = log_dir / f"scan_check_{datetime.now().strftime('%Y%m%d')}.png"
    region_img = capture_window_region(
        x_start_ratio=0.0,
        y_start_ratio=0.8,
        x_end_ratio=0.2,
        y_end_ratio=1.0,
        save_path=str(screenshot_path),
    )

    if region_img is None:
        debug_print("截取窗口右上部分失败。")
        return "截取窗口右上部分失败。"

    # 使用OCR识别截图中是否包含"扫描中"字符串
    try:
        recognizer = ImageRecognition()
        if recognizer.contains_text(
            str(screenshot_path), "当前模式", case_sensitive=False
        ):
            debug_print(f"正在执行快速扫描。截图已保存到: {screenshot_path}")
        else:
            debug_print(f"未成功执行快速扫描。截图已保存到: {screenshot_path}")
            return f"未成功执行快速扫描。截图路径: {screenshot_path}"
    except Exception as e:
        import traceback

        error_msg = f"OCR识别过程中出错: {e}\n{traceback.format_exc()}"
        debug_print(error_msg)
        return error_msg
    time.sleep(get_sleep_time("long"))

    # 4. 检测是否扫描完成（每30秒截取页面上半部分，使用OCR识别"扫描完成"字符串）
    start_time = time.time()
    interval = 600  # 10分钟
    check_interval = 30  # 每30秒检测一次
    last_check_time = 0
    recognizer = ImageRecognition()

    debug_print(f"[Step 4] 检测是否扫描完成（时长{interval}s，可调节）")
    debug_print("开始监控扫描进度，每30秒检测一次...")

    while time.time() - start_time < interval:
        current_time = time.time()

        # 每30秒检测一次
        if current_time - last_check_time >= check_interval:
            last_check_time = current_time
            elapsed_time = current_time - start_time

            # 截取页面上半部分
            screenshot_path = log_dir / f"scan_progress.png"
            region_img = capture_window_region(
                x_start_ratio=0.0,
                y_start_ratio=0.0,
                x_end_ratio=0.2,
                y_end_ratio=0.2,
                save_path=str(screenshot_path),
            )

            if region_img is None:
                debug_print("截取窗口上半部分失败。")
                continue

            # 使用OCR识别是否包含"扫描完成"字符串
            if recognizer.contains_text(
                str(screenshot_path), "提示", case_sensitive=False
            ):
                msg = f"[SUCCESS] 检测到'提示'字符，快速扫描已完成。耗时: {int(elapsed_time)}秒，截图保存在: {screenshot_path}"
                debug_print(msg)
                break

            debug_print(f"[{int(elapsed_time)}s] 继续等待扫描完成...")

        time.sleep(1)
    else:
        # 超时返回
        debug_print("扫描监控超时（10分钟）")
        return f"扫描监控超时，最后的截图保存在: {log_dir}"

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
    # 从配置文件读取Focus Pack路径
    global FOCUS_PACK_PATH, LOG_NAME
    FOCUS_PACK_PATH = get_config_value("paths.focus_pack_exe", default="")

    # 验证Focus Pack路径
    if not FOCUS_PACK_PATH:
        error_msg = "错误：未配置Focus Pack路径。请在 config/user_settings.toml 中设置 paths.focus_pack_exe"
        print(error_msg, file=sys.stderr)
        debug_print(error_msg)
    elif not os.path.exists(FOCUS_PACK_PATH):
        warning_msg = f"警告：Focus Pack路径不存在: {FOCUS_PACK_PATH}"
        print(warning_msg, file=sys.stderr)
        debug_print(warning_msg)
    else:
        debug_print(f"已从配置文件加载Focus Pack路径: {FOCUS_PACK_PATH}")

    LOG_NAME = setup_log()

    # 1. 检查VS code权限
    debug_print("--- VS code 管理员权限检查 ---")
    if not is_admin():
        msg = "未检测到管理员权限，为了使用Focus Pack MCP，请以管理员身份打开VS Code。"
        debug_print(msg)
        print(msg, file=sys.stderr)
        return msg
    else:
        debug_print("当前已具备管理员权限。")

    # 2. 运行
    debug_mode = get_config_value("debug_mode", default=False)
    if debug_mode:
        print("--- 当前处于调试模式 ---")
        quick_scan()
    else:
        print("--- 当前处于正式运行模式 ---")
        # mcp.run(transport="stdio")
        # start_app(FOCUS_PACK_PATH)
        quick_scan()
        # mcp.run(transport="stdio")


# --- 主程序入口 ---
if __name__ == "__main__":
    try:
        main()
    finally:
        close_log_file()
