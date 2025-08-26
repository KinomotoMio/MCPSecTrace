import argparse
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
from PIL import Image

# --- 输出使用utf-8编码 --
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

# --- 导入MCP ---
try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    debug_print('[致命错误] 请先运行: uv add "mcp[cli]" httpx')
    sys.exit(1)

mcp = FastMCP("huorong", log_level="ERROR", port=8888)

# --- 设备性能与等待时间 ---
DEVICE_LEVEL = 1  # 1: 低性能设备，2: 中性能设备，3: 高性能设备
SLEEP_TIME_SHORT = 1 * DEVICE_LEVEL
SLEEP_TIME_MEDIUM = 3 * DEVICE_LEVEL
SLEEP_TIME_LONG = 5 * DEVICE_LEVEL

# 病毒查杀功能对应的图片
QUICK_SCAN_BUTTON_IMAGE = (
    "D:/FTAgent-master/tag_image/huorong/huorong_quick_scan_button_me.png"
)
PAUSE_BUTTON_IMAGE = "D:/FTAgent-master/tag_image/huorong/huorong_pause_button_me.png"
SCAN_COMPLETE_IMAGE = (
    "D:/FTAgent-master/tag_image/huorong/huorong_complete_button_me.png"
)

# 查看隔离区
QUARANTINE_BUTTON_IMAGE = (
    "D:/FTAgent-master/tag_image/huorong/huorong_quarantine_button_me.png"
)
MAXIMIZE_BUTTON_IMAGE = (
    "D:/FTAgent-master/tag_image/huorong/huorong_maximize_button_me.png"
)

# 获取安全日志
SECURITY_LOG_IMAGE = "D:/FTAgent-master/tag_image/huorong/huorong_security_log_me.png"
LOG_CHECK_IMAGE = "D:/FTAgent-master/tag_image/huorong/huorong_log_check.png"  ## ?
EXPORT_LOG_BUTTON_IMAGE = (
    "D:/FTAgent-master/tag_image/huorong/huorong_export_log_button_me.png"
)
FILENAME_INPUT_BOX_IMAGE = (
    "D:/FTAgent-master/tag_image/huorong/huorong_filename_input_box_me.png"
)
SAVE_BUTTON_IMAGE = "D:/FTAgent-master/tag_image/huorong/huorong_save_button_me.png"
SAVE_MARK_IMAGE = "D:/FTAgent-master/tag_image/huorong/huorong_save_mark_me.png"
EXPORT_COMPLETE_IMAGE = (
    "D:/FTAgent-master/tag_image/huorong/huorong_export_complete_me.png"
)


def debug_print(message: str):
    """仅在调试模式下输出调试信息到标准错误流"""
    if DEBUG_MODE:
        print(message, file=sys.stderr)


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
                debug_print(f"找到 '{description}'，坐标: {location}")
                return location
            else:
                time.sleep(SLEEP_TIME_SHORT)
        except pyautogui.ImageNotFoundException:
            time.sleep(SLEEP_TIME_SHORT)
        except FileNotFoundError:
            debug_print(f"严重错误：图像文件 '{image_filename}' 未找到或无法访问！")
            return None
        except Exception as e:
            if "Failed to read" in str(e) or "cannot identify image file" in str(e):
                debug_print(
                    f"错误: 无法读取或识别图像文件 '{image_filename}'。错误详情: {e}"
                )
                return None
            debug_print(f"查找图像 '{description}' 时发生其他错误: {e}")
            return None

    debug_print(f"超时：在 {timeout_seconds} 秒内未能找到图像 '{description}'。")
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


def find_and_click(image_filename, confidence_level, timeout_seconds, description):
    """
    查找屏幕上的图片并点击。若成功，则返回true，否则返回false。
    """
    img_loc = find_image_on_screen(
        image_filename=image_filename,
        confidence_level=0.6,
        timeout_seconds=15,
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
    global COMPLETE_BUTTON_IMAGE
    COMPLETE_BUTTON_IMAGE = (
        "D:/FTAgent-master/tag_image/huorong/huorong_complete_button_me.png"
    )
    img_loc = find_image_on_screen(
        COMPLETE_BUTTON_IMAGE,
        confidence_level=0.6,
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
    time.sleep(SLEEP_TIME_LONG)  # 等待应用程序加载
    # 步骤2：点击“快速查杀”按钮
    img_loc = find_image_on_screen(
        QUICK_SCAN_BUTTON_IMAGE,
        confidence_level=0.6,
        timeout_seconds=15,
        description="快速查杀按钮",
    )
    if img_loc:
        click_image_at_location(img_loc, description="快速查杀按钮")
        debug_print("点击快速查杀按钮成功。")
    else:
        debug_print("点击快速查杀按钮失败。")
        return "点击快速查杀按钮失败。"
    time.sleep(SLEEP_TIME_LONG)
    # 步骤3：检测是否正在查杀
    if find_image_on_screen(
        PAUSE_BUTTON_IMAGE,
        confidence_level=0.6,
        timeout_seconds=15,
        description="暂停按钮",
    ):
        debug_print("正在执行快速查杀。")
    else:
        debug_print("未找到暂停按钮，说明未成功执行快速查杀。")
        return "未找到暂停按钮，说明未成功执行快速查杀。"
    # 步骤4：检测查杀是否完成
    start_time = time.time()
    interval = 300  # 5分钟
    while time.time() - start_time < interval:
        img_loc = find_image_on_screen(
            SCAN_COMPLETE_IMAGE,
            confidence_level=0.6,
            timeout_seconds=15,
            description="快速查杀完成",
        )
        if img_loc:
            debug_print(f"检测到查杀完成标志，坐标为: {img_loc}")
            ret2_top_page()
            return "快速查杀完成。"
        time.sleep(SLEEP_TIME_MEDIUM)
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
    # time.sleep(SLEEP_TIME_LONG)
    # 2：打开隔离区
    # find_and_click(QUARANTINE_BUTTON_IMAGE,"隔离区按钮")
    # time.sleep(SLEEP_TIME_SHORT)
    # find_and_click(MAXIMIZE_BUTTON_IMAGE,"最大化窗口按钮")
    # time.sleep(SLEEP_TIME_SHORT)
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
    time.sleep(SLEEP_TIME_LONG)
    debug_print("请确保火绒安全的首页是当前活动窗口，或者至少是可见的。")

    # 1.点击首页的安全日志图标
    if not find_and_click(
        SECURITY_LOG_IMAGE,
        confidence_level=0.6,
        timeout_seconds=20,
        description="安全日志",
    ):
        return "未能找到安全日志图标。"
    time.sleep(SLEEP_TIME_MEDIUM)
    debug_print("安全日志界面已打开。")

    # 2.检查今日安全日志是否为空
    # if find_image_on_screen(LOG_CHECK_IMAGE, confidence_level=0.6, timeout_seconds=15, description="今日安全日志检查"):
    #     debug_print("由总项目数可知，今日没有安全日志，无法导出。")
    #     return "由总项目数可知，今日没有安全日志，无法导出。"

    # 3.若不为空，则点击导出日志按钮
    debug_print("尝试点击导出日志按钮...")
    if not find_and_click(
        EXPORT_LOG_BUTTON_IMAGE,
        confidence_level=0.9,
        timeout_seconds=15,
        description="导出日志按钮",
    ):
        return "未能找到导出日志按钮，或点击失败。"
    time.sleep(SLEEP_TIME_MEDIUM)
    # 检查是否点击成功
    if not find_image_on_screen(
        SAVE_MARK_IMAGE,
        confidence_level=0.6,
        timeout_seconds=15,
        description="另存为标记",
    ):
        debug_print("未能找到'另存为'标记。")
        return "未能找到'另存为'标记，说明点击'导出日志'按钮失败。"

    # 4.点击文件名输入框
    debug_print("尝试点击文件名输入框...")
    # 注意：文件名输入框的截图可能需要精确，或者可以考虑点击 "文件名：" 标签右侧固定偏移量（更复杂）
    if not find_and_click(
        FILENAME_INPUT_BOX_IMAGE,
        confidence_level=0.6,
        timeout_seconds=15,
        description="文件名输入框",
    ):
        debug_print("未能找到文件名输入框。")
        return "未能找到文件名输入框。"
    time.sleep(SLEEP_TIME_MEDIUM)  # 给输入框获取焦点的时间

    # 5.输入文件名
    current_time_str = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    debug_print(f"准备输入文件名: {current_time_str}")
    pyautogui.typewrite(current_time_str, interval=0.05)  # interval 控制打字速度
    time.sleep(SLEEP_TIME_LONG)  # 打字时间
    pyautogui.press("enter")  # 模拟按一次回车（考虑到中文输入法）

    # 6.点击"保存"按钮
    debug_print("尝试点击'保存'按钮...")
    if not find_and_click(
        SAVE_BUTTON_IMAGE,
        confidence_level=0.6,
        timeout_seconds=15,
        description="保存按钮",
    ):
        return "未能找到保存按钮。"
    debug_print(
        f"安全日志导出流程执行完毕，请查看文件D:/Desktop/{current_time_str}.txt。"
    )
    time.sleep(SLEEP_TIME_MEDIUM)  # 等待保存操作完成

    # 7.检查是否导出成功
    if not find_image_on_screen(
        EXPORT_COMPLETE_IMAGE,
        confidence_level=0.6,
        timeout_seconds=15,
        description="导出完成标志",
    ):
        debug_print("导出日志失败，未找到导出完成标志。")
        return "导出日志失败，未找到导出完成标志。"
    return f"日志导出成功，请查看文件{current_time_str}.txt，默认在Desktop目录下。"
    # 不足：其他人的日志存储路径不一定在 D:/Desktop/。


# --- 主函数 ---
def main():
    """
    根据是否处于调试模式，执行不同的操作。
    """
    # 获取参数
    global HUORONG_PATH, DEBUG_MODE, QUARANTINE_DB_PATH, LOG_NAME
    parser = argparse.ArgumentParser(description="火绒MCP工具")
    parser.add_argument(
        "--huorong-path", type=str, required=True, help="火绒安全软件的完整路径"
    )
    parser.add_argument("--debug", action="store_true", help="调试模式")
    args = parser.parse_args()
    HUORONG_PATH = args.huorong_path
    DEBUG_MODE = args.debug
    # LOG_NAME = setup_log("./logs/huorong","huorong")

    # init_global_variables(DEBUG_MODE, LOG_NAME)

    # 1. 检查VS code权限
    # debug_print("--- VS code 管理员权限检查 ---")
    # if not is_admin():
    #     msg = "未检测到管理员权限，为了使用huorong MCP，请以管理员身份打开VS Code。"
    #     debug_print(msg)
    #     print(msg, file=sys.stderr)
    #     return msg
    # else:
    #     debug_print("当前已具备管理员权限。")

    # 2. 运行
    if DEBUG_MODE:
        print("--- 当前处于调试模式 ---")
        scan_virus()
        # get_trust_zone()
        # get_quarantine_file()
        # get_security_log()
    else:
        print("--- 当前处于正式运行模式 ---")
        mcp.run(transport="stdio")


# --- 主程序入口 ---
if __name__ == "__main__":
    try:
        main()
    finally:
        close_log_file()
