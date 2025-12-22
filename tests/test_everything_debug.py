"""诊断 Everything 搜索问题"""

import sys
import os
from pathlib import Path

# 添加项目路径到 sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from mcpsectrace.mcp_servers.everything_mcp.src.mcp_server_everything_search.search_interface import (
    SearchProvider,
)


def test_desktop_file():
    """测试桌面文件搜索"""
    print("=" * 80)
    print("诊断 Everything 搜索问题")
    print("=" * 80)
    print()

    # 获取桌面路径
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    print(f"当前用户桌面路径: {desktop}")
    print()

    # 检查文件是否真的存在
    test_file = os.path.join(desktop, "https_keylog.log")
    print(f"检查文件: {test_file}")
    if os.path.exists(test_file):
        print(f"[OK] 文件存在！")
        print(f"  文件大小: {os.path.getsize(test_file)} 字节")
        print(f"  绝对路径: {os.path.abspath(test_file)}")
    else:
        print(f"[FAIL] 文件不存在")
        # 列出桌面上所有 .log 文件
        print("\n桌面上的 .log 文件:")
        if os.path.exists(desktop):
            for file in os.listdir(desktop):
                if file.endswith('.log'):
                    print(f"  - {file}")
        return
    print()

    try:
        # 初始化搜索提供者
        search_provider = SearchProvider.get_provider()
        print(f"[OK] 搜索提供者初始化成功: {type(search_provider).__name__}")
        print()

        # 测试1: 只搜索文件名
        print("-" * 80)
        print("测试1: 搜索文件名 'https_keylog.log'")
        print("-" * 80)
        results = search_provider.search_files(
            query="https_keylog.log",
            max_results=10
        )
        print(f"找到 {len(results)} 个结果:")
        for i, r in enumerate(results, 1):
            print(f"  {i}. {r.path}")
        print()

        # 测试2: 搜索部分文件名
        print("-" * 80)
        print("测试2: 搜索部分文件名 'keylog'")
        print("-" * 80)
        results = search_provider.search_files(
            query="keylog",
            max_results=10
        )
        print(f"找到 {len(results)} 个结果:")
        for i, r in enumerate(results, 1):
            print(f"  {i}. {r.path}")
        print()

        # 测试3: 搜索 .log 扩展名
        print("-" * 80)
        print("测试3: 搜索 '*.log' 文件")
        print("-" * 80)
        results = search_provider.search_files(
            query="*.log",
            max_results=10
        )
        print(f"找到 {len(results)} 个结果:")
        for i, r in enumerate(results, 1):
            print(f"  {i}. {r.path}")
        print()

        # 测试4: 搜索桌面路径下的文件
        print("-" * 80)
        print(f"测试4: 在桌面路径下搜索 'https_keylog.log'")
        print("-" * 80)
        # Everything 路径语法: path:桌面路径 文件名
        desktop_normalized = desktop.replace("\\", "\\\\")  # 转义反斜杠
        search_query = f'path:"{desktop_normalized}" https_keylog.log'
        print(f"查询语句: {search_query}")
        results = search_provider.search_files(
            query=search_query,
            max_results=10
        )
        print(f"找到 {len(results)} 个结果:")
        for i, r in enumerate(results, 1):
            print(f"  {i}. {r.path}")
        print()

        # 测试5: 完整路径搜索
        print("-" * 80)
        print("测试5: 使用完整路径搜索")
        print("-" * 80)
        full_path = test_file.replace("\\", "\\\\")
        print(f"查询语句: {full_path}")
        results = search_provider.search_files(
            query=full_path,
            max_results=10,
            match_path=True  # 匹配路径
        )
        print(f"找到 {len(results)} 个结果:")
        for i, r in enumerate(results, 1):
            print(f"  {i}. {r.path}")
        print()

    except Exception as e:
        print(f"[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_desktop_file()
