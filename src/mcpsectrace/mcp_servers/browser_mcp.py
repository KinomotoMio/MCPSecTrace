import os
import sqlite3
import datetime
import platform
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, List
import sys
import asyncio
import traceback
import json

# --- 调试开关 ---
DEBUG_MODE = '--debug' in sys.argv

def debug_print(message: str):
    """仅在调试模式下输出调试信息到标准错误流"""
    if DEBUG_MODE:
        print(message, file=sys.stderr)

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    debug_print("[致命错误] 请先运行: uv add \"mcp[cli]\" httpx")
    sys.exit(1)

mcp = FastMCP("browser_tools", log_level="ERROR")

def _get_user_profile_path_sync() -> Optional[Path]:
    """获取当前用户的主目录路径（仅支持 Windows）"""
    if platform.system() == "Windows":
        return Path(os.environ['USERPROFILE'])
    return Path.home()

def _convert_chrome_time_sync(chrome_time: int) -> Optional[str]:
    """将 Chrome 时间戳转换为 ISO 8601 格式"""
    if chrome_time > 0:
        return (datetime.datetime(1601, 1, 1) + datetime.timedelta(microseconds=chrome_time)).isoformat() + "Z"
    return None

def find_chromium_profiles_sync(browser_base_path: Path) -> List[Path]:
    """查找 Chromium 浏览器的所有用户配置文件目录"""
    if not browser_base_path.exists():
        return []

    profile_paths = []
    if (browser_base_path / "Default").exists():
        profile_paths.append(browser_base_path / "Default")

    for i in range(1, 11):
        profile_dir = browser_base_path / f"Profile {i}"
        if profile_dir.exists():
            profile_paths.append(profile_dir)

    return profile_paths

def get_chromium_data_sync(browser_name: str, data_type: str, max_items_per_profile: int) -> Dict[str, Any]:
    """从 Chromium 浏览器中提取历史记录或下载记录"""
    debug_print(f"[调试] 开始执行同步函数 get_chromium_data_sync，目标: {browser_name}")
    try:
        profile_path = _get_user_profile_path_sync()
        if not profile_path or platform.system() != "Windows":
            return {"status": "error", "message": "此工具当前仅支持Windows操作系统。"}

        db_locations = {
            "Google Chrome": profile_path / "AppData/Local/Google/Chrome/User Data",
            "Microsoft Edge": profile_path / "AppData/Local/Microsoft/Edge/User Data"
        }

        base_path = db_locations.get(browser_name)
        if not base_path:
            return {"status": "error", "message": f"未知的浏览器名称: {browser_name}"}
        debug_print(f"[调试] 浏览器基础路径: {base_path}")

        profile_dirs = find_chromium_profiles_sync(base_path)
        if not profile_dirs:
            return {"status": "success_not_found", "message": f"未找到 {browser_name} 的任何用户配置文件目录。"}
        debug_print(f"[调试] 找到的Profile目录: {[p.name for p in profile_dirs]}")

        all_items = []
        for p_dir in profile_dirs:
            db_path = p_dir / "History"
            debug_print(f"[调试] 正在检查 History 文件: {db_path}")
            if not db_path.exists():
                continue

            temp_db_path = db_path.parent / f"temp_{db_path.name}_{os.getpid()}.db"
            debug_print(f"[调试] 准备复制文件到: {temp_db_path}")
            shutil.copy2(db_path, temp_db_path)
            debug_print("[调试] 文件复制成功。")

            conn = None
            try:
                conn = sqlite3.connect(f"file:{temp_db_path}?mode=ro", uri=True)
                cursor = conn.cursor()
                query = ""
                if data_type == 'history':
                    query = f"SELECT u.url, u.title, v.visit_time FROM urls u, visits v WHERE u.id = v.url ORDER BY v.visit_time DESC LIMIT {max_items_per_profile};"
                elif data_type == 'downloads':
                    query = f"SELECT target_path, tab_url, mime_type, total_bytes, start_time, end_time, state, danger_type FROM downloads ORDER BY start_time DESC LIMIT {max_items_per_profile};"

                for row in cursor.execute(query):
                    item = {"profile": p_dir.name}
                    if data_type == 'history':
                        item.update(
                            {"url": row[0], "title": row[1], "last_visit_time_utc": _convert_chrome_time_sync(row[2])})
                    elif data_type == 'downloads':
                        item.update(
                            {"target_path": row[0], "source_url": row[1], "mime_type": row[2], "total_bytes": row[3],
                             "start_time_utc": _convert_chrome_time_sync(row[4]),
                             "end_time_utc": _convert_chrome_time_sync(row[5]), "state": row[6], "danger_type": row[7]})
                    all_items.append(item)
            finally:
                if conn:
                    conn.close()
                if os.path.exists(temp_db_path):
                    os.remove(temp_db_path)

        if data_type == 'history':
            all_items.sort(key=lambda x: x.get('last_visit_time_utc') or '', reverse=True)
        elif data_type == 'downloads':
            all_items.sort(key=lambda x: x.get('start_time_utc') or '', reverse=True)

        debug_print("[调试] 同步函数执行完毕。")
        return {"status": "success", "count": len(all_items), "data": all_items}

    except Exception as e:
        return {"status": "error", "message": f"执行同步任务时出错: {str(e)}", "traceback": traceback.format_exc()}

# --- 异步MCP工具 ---

@mcp.tool()  # 添加资源绑定
async def get_chrome_history(max_items_per_profile: int = 100) -> Dict[str, Any]:
    """
    从Google Chrome的所有用户配置中获取浏览历史记录。

    Args:
        max_items_per_profile (int): 从每个用户配置中返回历史记录的最大条目数。
    """
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(
        None, get_chromium_data_sync, "Google Chrome", "history", max_items_per_profile
    )
    return result

@mcp.tool()
async def get_chrome_downloads(max_items_per_profile: int = 50) -> Dict[str, Any]:
    """
    从Google Chrome的所有用户配置中获取下载历史记录。

    Args:
        max_items_per_profile (int): 从每个用户配置中返回下载记录的最大条目数。
    """
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(
        None, get_chromium_data_sync, "Google Chrome", "downloads", max_items_per_profile
    )
    return result

@mcp.tool()
async def get_edge_history(max_items_per_profile: int = 100) -> Dict[str, Any]:
    """
    从Microsoft Edge的所有用户配置中获取浏览历史记录。

    Args:
        max_items_per_profile (int): 从每个用户配置中返回历史记录的最大条目数。
    """
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(
        None, get_chromium_data_sync, "Microsoft Edge", "history", max_items_per_profile
    )
    return result

@mcp.tool()
async def get_edge_downloads(max_items_per_profile: int = 50) -> Dict[str, Any]:
    """
    从Microsoft Edge的所有用户配置中获取下载历史记录。

    Args:
        max_items_per_profile (int): 从每个用户配置中返回下载记录的最大条目数。
    """
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(
        None, get_chromium_data_sync, "Microsoft Edge", "downloads", max_items_per_profile
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
        mcp.run(transport='stdio')