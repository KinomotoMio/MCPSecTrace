import asyncio
import io
import os
import shutil  # 文件复制
import sqlite3  # 数据库
import subprocess
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Optional

import pyautogui
import pyperclip
import win32gui
from PIL import Image

# --- 输出使用utf-8编码（仅在非测试环境） --
if "pytest" not in sys.modules:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")
from mcpsectrace.config import get_config_value
from mcpsectrace.utils.image_recognition import ImageRecognition

# --- 导入MCP ---
try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    debug_print('[致命错误] 请先运行: uv add "mcp[cli]" httpx')
    sys.exit(1)

mcp = FastMCP("huorong", log_level="ERROR", port=8888)

# --- 全局变量 ---
LOG_HANDLE = None  # 日志文件句柄
LOG_NAME = None
HUORONG_PATH = ""  # 将在main()中从配置文件加载


# --- 日志函数 ---
def setup_log():
    # 计算项目根目录(向上3层)
    project_root = Path(__file__).parent.parent.parent.parent
    log_dir = project_root / "logs" / "huorong"

    # 如果不存在，则创建目录
    log_dir.mkdir(parents=True, exist_ok=True)
    debug_print(f"日志目录: {log_dir}")

    # 生成日志文件名（包含时间戳）
    timestamp = datetime.now().strftime("%Y%m%d")
    log_filename = log_dir / f"huorong_mcp_{timestamp}.log"
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
    基于相对位置定位并点击元素。若成功，则返回true，否则返回false。
    """
    img_loc = find_image_on_screen(
        x_ratio=x_ratio,
        y_ratio=y_ratio,
        timeout_seconds=timeout_seconds,
        description=description,
    )
    if img_loc:
        click_image_at_location(img_loc, description)
        debug_print("点击{0}成功。".format(description))
        return True
    else:
        debug_print("未找到{0}，点击失败。".format(description))
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


def ret2_top_page():
    """
    执行完功能后，返回首页。
    """
    # 从配置文件读取完成按钮的相对位置
    complete_button_pos = get_config_value(
        "positions.huorong.complete_button_alt", default=[0.9, 0.128]
    )
    x_ratio, y_ratio = complete_button_pos[0], complete_button_pos[1]

    img_loc = find_image_on_screen(
        x_ratio=x_ratio,
        y_ratio=y_ratio,
        timeout_seconds=15,
        description="完成按钮",
    )
    if img_loc:
        click_image_at_location(img_loc, description="完成按钮")
        debug_print("已经返回首页。")


def read_QuarantineEx_db(db_path, file_path):
    # 连接数据库
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 查看所有表名
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    table_name = tables[0][0]  # 第一张表（可能不准确）

    # 查询fn和vn字段
    cursor.execute(f"SELECT fn, vn FROM {table_name};")
    rows = cursor.fetchall()

    # 写入到log文件
    with open(file_path, "w", encoding="utf-8") as f:
        for fn, vn in rows:
            f.write(f"文件名: {fn}, 病毒名: {vn}\n")

    # 关闭连接
    conn.close()


def read_wlfile_db(db_path, file_path):
    # 连接数据库
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 查询fn字段
    cursor.execute(f"SELECT fn FROM TrustRegion_60;")
    rows = cursor.fetchall()

    # 写入到log文件
    with open(file_path, "w", encoding="utf-8") as f:
        for fn in rows:
            f.write(f"{fn}\n")

    # 关闭连接
    conn.close()


# --- MCP工具 ---
@mcp.tool()
def start_huorong(path):
    """
        启动火绒安全软件（简称火绒）。
        启动后会检测是否在主界面，如果不在则自动返回主界面。
    Args：
        path: 火绒安全软件的完整安装路径（即HUORONG_PATH）。
    Returns：
        int: 如果成功启动，返回启动后的进程ID (PID)。
        None: 如果路径无效，或者在启动过程中发生错误，返回 None。
    """
    try:
        if not path or not os.path.exists(path):
            debug_print(
                f"错误：应用程序路径 '{path}' 无效或不存在。\n\
                        请确保 HUORONG_PATH 变量已正确设置为火绒安全的启动程序路径。\n\
                        脚本将尝试在不启动新进程的情况下继续（假设火绒已打开）。"
            )
            return None
        debug_print(f"正在尝试启动火绒: {path}")
        app = subprocess.Popen(path)
        debug_print(f"应用程序已启动 (进程ID: {app.pid})。")

        # 等待应用加载
        time.sleep(get_sleep_time("medium"))

        # 检测是否在主界面（通过检测右上角是否有"完成"字符）
        debug_print("检测是否在主界面...")
        try:
            # 创建截图保存目录
            log_dir = Path(__file__).parent / "artifacts" / "huorong"
            log_dir.mkdir(parents=True, exist_ok=True)

            # 截取右上角区域（80%-100%宽度，0%-20%高度）
            screenshot_path = log_dir / f"startup_check.png"
            region_img = capture_window_region(
                x_start_ratio=0.8,
                y_start_ratio=0.0,
                x_end_ratio=1.0,
                y_end_ratio=0.2,
                save_path=str(screenshot_path),
            )

            if region_img is not None:
                recognizer = ImageRecognition()
                if recognizer.contains_text(str(screenshot_path), "完成", case_sensitive=False):
                    debug_print("[WARN] 检测到'完成'字符，当前不在主界面，点击返回主页...")

                    # 从配置文件读取完成按钮的相对位置
                    complete_button_pos = get_config_value(
                        "positions.huorong.complete_button", default=[0.92, 0.12]
                    )
                    return_pos = find_image_on_screen(
                        x_ratio=complete_button_pos[0],
                        y_ratio=complete_button_pos[1],
                        timeout_seconds=5,
                        description="返回主页按钮",
                    )
                    if return_pos:
                        click_image_at_location(return_pos, description="返回主页按钮")
                        debug_print("[SUCCESS] 已点击返回主页按钮")
                        time.sleep(get_sleep_time("short"))
                    else:
                        debug_print("[WARN] 未找到返回主页按钮位置")
                else:
                    debug_print("[SUCCESS] 当前已在主界面")
            else:
                debug_print("[WARN] 截图失败，跳过主页检查")

        except Exception as check_error:
            debug_print(f"[WARN] 主界面检测时出错: {check_error}，继续执行...")

        return app.pid
    except Exception as e:
        debug_print(f"启动应用程序 '{path}' 时发生错误: {e}")
        debug_print("脚本将尝试在不启动新进程的情况下继续（假设火绒已打开）。")
        return None


@mcp.tool()
def quick_scan():
    """
        执行火绒安全软件的快速查杀功能。
    Args：
        None
    """
    # 步骤1：打开火绒安全软件（不足：必须在火绒的首页）
    start_huorong(HUORONG_PATH)
    debug_print(f"火绒安全软件已启动，请确保火绒处于首页，否则后续可能执行失败。")
    time.sleep(get_sleep_time("short"))  # 等待应用程序加载

    # 步骤2：点击"快速查杀"按钮（使用相对位置定位）
    quick_scan_pos = get_config_value(
        "positions.huorong.quick_scan_button", default=[0.55, 0.5]
    )
    debug_print(quick_scan_pos)
    img_loc = find_image_on_screen(
        x_ratio=quick_scan_pos[0],
        y_ratio=quick_scan_pos[1],
        timeout_seconds=15,
        description="快速查杀按钮",
    )
    if img_loc:
        click_image_at_location(img_loc, description="快速查杀按钮")
        debug_print("点击快速查杀按钮成功。")
    else:
        debug_print("点击快速查杀按钮失败。")
        return "点击快速查杀按钮失败。"
    time.sleep(get_sleep_time("short"))

    # 步骤3：检测是否正在查杀（使用OCR识别"暂停"字符串）
    # 创建 mcp_servers/artifacts/huorong 目录
    log_dir = Path(__file__).parent / "artifacts" / "huorong"
    log_dir.mkdir(parents=True, exist_ok=True)

    # 截取右上部分（从50%宽度到100%，从0%高度到50%）
    screenshot_path = log_dir / f"scan_check.png"
    region_img = capture_window_region(
        x_start_ratio=0.8,
        y_start_ratio=0.0,
        x_end_ratio=1.0,
        y_end_ratio=0.2,
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
                f"检测到'暂停'字符，说明正在执行快速查杀。截图已保存到: {screenshot_path}"
            )
        else:
            debug_print(
                f"未找到'暂停'字符，说明未成功执行快速查杀。截图已保存到: {screenshot_path}"
            )
            return (
                f"未找到'暂停'字符，说明未成功执行快速查杀。截图路径: {screenshot_path}"
            )
    except Exception as e:
        import traceback

        error_msg = f"OCR识别过程中出错: {e}\n{traceback.format_exc()}"
        debug_print(error_msg)
        return error_msg

    # 步骤4：检测查杀是否完成（每60秒截取右上角，使用OCR识别"完成"字符串）
    start_time = time.time()
    interval = 3600  # 60分钟
    check_interval = 15  # 每15秒检测一次
    last_check_time = 0
    recognizer = ImageRecognition()

    debug_print("开始监控查杀进度，每15秒检测一次...")
    while time.time() - start_time < interval:
        current_time = time.time()

        # 每15秒检测一次
        if current_time - last_check_time >= check_interval:
            last_check_time = current_time
            elapsed_time = current_time - start_time

            # 截取右上部分
            screenshot_path = (
                log_dir / f"scan_progress.png"
            )
            region_img = capture_window_region(
                x_start_ratio=0.8,
                y_start_ratio=0.0,
                x_end_ratio=1.0,
                y_end_ratio=0.2,
                save_path=str(screenshot_path),
            )

            if region_img is None:
                debug_print("截取窗口右上部分失败。")
                continue

            # 使用OCR识别是否包含"完成"或"立即处理"字符串
            if recognizer.contains_text(
                str(screenshot_path), "完成", case_sensitive=False
            ):
                debug_print(f"检测到'完成'字符，说明查杀已完成。耗时: {int(elapsed_time)}秒")
                ret2_top_page()
                return f"快速查杀完成。耗时: {int(elapsed_time)}秒，截图保存在: {screenshot_path}"

            elif recognizer.contains_text(
                str(screenshot_path), "立即处理", case_sensitive=False
            ):
                debug_print(f"检测到'立即处理'字符。耗时: {int(elapsed_time)}秒，正在处理...")
                # 点击"立即处理"按钮（同样位置）
                complete_button_pos = get_config_value(
                    "positions.huorong.complete_button", default=[0.92, 0.12]
                )
                handle_loc = find_image_on_screen(
                    x_ratio=complete_button_pos[0],
                    y_ratio=complete_button_pos[1],
                    timeout_seconds=5,
                    description="立即处理按钮",
                )
                if handle_loc:
                    click_image_at_location(handle_loc, description="立即处理按钮")
                    debug_print("点击'立即处理'按钮成功。")
                    time.sleep(get_sleep_time("short"))

                ret2_top_page()
                return f"快速查杀完成（已处理风险项）。耗时: {int(elapsed_time)}秒，截图保存在: {screenshot_path}"

            debug_print(f"[{int(elapsed_time)}s] 继续等待查杀完成...")

        time.sleep(1)

    # 超时返回
    debug_print("查杀监控超时（60分钟）")
    return f"查杀监控超时，最后的截图保存在: {log_dir}"


@mcp.tool()
def full_scan():
    """
        执行火绒安全软件的全盘查杀功能。
    Args：
        None
    """
    # 步骤1：打开火绒安全软件（不足：必须在火绒的首页）
    start_huorong(HUORONG_PATH)
    debug_print(f"火绒安全软件已启动，请确保火绒处于首页，否则后续可能执行失败。")
    time.sleep(get_sleep_time("short"))  # 等待应用程序加载

    # 步骤2：点击"全盘查杀"按钮（使用相对位置定位）
    full_scan_pos = get_config_value(
        "positions.huorong.full_scan_button", default=[0.33, 0.5]
    )
    debug_print(full_scan_pos)
    full_scan_loc = find_image_on_screen(
        x_ratio=full_scan_pos[0],
        y_ratio=full_scan_pos[1],
        timeout_seconds=15,
        description="全盘查杀按钮",
    )
    if full_scan_loc:
        click_image_at_location(full_scan_loc, description="全盘查杀按钮")
        debug_print("点击全盘查杀按钮成功。")
    else:
        debug_print("点击全盘查杀按钮失败。")
        return "点击全盘查杀按钮失败。"
    time.sleep(get_sleep_time("short"))

    # 步骤3：检测是否正在查杀（使用OCR识别"暂停"字符串）
    # 创建 mcp_servers/artifacts/huorong 目录
    log_dir = Path(__file__).parent / "artifacts" / "huorong"
    log_dir.mkdir(parents=True, exist_ok=True)

    # 截取右上部分（从50%宽度到100%，从0%高度到50%）
    screenshot_path = (
        log_dir / f"full_scan_check.png"
    )
    region_img = capture_window_region(
        x_start_ratio=0.8,
        y_start_ratio=0.0,
        x_end_ratio=1.0,
        y_end_ratio=0.2,
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
                f"检测到'暂停'字符，说明正在执行全盘查杀。截图已保存到: {screenshot_path}"
            )
        else:
            debug_print(
                f"未找到'暂停'字符，说明未成功执行全盘查杀。截图已保存到: {screenshot_path}"
            )
            return (
                f"未找到'暂停'字符，说明未成功执行全盘查杀。截图路径: {screenshot_path}"
            )
    except Exception as e:
        import traceback

        error_msg = f"OCR识别过程中出错: {e}\n{traceback.format_exc()}"
        debug_print(error_msg)
        return error_msg

    # 步骤4：检测查杀是否完成（每15秒截取右上角，使用OCR识别"完成"字符串）
    start_time = time.time()
    interval = 3600  # 60分钟（全盘查杀耗时较长）
    check_interval = 15  # 每15秒检测一次
    last_check_time = 0
    recognizer = ImageRecognition()

    debug_print("开始监控全盘查杀进度，每15秒检测一次...")
    while time.time() - start_time < interval:
        current_time = time.time()

        # 每15秒检测一次
        if current_time - last_check_time >= check_interval:
            last_check_time = current_time
            elapsed_time = current_time - start_time

            # 截取右上部分
            screenshot_path = (
                log_dir / f"full_scan_progress.png"
            )
            region_img = capture_window_region(
                x_start_ratio=0.8,
                y_start_ratio=0.0,
                x_end_ratio=1.0,
                y_end_ratio=0.2,
                save_path=str(screenshot_path),
            )

            if region_img is None:
                debug_print("截取窗口右上部分失败。")
                continue

            # 使用OCR识别是否包含"完成"或"立即处理"字符串
            if recognizer.contains_text(
                str(screenshot_path), "完成", case_sensitive=False
            ):
                debug_print(
                    f"检测到'完成'字符，说明全盘查杀已完成。耗时: {int(elapsed_time)}秒"
                )
                ret2_top_page()
                return f"全盘查杀完成。耗时: {int(elapsed_time)}秒，截图保存在: {screenshot_path}"

            elif recognizer.contains_text(
                str(screenshot_path), "立即处理", case_sensitive=False
            ):
                debug_print(f"检测到'立即处理'字符。耗时: {int(elapsed_time)}秒，正在处理...")
                # 点击"立即处理"按钮（同样位置）
                complete_button_pos = get_config_value(
                    "positions.huorong.complete_button", default=[0.92, 0.12]
                )
                handle_loc = find_image_on_screen(
                    x_ratio=complete_button_pos[0],
                    y_ratio=complete_button_pos[1],
                    timeout_seconds=5,
                    description="立即处理按钮",
                )
                if handle_loc:
                    click_image_at_location(handle_loc, description="立即处理按钮")
                    debug_print("点击'立即处理'按钮成功。")
                    time.sleep(get_sleep_time("short"))

                ret2_top_page()
                return f"全盘查杀完成（已处理风险项）。耗时: {int(elapsed_time)}秒，截图保存在: {screenshot_path}"

            debug_print(f"[{int(elapsed_time)}s] 继续等待全盘查杀完成...")

        time.sleep(1)

    # 超时返回
    debug_print("全盘查杀监控超时（60分钟）")
    return f"全盘查杀监控超时，最后的截图保存在: {log_dir}"


@mcp.tool()
def get_quarantine_file():
    """
        执行火绒的查看隔离区功能，获取当前隔离区内的文件列表，有可能为空，注意导出后还要进行读取分析工作。
    Args:
        None
    """
    # 读取数据库中信息
    source_db_path = r"C:/ProgramData/Huorong/ESEndpoint/log.db"
    target_dir = r"./src/mcpsectrace/mcp_servers/artifacts/huorong/"  # 目标目录
    target_db_path = os.path.join(target_dir, "QuarantineEx.db")
    log_path = "./src/mcpsectrace/mcp_servers/artifacts/huorong/quarantine_files.log"
    try:
        # 1. 复制数据库到目标目录下
        if not os.path.exists(source_db_path):
            debug_print(f"[ERR]隔离区数据库文件不存在: {source_db_path}")
            return f"[ERR]隔离区数据库文件不存在: {source_db_path}"
        shutil.copy(source_db_path, target_dir)
        debug_print(f"已复制到目标目录下: {source_db_path}")

        # 2. 读取数据库内容到log中
        read_QuarantineEx_db(target_db_path, log_path)
        debug_print(f"已读取隔离区内容到: {target_db_path}")

    except Exception as e:
        debug_print(f"[ERR]执行失败，错误信息: {e}")
        return f"[ERR]执行失败，错误信息: {e}"

    finally:
        # 3. 删除临时数据库文件
        if os.path.exists(target_db_path):
            try:
                os.remove(target_db_path)
                debug_print(f"已删除临时数据库文件: {target_db_path}")
            except Exception as e:
                debug_print(f"[ERR]删除临时数据库文件失败: {e}")

    return f"已获取当前隔离区内的文件列表，见 {log_path}。"


@mcp.tool()
def get_trust_zone():
    """
        执行火绒的查看信任区功能，获取当前信任区内的文件列表，有可能为空，注意导出后还要进行读取分析工作。
    Args:
        None
    """
    # 1：复制相关文件到当前目录下（存在才复制）
    target_dir = r"./src/mcpsectrace/mcp_servers/artifacts/huorong/"
    files = [
        r"C:/ProgramData/Huorong/ESEndpoint/wlfile.db",
        r"C:/ProgramData/Huorong/ESEndpoint/wlfile.db-wal",
    ]
    for f in files:
        try:
            shutil.copy(f, target_dir)
            debug_print(f"已复制文件: {f}")
        except Exception as e:
            debug_print(f"文件复制失败: {f}, 错误: {e}")
            return f"复制文件失败: {f}, 错误: {e}"
    # 2：读取表内容
    file_path = "./src/mcpsectrace/mcp_servers/artifacts/huorong/trust_files.log"
    read_wlfile_db(target_dir + "wlfile.db", file_path)
    # 3：删除复制的文件
    for f in ["wlfile.db", "wlfile.db-wal"]:
        f_path = os.path.join(target_dir, f)
        if os.path.exists(f_path):
            os.remove(f_path)
            debug_print(f"已删除临时文件: {f}")
        else:
            debug_print(f"未找到临时文件（跳过删除）: {f}")
    return f"已获取当前信任区内的文件列表，见{file_path}。"


@mcp.tool()
def get_security_log():
    """
    执行火绒的获取今日安全日志功能，具体为导出今日的安全日志为txt文件。
    """
    # 0.打开火绒
    start_huorong(HUORONG_PATH)
    time.sleep(get_sleep_time("short"))
    debug_print("请确保火绒安全的首页是当前活动窗口，或者至少是可见的。")

    # 1.点击首页的安全日志图标（分为两步）
    # 1.1 先点击展开菜单按钮
    menu_button_pos = get_config_value(
        "positions.huorong.menu_button", default=[0.876, 0.05]
    )
    if not find_and_click(
        x_ratio=menu_button_pos[0],
        y_ratio=menu_button_pos[1],
        timeout_seconds=15,
        description="展开菜单按钮",
    ):
        return "未能找到展开菜单按钮。"
    time.sleep(get_sleep_time("short"))
    debug_print("展开菜单已打开。")

    # 1.2 再点击安全日志按钮
    security_log_pos = get_config_value(
        "positions.huorong.security_log_icon", default=[0.178, 0.5]
    )
    if not find_and_click(
        x_ratio=security_log_pos[0],
        y_ratio=security_log_pos[1],
        timeout_seconds=20,
        description="安全日志按钮",
    ):
        return "未能找到安全日志按钮。"
    time.sleep(get_sleep_time("short"))
    debug_print("安全日志界面已打开。")

    # 2.若不为空，则点击导出日志按钮（使用相对位置定位）
    debug_print("尝试点击导出日志按钮...")
    export_log_pos = get_config_value(
        "positions.huorong.export_log_button", default=[0.935, 0.954]
    )
    if not find_and_click(
        x_ratio=export_log_pos[0],
        y_ratio=export_log_pos[1],
        timeout_seconds=15,
        description="导出日志按钮",
    ):
        return "未能找到导出日志按钮，或点击失败。"
    time.sleep(get_sleep_time("medium"))

    # 3.检查是否点击成功（检查另存为对话框）
    debug_print("检查是否出现'另存为'对话框...")
    recognizer = ImageRecognition()

    # 截取左上角部分，检测"另存为"文本
    save_as_detected = False
    logs_dir = Path(__file__).parent / "artifacts" / "huorong"
    logs_dir.mkdir(parents=True, exist_ok=True)

    for attempt in range(15):  # 15次重试，每次等待1秒
        try:
            # 保存截图，带上时间戳
            timestamp = datetime.now().strftime("%Y%m%d")
            temp_screenshot_path = logs_dir / f"save_as_check_{timestamp}.png"

            # 截取窗口的左上角部分（0%-40%宽度，0%-20%高度）
            region_img = capture_window_region(
                x_start_ratio=0.0,
                y_start_ratio=0.0,
                x_end_ratio=0.4,
                y_end_ratio=0.2,
                save_path=str(temp_screenshot_path)
            )

            if region_img is None:
                debug_print(f"截图失败，重试中... ({attempt + 1}/15)")
                time.sleep(1)
                continue

            # 使用OCR检测"另存为"
            if recognizer.contains_text(
                str(temp_screenshot_path), "另存为", case_sensitive=False
            ):
                debug_print("检测到'另存为'对话框，点击成功。")
                save_as_detected = True
                break

            debug_print(f"未检测到'另存为'，重试中... ({attempt + 1}/15)")
            time.sleep(1)

        except Exception as e:
            debug_print(f"检查'另存为'对话框时出错: {e}")
            time.sleep(1)

    if not save_as_detected:
        debug_print("超时：未能检测到'另存为'对话框。")
        return "未能检测到'另存为'对话框，说明点击'导出日志'按钮失败。"

    # 3.5 确定文件输出位置
    debug_print("设置文件输出位置...")

    # 点击浏览按钮
    browse_button_pos = get_config_value(
        "positions.huorong.browse_button", default=[0.77, 0.15]
    )
    if not find_and_click(
        x_ratio=browse_button_pos[0],
        y_ratio=browse_button_pos[1],
        timeout_seconds=15,
        description="浏览按钮",
    ):
        return "未能找到浏览按钮。"
    time.sleep(get_sleep_time("medium"))

    # 输入路径（使用剪贴板粘贴）
    log_path = r"D:\MCPSecTrace\logs\huorong"
    debug_print(f"输入日志输出路径: {log_path}")

    # 复制路径到剪贴板
    pyperclip.copy(log_path)
    time.sleep(0.2)

    # 使用 Ctrl+V 粘贴
    pyautogui.hotkey("ctrl", "v")
    debug_print("已粘贴路径")
    time.sleep(get_sleep_time("short"))

    # 按回车键确定
    pyautogui.press("enter")
    debug_print("已按回车键确定")
    time.sleep(get_sleep_time("medium"))

    # 4.点击文件名输入框
    debug_print("尝试点击文件名输入框...")
    filename_input_pos = get_config_value(
        "positions.windows_dialogs.save_as.filename_input", default=[0.28, 0.9]
    )
    if not find_and_click(
        x_ratio=filename_input_pos[0],
        y_ratio=filename_input_pos[1],
        timeout_seconds=15,
        description="文件名输入框",
    ):
        debug_print("未能找到文件名输入框。")
        return "未能找到文件名输入框。"
    time.sleep(get_sleep_time("medium"))  # 给输入框获取焦点的时间

    # 5.输入文件名（使用剪贴板粘贴）
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"huorong_securitylog_{timestamp}"
    debug_print(f"准备输入文件名: {filename}")

    # 复制文件名到剪贴板
    pyperclip.copy(filename)
    time.sleep(0.2)

    # 使用 Ctrl+V 粘贴
    pyautogui.hotkey("ctrl", "v")
    debug_print("已粘贴文件名")
    time.sleep(get_sleep_time("long"))

    # 6.点击"保存"按钮
    debug_print("尝试点击'保存'按钮...")
    save_button_pos = get_config_value(
        "positions.windows_dialogs.save_as.save_button", default=[0.8, 0.9]
    )
    if not find_and_click(
        x_ratio=save_button_pos[0],
        y_ratio=save_button_pos[1],
        timeout_seconds=15,
        description="保存按钮",
    ):
        return "未能找到保存按钮。"
    debug_print(f"安全日志导出流程执行完毕，请查看文件{log_path} + {filename}.txt。")
    time.sleep(get_sleep_time("medium"))  # 等待保存操作完成

    # 6.5 点击返回按钮
    debug_print("点击返回按钮...")
    back_button_pos = get_config_value(
        "positions.huorong.back_button", default=[0.855, 0.88]
    )
    if not find_and_click(
        x_ratio=back_button_pos[0],
        y_ratio=back_button_pos[1],
        timeout_seconds=15,
        description="返回按钮",
    ):
        debug_print("未能找到返回按钮，继续执行...")
    time.sleep(get_sleep_time("medium"))

    # 7.检查是否导出成功（返回到火绒主界面）
    return f"日志导出成功，请查看文件{log_path} + {filename}.txt。"


# --- 主函数 ---
def main():
    """
    根据是否处于调试模式，执行不同的操作。
    """
    # 1. 初始化日志
    global LOG_NAME
    LOG_NAME = setup_log()

    # 2. 从配置文件读取火绒路径
    global HUORONG_PATH
    HUORONG_PATH = get_config_value("paths.huorong_exe", default="")

    # 验证火绒路径
    if not HUORONG_PATH:
        error_msg = "错误：未配置火绒路径。请在 config/user_settings.toml 中设置 paths.huorong_exe"
        print(error_msg, file=sys.stderr)
        debug_print(error_msg)
    elif not os.path.exists(HUORONG_PATH):
        warning_msg = f"警告：火绒路径不存在: {HUORONG_PATH}"
        print(warning_msg, file=sys.stderr)
        debug_print(warning_msg)
    else:
        debug_print(f"已从配置文件加载火绒路径: {HUORONG_PATH}")

    print("--- 火绒MCP服务器启动 ---", file=sys.stderr)
    debug_print(f"调试模式: {get_config_value('debug_mode', default=False)}")
    debug_print(f"设备性能等级: {get_config_value('device_level', default=2)}")
    # start_huorong(HUORONG_PATH)
    # quick_scan()
    # full_scan()
    # get_quarantine_file()
    # get_trust_zone()
    # get_security_log()
    mcp.run(transport="stdio")


# --- 主程序入口 ---
if __name__ == "__main__":
    main()
