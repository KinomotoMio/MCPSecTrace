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
from typing import Optional

import pyautogui
import win32gui
from PIL import Image

# --- 输出使用utf-8编码（仅在非测试环境） --
if "pytest" not in sys.modules:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")
from mcpsectrace.config import get_config_value

# --- 导入MCP ---
try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    debug_print('[致命错误] 请先运行: uv add "mcp[cli]" httpx')
    sys.exit(1)

mcp = FastMCP("huorong", log_level="ERROR", port=8888)

# --- 全局变量 ---
HUORONG_PATH = ""  # 将在main()中从配置文件加载


def debug_print(message: str):
    """仅在调试模式下输出调试信息到标准错误流"""
    debug_mode = get_config_value("debug_mode", default=False)
    if debug_mode:
        print(message, file=sys.stderr)


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


def find_image_on_screen(
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
            debug_print(f"  窗口信息: 位置({win_left}, {win_top}), 大小 {win_width}x{win_height}")
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
        pyautogui.click(location)
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


def ret2_top_page():
    """
    执行完功能后，返回首页。
    """
    # 从配置文件读取完成按钮的相对位置
    complete_button_pos = get_config_value("positions.huorong.complete_button_alt", default=[0.5, 0.75])
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
        return app.pid
    except Exception as e:
        debug_print(f"启动应用程序 '{path}' 时发生错误: {e}")
        debug_print("脚本将尝试在不启动新进程的情况下继续（假设火绒已打开）。")
        return None


@mcp.tool()
def scan_virus():
    """
        执行火绒安全软件的快速查杀功能。
    Args：
        None
    """
    # 步骤1：打开火绒安全软件（不足：必须在火绒的首页）
    start_huorong(HUORONG_PATH)
    debug_print(f"火绒安全软件已启动，请确保火绒处于首页，否则后续可能执行失败。")
    time.sleep(get_sleep_time("long"))  # 等待应用程序加载

    # 步骤2：点击"快速查杀"按钮（使用相对位置定位）
    quick_scan_pos = get_config_value("positions.huorong.quick_scan_button", default=[0.4, 0.3])
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
    time.sleep(get_sleep_time("long"))

    # 步骤3：检测是否正在查杀（检查暂停按钮位置）
    pause_button_pos = get_config_value("positions.huorong.pause_button", default=[0.5, 0.5])
    if find_image_on_screen(
        x_ratio=pause_button_pos[0],
        y_ratio=pause_button_pos[1],
        timeout_seconds=15,
        description="暂停按钮",
    ):
        debug_print("正在执行快速查杀。")
    else:
        debug_print("未找到暂停按钮，说明未成功执行快速查杀。")
        return "未找到暂停按钮，说明未成功执行快速查杀。"

    # 步骤4：检测查杀是否完成
    complete_button_pos = get_config_value("positions.huorong.complete_button", default=[0.5, 0.7])
    start_time = time.time()
    interval = 300  # 5分钟
    while time.time() - start_time < interval:
        img_loc = find_image_on_screen(
            x_ratio=complete_button_pos[0],
            y_ratio=complete_button_pos[1],
            timeout_seconds=15,
            description="快速查杀完成",
        )
        if img_loc:
            debug_print(f"检测到查杀完成标志，坐标为: {img_loc}")
            ret2_top_page()
            return "快速查杀完成。"
        time.sleep(get_sleep_time("medium"))
    # 步骤5：返回查杀结果
    # 待补充（OCR识别查杀结果界面、联动日志查询）
    # 步骤6：点击完成，返回首页


@mcp.tool()
def get_quarantine_file():
    """
        执行火绒的查看隔离区功能，获取当前隔离区内的文件列表，有可能为空，注意导出后还要进行读取分析工作。
    Args:
        None
    """
    # 方法1：图像识别
    # 1：打开火绒安全软件
    # start_huorong(HUORONG_PATH)
    # time.sleep(get_sleep_time("long"))
    # 2：打开隔离区
    # find_and_click(QUARANTINE_BUTTON_IMAGE,"隔离区按钮")
    # time.sleep(get_sleep_time("short"))
    # find_and_click(MAXIMIZE_BUTTON_IMAGE,"最大化窗口按钮")
    # time.sleep(get_sleep_time("short"))
    # 3：获取文件列表

    # 方法2：读取数据库中信息
    source_db_path = r"C:/ProgramData/Huorong/Sysdiag/QuarantineEx.db"
    target_dir = r"./"  # 目标目录
    target_db_path = os.path.join(target_dir, "QuarantineEx.db")
    log_path = "quarantine_files.log"
    try:
        # 1. 复制数据库到目标目录下
        if not os.path.exists(source_db_path):
            debug_print(f"[ERR]隔离区数据库文件不存在: {source_db_path}")
            return f"[ERR]隔离区数据库文件不存在: {source_db_path}"
        shutil.copy(source_db_path, target_dir)
        debug_print(f"已复制到目标目录下: {source_db_path}")

        # 2. 读取数据库内容到log中
        read_QuarantineEx_db(target_db_path, log_path)
        debug_print(f"已读取隔离区内容到: {log_path}")

    except Exception as e:
        return f"[ERR]执行失败，错误信息: {e}"

    finally:
        # 3. 删除临时数据库文件（存在才删）
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
    # 不足：缺乏错误处理,db中的其他表也可以读取
    # 1：复制相关文件到当前目录下（存在才复制）
    target_dir = r"./"
    files = [
        r"C:/ProgramData/Huorong/Sysdiag/wlfile.db",
        r"C:/ProgramData/Huorong/Sysdiag/wlfile.db-wal",
    ]
    for f in files:
        try:
            shutil.copy(f, target_dir)
            debug_print(f"已复制文件: {f}")
        except Exception as e:
            debug_print(f"文件复制失败: {f}, 错误: {e}")
            return f"复制文件失败: {f}, 错误: {e}"
    # 2：读取表内容
    file_path = "trust_files.log"
    read_wlfile_db("./wlfile.db", file_path)
    # 3：删除复制的文件（存在才删）
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
    执行火绒的获取今日安全日志功能，具体为导出今日的安全日志为txt文件，注意导出后还要进行读取分析工作。
    """
    # 0.打开火绒
    start_huorong(HUORONG_PATH)
    time.sleep(get_sleep_time("long"))
    debug_print("请确保火绒安全的首页是当前活动窗口，或者至少是可见的。")

    # 1.点击首页的安全日志图标（使用相对位置定位）
    security_log_pos = get_config_value("positions.huorong.security_log_icon", default=[0.8, 0.15])
    if not find_and_click(
        x_ratio=security_log_pos[0],
        y_ratio=security_log_pos[1],
        timeout_seconds=20,
        description="安全日志",
    ):
        return "未能找到安全日志图标。"
    time.sleep(get_sleep_time("medium"))
    debug_print("安全日志界面已打开。")

    # 2.检查今日安全日志是否为空
    # (留作备用，可根据需要启用)

    # 3.若不为空，则点击导出日志按钮（使用相对位置定位）
    debug_print("尝试点击导出日志按钮...")
    export_log_pos = get_config_value("positions.huorong.export_log_button", default=[0.9, 0.1])
    if not find_and_click(
        x_ratio=export_log_pos[0],
        y_ratio=export_log_pos[1],
        timeout_seconds=15,
        description="导出日志按钮",
    ):
        return "未能找到导出日志按钮，或点击失败。"
    time.sleep(get_sleep_time("medium"))

    # 检查是否点击成功（检查另存为对话框）
    # 注意：这里使用屏幕坐标而不是窗口坐标
    save_dialog_mark = get_config_value("positions.windows_dialogs.save_as.filename_input", default=[0.5, 0.5])
    if not find_image_on_screen(
        x_ratio=save_dialog_mark[0],
        y_ratio=save_dialog_mark[1],
        timeout_seconds=15,
        description="另存为标记",
    ):
        debug_print("未能找到'另存为'标记。")
        return "未能找到'另存为'标记，说明点击'导出日志'按钮失败。"

    # 4.点击文件名输入框
    debug_print("尝试点击文件名输入框...")
    filename_input_pos = get_config_value("positions.windows_dialogs.save_as.filename_input", default=[0.5, 0.5])
    if not find_and_click(
        x_ratio=filename_input_pos[0],
        y_ratio=filename_input_pos[1],
        timeout_seconds=15,
        description="文件名输入框",
    ):
        debug_print("未能找到文件名输入框。")
        return "未能找到文件名输入框。"
    time.sleep(get_sleep_time("medium"))  # 给输入框获取焦点的时间

    # 5.输入文件名
    current_time_str = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    debug_print(f"准备输入文件名: {current_time_str}")
    pyautogui.typewrite(current_time_str, interval=0.05)  # interval 控制打字速度
    time.sleep(get_sleep_time("long"))  # 打字时间
    pyautogui.press("enter")  # 模拟按一次回车（考虑到中文输入法）

    # 6.点击"保存"按钮
    debug_print("尝试点击'保存'按钮...")
    save_button_pos = get_config_value("positions.windows_dialogs.save_as.save_button", default=[0.7, 0.9])
    if not find_and_click(
        x_ratio=save_button_pos[0],
        y_ratio=save_button_pos[1],
        timeout_seconds=15,
        description="保存按钮",
    ):
        return "未能找到保存按钮。"
    debug_print(
        f"安全日志导出流程执行完毕，请查看文件D:/Desktop/{current_time_str}.txt。"
    )
    time.sleep(get_sleep_time("medium"))  # 等待保存操作完成

    # 7.检查是否导出成功（返回到火绒主界面）
    return f"日志导出成功，请查看文件{current_time_str}.txt，默认在Desktop目录下。"
    # 不足：其他人的日志存储路径不一定在 D:/Desktop/。


# --- 主函数 ---
def main():
    """
    根据是否处于调试模式，执行不同的操作。
    """
    # 从配置文件读取火绒路径
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
    scan_virus()
    # mcp.run(transport="stdio")


# --- 主程序入口 ---
if __name__ == "__main__":
    main()
