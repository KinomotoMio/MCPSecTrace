import argparse
import ctypes
import io
import os
import subprocess
import sys
import time
from datetime import datetime

import pyautogui

# --- 输出使用utf-8编码（仅在非测试环境） --
if "pytest" not in sys.modules:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")
from mcpsectrace.config import get_config_value

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
def setup_log(log_dir="logs"):
    # 如果不存在，则创建logs目录
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    debug_print(f"日志目录: {log_dir}")

    # 生成日志文件名（包含时间戳）
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = os.path.join(log_dir, f"hrkill_mcp_{timestamp}.log")
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

    # 2. 点击'开始扫描按钮'
    debug_print(f"[Step 2] 点击'开始扫描按钮'")
    if not find_and_click(
        "start_scan_button.png",  # HRKill界面固定元素
        confidence_level=0.8,
        timeout_seconds=15,
        description="开始扫描按钮",
    ):
        return "[ERROR] 未能找到'开始扫描按钮'，或点击按钮失败，请查看最新日志溯源。"
    time.sleep(get_sleep_time("long"))

    # 3. 检测是否正在查杀病毒
    debug_print(f"[Step 3] 检测是否正在查杀病毒")
    if find_image_on_screen(
        "pause_button.png",  # HRKill界面固定元素
        confidence_level=0.8,
        timeout_seconds=15,
        description="查杀暂停按钮",
    ):
        debug_print("正在执行病毒查杀。")
    else:
        debug_print("[ERROR] 未成功执行病毒查杀，请查看最新日志溯源。")
        return "[ERROR] 未成功执行病毒查杀，请查看最新日志溯源。"
    time.sleep(get_sleep_time("long"))

    # 4. 检测是否扫描完成
    interval = 300  # 5分钟
    debug_print(f"[Step 4] 检测是否扫描完成（时长{interval}s，可调节）")
    start_time = time.time()
    img_loc = find_image_on_screen(
        "scan_complete.png",  # HRKill界面固定元素
        confidence_level=0.8,
        timeout_seconds=interval,
        description="扫描完成",
    )
    if img_loc:
        msg = f"[SUCCESS] 检测到完成标志(坐标为{img_loc}, 用时{time.time() - start_time}秒)，病毒查杀已完成。"
        debug_print(msg)
        return msg


# --- 主函数 ---
def main():
    """
    主函数，用于初始化参数并启动MCP服务器。
    """
    # 参数设置
    global HRKILL_PATH, LOG_NAME
    parser = argparse.ArgumentParser(description="hrkill MCP工具")
    parser.add_argument(
        "--hrkill-path", type=str, required=True, help="hrkill软件的完整路径"
    )
    parser.add_argument("--debug", action="store_true", help="调试模式")
    args = parser.parse_args()
    HRKILL_PATH = args.hrkill_path
    # DEBUG_MODE现在通过配置系统管理
    LOG_NAME = setup_log("logs/hrkill")

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
        mcp.run(transport="stdio")


# --- 主程序入口 ---
if __name__ == "__main__":
    try:
        main()
    finally:
        close_log_file()
