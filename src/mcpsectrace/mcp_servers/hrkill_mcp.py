import ctypes
import io
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import psutil
import pyautogui
import win32con
import win32gui

# --- 输出使用utf-8编码（仅在非测试环境） --
if "pytest" not in sys.modules:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")
from mcpsectrace.config import get_config_value
from mcpsectrace.utils.image_recognition import ImageRecognition

# --- 全局变量 ---
LOG_HANDLE = None  # 日志文件句柄
LOG_NAME = None
HRKILL_PATH = None

# --- 导入MCP ---
try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    print('[致命错误] 请先运行: uv add "mcp[cli]" httpx', file=sys.stderr)
    sys.exit(1)

# --- 创建MCP Server ---
mcp = FastMCP("hrkill", log_level="ERROR", port=8888)


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
    log_dir = project_root / "logs" / "hrkill"

    # 如果不存在，则创建目录
    log_dir.mkdir(parents=True, exist_ok=True)
    debug_print(f"日志目录: {log_dir}")

    # 生成日志文件名（包含时间戳）
    timestamp = datetime.now().strftime("%Y%m%d")
    log_filename = log_dir / f"hrkill_mcp_runtime_{timestamp}.log"
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


# --- 功能函数 ---
def find_image_on_screen(x_ratio, y_ratio, timeout_seconds=None, description=""):
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


def find_and_click(x_ratio, y_ratio, timeout_seconds=15, description=""):
    """
    基于相对位置定位并点击元素。若成功，则返回True，否则返回False。
    """
    location = find_image_on_screen(
        x_ratio=x_ratio,
        y_ratio=y_ratio,
        timeout_seconds=timeout_seconds,
        description=description,
    )
    if location:
        click_image_at_location(location, description)
        debug_print(f"点击{description}成功。")
        return True
    else:
        debug_print(f"[ERROR] 未找到{description}，点击失败。")
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


# --- 进程和窗口管理函数 ---
def is_process_running(process_name):
    """
    检查指定进程是否正在运行

    Args:
        process_name: 进程名称(如 "HRKill.exe")

    Returns:
        bool: 进程是否正在运行
    """
    try:
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] and proc.info['name'].lower() == process_name.lower():
                debug_print(f"检测到进程 {process_name} 正在运行")
                return True
        return False
    except Exception as e:
        debug_print(f"[ERROR] 检查进程时出错: {e}")
        return False


def bring_window_to_front(window_title_keyword, silent=False):
    """
    将包含指定关键字的窗口置顶

    Args:
        window_title_keyword: 窗口标题关键字(如 "火绒")
        silent: 是否静默模式(不输出日志)

    Returns:
        bool: 是否成功找到并置顶窗口
    """
    def enum_windows_callback(hwnd, result):
        if win32gui.IsWindowVisible(hwnd):
            window_title = win32gui.GetWindowText(hwnd)
            if window_title_keyword.lower() in window_title.lower():
                result.append((hwnd, window_title))

    try:
        windows = []
        win32gui.EnumWindows(enum_windows_callback, windows)

        if windows:
            hwnd, title = windows[0]
            # 显示窗口并置顶
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)  # 先还原窗口(如果最小化)
            win32gui.SetForegroundWindow(hwnd)  # 置顶窗口
            if not silent:
                debug_print(f"[SUCCESS] 窗口 '{title}' 已置顶")
            return True
        else:
            if not silent:
                debug_print(f"[WARN] 未找到包含 '{window_title_keyword}' 的窗口")
            return False
    except Exception as e:
        if not silent:
            debug_print(f"[ERROR] 窗口置顶失败: {e}")
        return False


def ensure_hrkill_window_active(window_keyword="火绒恶性木马专杀工具"):
    """
    确保 HRKill 窗口在前台

    Args:
        window_keyword: HRKill 窗口标题关键字

    Returns:
        bool: 是否成功将窗口置顶
    """
    # 第一步：检查当前前台窗口是否已经是 HRKill 相关
    try:
        hwnd = win32gui.GetForegroundWindow()
        if hwnd:
            current_title = win32gui.GetWindowText(hwnd)
            debug_print(f"当前窗口: {current_title}")
            # 如果当前窗口已经是 HRKill 相关窗口，不需要切换
            if window_keyword in current_title:
                return True
    except:
        pass

    # 第二步：当前窗口不是 HRKill，需要将 HRKill 窗口置顶
    # 收集所有 HRKill 相关窗口
    def enum_windows_callback(hwnd, result):
        if win32gui.IsWindowVisible(hwnd):
            window_title = win32gui.GetWindowText(hwnd)
            if window_keyword in window_title:
                result.append((hwnd, window_title))

    try:
        windows = []
        win32gui.EnumWindows(enum_windows_callback, windows)

        if not windows:
            return False

        # 置顶找到的第一个窗口
        hwnd, title = windows[0]
        current_title = win32gui.GetWindowText(hwnd)
        debug_print(f"置顶第一个窗口: {current_title}")
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        win32gui.SetForegroundWindow(hwnd)
        time.sleep(0.5)  # 等待窗口切换完成
        return True

    except Exception:
        pass

    return False


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
def scan_virus():
    """
        执行hrkill软件的病毒查杀功能。
    Args：
        None
    """
    # 1. 打开hrkill软件
    debug_print(f"[Step 1] 打开hrkill软件")
    if start_app(HRKILL_PATH) is False:
        return "[ERROR] 启动hrkill软件失败，请检查路径或权限。"
    time.sleep(get_sleep_time("long"))
    debug_print(
        "hrkill软件已启动，请确保处于首页，否则后续可能执行失败。"
    )  # 能否显示在mcp上

    # 1.5. 检查是否在结果页面，如果是则返回主页
    debug_print("[Step 1.5] 检查是否需要返回主页")
    ensure_hrkill_window_active()

    # 创建截图保存目录
    log_dir = Path(__file__).parent / "artifacts" / "hrkill"
    log_dir.mkdir(parents=True, exist_ok=True)

    # 截取上半部分检查是否有"查杀完成"
    check_screenshot = log_dir / "startup_check.png"
    region_img = capture_window_region(
        x_start_ratio=0.0,
        y_start_ratio=0.0,
        x_end_ratio=1.0,
        y_end_ratio=0.5,
        save_path=str(check_screenshot),
    )

    if region_img is not None:
        recognizer = ImageRecognition()
        if recognizer.contains_text(str(check_screenshot), "查杀完成", case_sensitive=False):
            debug_print("[WARN] 检测到'查杀完成'，当前不在主界面，点击(0.5, 0.67)返回主页")

            # 点击返回主页按钮
            return_pos = find_image_on_screen(
                x_ratio=0.5,
                y_ratio=0.67,
                timeout_seconds=5,
                description="返回主页按钮",
            )
            if return_pos:
                click_image_at_location(return_pos, description="返回主页按钮")
                time.sleep(get_sleep_time("medium"))
            else:
                debug_print("[WARN] 未找到返回主页按钮位置，尝试继续")

            # 重新打开程序
            debug_print("重新打开hrkill软件...")
            if start_app(HRKILL_PATH) is False:
                return "[ERROR] 重新启动hrkill软件失败"
            time.sleep(get_sleep_time("long"))
            debug_print("[SUCCESS] 已重新打开hrkill软件")
        else:
            debug_print("[SUCCESS] 当前在主界面，继续执行")
    else:
        debug_print("[WARN] 截图失败，跳过主页检查")

    # 2. 点击'开始扫描按钮'（使用相对位置定位）
    debug_print(f"[Step 2] 点击'开始扫描按钮'")
    # 确保窗口在前台（用于点击）
    ensure_hrkill_window_active()
    start_scan_pos = get_config_value(
        "positions.hrkill.start_scan_button", default=[0.5, 0.72]
    )
    img_loc = find_image_on_screen(
        x_ratio=start_scan_pos[0],
        y_ratio=start_scan_pos[1],
        timeout_seconds=15,
        description="开始扫描按钮",
    )
    if img_loc:
        click_image_at_location(img_loc, description="开始扫描按钮")
        debug_print("点击开始扫描按钮成功。")
    else:
        debug_print("点击开始扫描按钮失败。")
        return "点击开始扫描按钮失败。"
    time.sleep(get_sleep_time("long"))

    # 3. 检测是否正在查杀病毒（使用OCR识别"暂停"字符串）
    debug_print(f"[Step 3] 检测是否正在查杀病毒")
    # 确保窗口在前台（用于截图）
    ensure_hrkill_window_active()

    # 截取右上部分（从50%宽度到100%，从0%高度到50%）
    screenshot_path = log_dir / f"scan_check.png"
    region_img = capture_window_region(
        x_start_ratio=0.5,
        y_start_ratio=0.0,
        x_end_ratio=1.0,
        y_end_ratio=0.5,
        save_path=str(screenshot_path),
    )

    if region_img is None:
        debug_print("截取窗口右上部分失败。")
        return "截取窗口右上部分失败。"

    # 使用OCR识别截图中是否包含"暂停"字符串
    try:
        recognizer = ImageRecognition()
        if recognizer.contains_text(str(screenshot_path), "暂停", case_sensitive=False):
            debug_print(
                f"检测到'暂停'字符，说明正在执行病毒查杀。截图已保存到: {screenshot_path}"
            )
        else:
            debug_print(
                f"未找到'暂停'字符，说明未成功执行病毒查杀。截图已保存到: {screenshot_path}"
            )
            return (
                f"未找到'暂停'字符，说明未成功执行病毒查杀。截图路径: {screenshot_path}"
            )
    except Exception as e:
        import traceback

        error_msg = f"OCR识别过程中出错: {e}\n{traceback.format_exc()}"
        debug_print(error_msg)
        return error_msg
    time.sleep(get_sleep_time("long"))

    # 4. 检测是否扫描完成（每15秒截取页面上半部分，使用OCR识别"查杀完成"字符串）
    start_time = time.time()
    interval = 3600  # 60分钟
    check_interval = 15  # 每15秒检测一次
    last_check_time = 0
    recognizer = ImageRecognition()

    debug_print(f"[Step 4] 检测是否扫描完成（时长{interval}s，可调节）")
    debug_print("开始监控扫描进度，每15秒检测一次...")

    while time.time() - start_time < interval:
        current_time = time.time()

        # 每15秒检测一次
        if current_time - last_check_time >= check_interval:
            last_check_time = current_time
            elapsed_time = current_time - start_time

            # 确保窗口在前台（用于截图）
            ensure_hrkill_window_active()

            # 截取页面上半部分
            screenshot_path = log_dir / f"scan_progress.png"
            region_img = capture_window_region(
                x_start_ratio=0.0,
                y_start_ratio=0.0,
                x_end_ratio=1.0,
                y_end_ratio=0.5,
                save_path=str(screenshot_path),
            )

            if region_img is None:
                debug_print("截取窗口上半部分失败。")
                continue

            # 使用OCR识别是否包含"查杀完成"字符串
            if recognizer.contains_text(
                str(screenshot_path), "查杀完成", case_sensitive=False
            ):
                msg = f"[SUCCESS] 检测到'查杀完成'字符，病毒查杀已完成。耗时: {int(elapsed_time)}秒，截图保存在: {screenshot_path}"
                debug_print(msg)
                return msg

            debug_print(f"[{int(elapsed_time)}s] 继续等待扫描完成...")

        time.sleep(1)

    # 超时返回
    debug_print("扫描监控超时（60分钟）")
    return f"扫描监控超时，最后的截图保存在: {log_dir}"


# --- 主函数 ---
def main():
    """
    主函数，用于初始化参数并启动MCP服务器。
    """
    # 参数设置
    global HRKILL_PATH, LOG_NAME

    # 从配置文件读取HRKill路径
    HRKILL_PATH = get_config_value("paths.hrkill_exe", default="")

    # 验证HRKill路径
    if not HRKILL_PATH:
        error_msg = "错误：未配置HRKill路径。请在 config/user_settings.toml 中设置 paths.hrkill_exe"
        print(error_msg, file=sys.stderr)
        debug_print(error_msg)
    elif not os.path.exists(HRKILL_PATH):
        warning_msg = f"警告：HRKill路径不存在: {HRKILL_PATH}"
        print(warning_msg, file=sys.stderr)
        debug_print(warning_msg)
    else:
        debug_print(f"已从配置文件加载HRKill路径: {HRKILL_PATH}")

    LOG_NAME = setup_log()

    # 1. 检查VS code权限
    debug_print("--- VS code 管理员权限检查 ---")
    if not is_admin():
        msg = "未检测到管理员权限，为了使用hrkill MCP，请以管理员身份打开VS Code。"
        debug_print(msg)
        print(msg, file=sys.stderr)
        return msg
    else:
        debug_print("当前已具备管理员权限。")

    # 2. 运行
    debug_mode = get_config_value("debug_mode", default=False)
    if debug_mode:
        debug_print("--- 当前处于调试模式 ---")
        scan_virus()
    else:
        debug_print("--- 当前处于MCP运行模式 ---")
        # scan_virus()
        mcp.run(transport="stdio")


# --- 主程序入口 ---
if __name__ == "__main__":
    main()
