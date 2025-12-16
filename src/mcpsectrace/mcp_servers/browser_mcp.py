import asyncio
import datetime
import json
import os
import platform
import shutil
import sqlite3
import sys
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional

from mcpsectrace.config import get_config_value

# --- 调试开关 ---
DEBUG_MODE = "--debug" in sys.argv


def debug_print(message: str):
    """仅在调试模式下输出调试信息到标准错误流"""
    if DEBUG_MODE:
        print(message, file=sys.stderr)


try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    debug_print('[致命错误] 请先运行: uv add "mcp[cli]" httpx')
    sys.exit(1)

mcp = FastMCP("browser_tools", log_level="ERROR")


def _get_user_profile_path_sync() -> Optional[Path]:
    """获取当前用户的主目录路径（仅支持 Windows）"""
    if platform.system() == "Windows":
        return Path(os.environ["USERPROFILE"])
    return Path.home()


def _convert_chrome_time_sync(chrome_time: int) -> Optional[str]:
    """将 Chrome 时间戳转换为 ISO 8601 格式"""
    if chrome_time > 0:
        # Chrome时间戳基准：1601年1月1日（Windows文件时间格式）
        epoch_time = datetime.datetime.fromisoformat("1601-01-01T00:00:00+00:00")
        return (
            epoch_time + datetime.timedelta(microseconds=chrome_time)
        ).isoformat() + "Z"
    return None


def find_chromium_profiles_sync(browser_base_path: Path) -> List[Path]:
    """查找 Chromium 浏览器的所有用户配置文件目录"""
    if not browser_base_path.exists():
        return []

    profile_paths = []
    if (browser_base_path / "Default").exists():
        profile_paths.append(browser_base_path / "Default")

    max_profile_search = get_config_value("browser.max_profile_search", default=10)
    for i in range(1, max_profile_search + 1):
        profile_dir = browser_base_path / f"Profile {i}"
        if profile_dir.exists():
            profile_paths.append(profile_dir)

    return profile_paths


def detect_installed_browsers_sync() -> Dict[str, Any]:
    """检测当前系统已安装的浏览器"""
    debug_print("[调试] 开始检测已安装的浏览器")
    try:
        profile_path = _get_user_profile_path_sync()
        if not profile_path or platform.system() != "Windows":
            return {"status": "error", "message": "此工具当前仅支持Windows操作系统。"}

        # 定义浏览器检测信息
        browsers_to_check = {
            "Google Chrome": {
                "user_data_path": profile_path / "AppData/Local/Google/Chrome/User Data",
                "exe_paths": [
                    "C:/Program Files/Google/Chrome/Application/chrome.exe",
                    "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe",
                ],
            },
            "Microsoft Edge": {
                "user_data_path": profile_path / "AppData/Local/Microsoft/Edge/User Data",
                "exe_paths": [
                    "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
                    "C:/Program Files/Microsoft/Edge/Application/msedge.exe",
                ],
            },
            "Firefox": {
                "user_data_path": profile_path / "AppData/Roaming/Mozilla/Firefox/Profiles",
                "exe_paths": [
                    "C:/Program Files/Mozilla Firefox/firefox.exe",
                    "C:/Program Files (x86)/Mozilla Firefox/firefox.exe",
                ],
            },
            "Brave": {
                "user_data_path": profile_path / "AppData/Local/BraveSoftware/Brave-Browser/User Data",
                "exe_paths": [
                    "C:/Program Files/BraveSoftware/Brave-Browser/Application/brave.exe",
                    "C:/Program Files (x86)/BraveSoftware/Brave-Browser/Application/brave.exe",
                ],
            },
        }

        installed_browsers = []

        for browser_name, browser_info in browsers_to_check.items():
            browser_data = {
                "name": browser_name,
                "installed": False,
                "has_user_data": False,
                "executable_path": None,
                "user_data_path": None,
                "profile_count": 0,
            }

            # 检查用户数据目录是否存在
            user_data_path = browser_info["user_data_path"]
            if user_data_path.exists():
                browser_data["has_user_data"] = True
                browser_data["user_data_path"] = str(user_data_path)

                # 统计配置文件数量(仅对Chromium内核浏览器)
                if browser_name != "Firefox":
                    profiles = find_chromium_profiles_sync(user_data_path)
                    browser_data["profile_count"] = len(profiles)
                else:
                    # Firefox使用不同的配置文件结构
                    try:
                        profile_count = len([p for p in user_data_path.iterdir() if p.is_dir()])
                        browser_data["profile_count"] = profile_count
                    except:
                        browser_data["profile_count"] = 0

            # 检查可执行文件是否存在
            for exe_path in browser_info["exe_paths"]:
                if Path(exe_path).exists():
                    browser_data["installed"] = True
                    browser_data["executable_path"] = exe_path
                    break

            # 如果有用户数据或可执行文件,则认为浏览器已安装
            if browser_data["has_user_data"] or browser_data["installed"]:
                installed_browsers.append(browser_data)

        debug_print(f"[调试] 检测完成,找到 {len(installed_browsers)} 个已安装的浏览器")
        return {
            "status": "success",
            "count": len(installed_browsers),
            "browsers": installed_browsers,
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"检测浏览器时出错: {str(e)}",
            "traceback": traceback.format_exc(),
        }


def get_chromium_data_sync(
    browser_name: str, data_type: str, max_items_per_profile: int
) -> Dict[str, Any]:
    """从 Chromium 浏览器中提取历史记录或下载记录"""
    debug_print(f"[调试] 开始执行同步函数 get_chromium_data_sync，目标: {browser_name}")
    try:
        profile_path = _get_user_profile_path_sync()
        if not profile_path or platform.system() != "Windows":
            return {"status": "error", "message": "此工具当前仅支持Windows操作系统。"}

        # Windows标准浏览器路径
        chrome_path = "AppData/Local/Google/Chrome/User Data"
        edge_path = "AppData/Local/Microsoft/Edge/User Data"

        db_locations = {
            "Google Chrome": profile_path / chrome_path,
            "Microsoft Edge": profile_path / edge_path,
        }

        base_path = db_locations.get(browser_name)
        if not base_path:
            return {"status": "error", "message": f"未知的浏览器名称: {browser_name}"}
        debug_print(f"[调试] 浏览器基础路径: {base_path}")

        profile_dirs = find_chromium_profiles_sync(base_path)
        if not profile_dirs:
            return {
                "status": "success_not_found",
                "message": f"未找到 {browser_name} 的任何用户配置文件目录。",
            }
        debug_print(f"[调试] 找到的Profile目录: {[p.name for p in profile_dirs]}")

        all_items = []
        # Chrome/Edge数据库文件名是固定的
        db_filename = "History"
        temp_prefix = "temp_"

        for p_dir in profile_dirs:
            db_path = p_dir / db_filename
            debug_print(f"[调试] 正在检查 {db_filename} 文件: {db_path}")
            if not db_path.exists():
                continue

            temp_db_path = (
                db_path.parent / f"{temp_prefix}{db_path.name}_{os.getpid()}.db"
            )
            debug_print(f"[调试] 准备复制文件到: {temp_db_path}")
            shutil.copy2(db_path, temp_db_path)
            debug_print("[调试] 文件复制成功。")

            conn = None
            try:
                conn = sqlite3.connect(f"file:{temp_db_path}?mode=ro", uri=True)
                cursor = conn.cursor()

                # Chrome/Edge数据库结构是固定的，SQL查询不应该让用户修改
                if data_type == "history":
                    query = f"SELECT u.url, u.title, v.visit_time FROM urls u, visits v WHERE u.id = v.url ORDER BY v.visit_time DESC LIMIT {max_items_per_profile};"
                elif data_type == "downloads":
                    query = f"SELECT target_path, tab_url, mime_type, total_bytes, start_time, end_time, state, danger_type FROM downloads ORDER BY start_time DESC LIMIT {max_items_per_profile};"

                for row in cursor.execute(query):
                    item = {"profile": p_dir.name}
                    if data_type == "history":
                        item.update(
                            {
                                "url": row[0],
                                "title": row[1],
                                "last_visit_time_utc": _convert_chrome_time_sync(
                                    row[2]
                                ),
                            }
                        )
                    elif data_type == "downloads":
                        item.update(
                            {
                                "target_path": row[0],
                                "source_url": row[1],
                                "mime_type": row[2],
                                "total_bytes": row[3],
                                "start_time_utc": _convert_chrome_time_sync(row[4]),
                                "end_time_utc": _convert_chrome_time_sync(row[5]),
                                "state": row[6],
                                "danger_type": row[7],
                            }
                        )
                    all_items.append(item)
            finally:
                if conn:
                    conn.close()
                if os.path.exists(temp_db_path):
                    os.remove(temp_db_path)

        if data_type == "history":
            all_items.sort(
                key=lambda x: x.get("last_visit_time_utc") or "", reverse=True
            )
        elif data_type == "downloads":
            all_items.sort(key=lambda x: x.get("start_time_utc") or "", reverse=True)

        debug_print("[调试] 同步函数执行完毕。")
        return {"status": "success", "count": len(all_items), "data": all_items}

    except Exception as e:
        return {
            "status": "error",
            "message": f"执行同步任务时出错: {str(e)}",
            "traceback": traceback.format_exc(),
        }


# --- 异步MCP工具 ---


@mcp.tool()
async def detect_installed_browsers() -> Dict[str, Any]:
    """
    检测当前Windows系统已安装的浏览器。

    返回每个浏览器的安装状态、可执行文件路径、用户数据路径和配置文件数量。
    支持检测: Google Chrome, Microsoft Edge, Firefox, Brave。
    """
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(None, detect_installed_browsers_sync)
    return result


@mcp.tool()
async def get_chrome_history(max_items_per_profile: int = None) -> Dict[str, Any]:
    """
    从Google Chrome的所有用户配置中获取浏览历史记录。

    Args:
        max_items_per_profile (int): 从每个用户配置中返回历史记录的最大条目数。
    """
    if max_items_per_profile is None:
        max_items_per_profile = get_config_value(
            "browser.max_history_items", default=100
        )
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(
        None, get_chromium_data_sync, "Google Chrome", "history", max_items_per_profile
    )
    return result


@mcp.tool()
async def get_chrome_downloads(max_items_per_profile: int = None) -> Dict[str, Any]:
    """
    从Google Chrome的所有用户配置中获取下载历史记录。

    Args:
        max_items_per_profile (int): 从每个用户配置中返回下载记录的最大条目数。
    """
    if max_items_per_profile is None:
        max_items_per_profile = get_config_value(
            "browser.max_download_items", default=50
        )
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(
        None,
        get_chromium_data_sync,
        "Google Chrome",
        "downloads",
        max_items_per_profile,
    )
    return result


@mcp.tool()
async def get_edge_history(max_items_per_profile: int = None) -> Dict[str, Any]:
    """
    从Microsoft Edge的所有用户配置中获取浏览历史记录。

    Args:
        max_items_per_profile (int): 从每个用户配置中返回历史记录的最大条目数。
    """
    if max_items_per_profile is None:
        max_items_per_profile = get_config_value(
            "browser.max_history_items", default=100
        )
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(
        None, get_chromium_data_sync, "Microsoft Edge", "history", max_items_per_profile
    )
    return result


@mcp.tool()
async def get_edge_downloads(max_items_per_profile: int = None) -> Dict[str, Any]:
    """
    从Microsoft Edge的所有用户配置中获取下载历史记录。

    Args:
        max_items_per_profile (int): 从每个用户配置中返回下载记录的最大条目数。
    """
    if max_items_per_profile is None:
        max_items_per_profile = get_config_value(
            "browser.max_download_items", default=50
        )
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(
        None,
        get_chromium_data_sync,
        "Microsoft Edge",
        "downloads",
        max_items_per_profile,
    )
    return result


# --- 主程序入口 ---
if __name__ == "__main__":
    if DEBUG_MODE:
        print("--- 处于调试模式 ---")

        async def main_test():
            print("[测试开始] 准备直接调用Edge下载记录取证逻辑...")
            result = await get_edge_downloads(max_items_per_profile=5)
            print("\n[测试成功] 工具函数已返回结果：")
            print(json.dumps(result, indent=2, ensure_ascii=False))

        asyncio.run(main_test())
    else:
        mcp.run(transport="stdio")
