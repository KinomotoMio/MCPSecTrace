"""测试 Everything MCP 的查询功能"""

import sys
from pathlib import Path

# 添加项目路径到 sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from mcpsectrace.mcp_servers.everything_mcp.src.mcp_server_everything_search.search_interface import (
    SearchProvider,
)


def test_search_file(filename: str, max_results: int = 10):
    """
    测试搜索单个文件。

    Args:
        filename: 要搜索的文件名
        max_results: 最大返回结果数
    """
    print("=" * 80)
    print(f"测试搜索文件: {filename}")
    print("=" * 80)
    print()

    try:
        # 获取搜索提供者
        search_provider = SearchProvider.get_provider()
        print(f"✓ 搜索提供者初始化成功: {type(search_provider).__name__}")
        print()

        # 执行搜索
        print(f"正在搜索: {filename}")
        print(f"最大结果数: {max_results}")
        print()

        results = search_provider.search_files(
            query=filename,
            max_results=max_results
        )

        # 输出结果
        if results:
            print(f"✓ 找到 {len(results)} 个结果:")
            print("-" * 80)
            for i, result in enumerate(results, 1):
                print(f"\n结果 {i}:")
                print(f"  文件名: {result.filename}")
                print(f"  完整路径: {result.path}")
                print(f"  扩展名: {result.extension or 'N/A'}")
                print(f"  大小: {result.size:,} 字节")
                print(f"  修改时间: {result.modified or 'N/A'}")
        else:
            print(f"✗ 未找到任何结果")

        print()
        print("=" * 80)

    except Exception as e:
        print(f"✗ 搜索失败: {e}")
        import traceback
        traceback.print_exc()


def test_multiple_files():
    """测试搜索多个文件（模拟可疑进程和文件的查找逻辑）"""
    print("\n" + "=" * 80)
    print("测试批量搜索（模拟可疑进程和文件查找）")
    print("=" * 80)
    print()

    # 模拟的可疑文件列表（从CSV中提取）
    test_files = [
        "https_keylog.log",      # 系统进程，应该能找到
    ]

    try:
        search_provider = SearchProvider.get_provider()
        print(f"✓ 搜索提供者初始化成功\n")

        found_results = {}
        not_found = []

        for filename in test_files:
            print(f"搜索: {filename} ... ", end="", flush=True)
            try:
                results = search_provider.search_files(
                    query=filename,
                    max_results=3  # 每个文件最多3个结果
                )
                if results:
                    found_results[filename] = [r.path for r in results]
                    print(f"✓ 找到 {len(results)} 个")
                else:
                    not_found.append(filename)
                    print("✗ 未找到")
            except Exception as e:
                not_found.append(filename)
                print(f"✗ 错误: {e}")

        # 汇总结果
        print("\n" + "=" * 80)
        print("汇总结果")
        print("=" * 80)
        print()

        print(f"总文件数: {len(test_files)}")
        print(f"  ├─ 找到: {len(found_results)} 个")
        print(f"  └─ 未找到: {len(not_found)} 个")
        print()

        if found_results:
            print("找到的文件:")
            print("-" * 80)
            for filename, paths in found_results.items():
                print(f"\n{filename}:")
                for path in paths:
                    print(f"  - {path}")

        if not_found:
            print("\n未找到的文件:")
            print("-" * 80)
            for filename in not_found:
                print(f"  - {filename}")

        print()

    except Exception as e:
        print(f"✗ 批量搜索失败: {e}")
        import traceback
        traceback.print_exc()


def main():
    """主函数"""
    print("\n" + "#" * 80)
    print("# Everything MCP 搜索功能测试")
    print("#" * 80)
    print()

    # 测试1: 搜索单个已知文件
    print("【测试1】搜索系统文件 notepad.exe")
    test_search_file("notepad.exe", max_results=5)

    # 测试2: 搜索可能不存在的文件
    print("\n【测试2】搜索可能不存在的文件 malicious.exe")
    test_search_file("malicious.exe", max_results=5)

    # 测试3: 批量搜索
    print("\n【测试3】批量搜索测试")
    test_multiple_files()

    print("\n" + "#" * 80)
    print("# 测试完成")
    print("#" * 80)


if __name__ == "__main__":
    main()
