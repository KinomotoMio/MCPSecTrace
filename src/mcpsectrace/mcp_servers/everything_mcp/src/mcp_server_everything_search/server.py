"""跨平台文件搜索的 MCP 服务器实现。"""

import json
import platform
import sys
import os
import csv
from typing import List, Dict, Optional
from pathlib import Path
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool, Resource, ResourceTemplate, Prompt
from pydantic import BaseModel, Field

from .platform_search import UnifiedSearchQuery, WindowsSpecificParams, build_search_command
from .search_interface import SearchProvider

class SearchQuery(BaseModel):
    """搜索查询参数的模型。"""
    query: str = Field(
        description="Search query string. See the search syntax guide for details."
    )
    max_results: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Maximum number of results to return (1-1000)"
    )
    match_path: bool = Field(
        default=False,
        description="Match against full path instead of filename only"
    )
    match_case: bool = Field(
        default=False,
        description="Enable case-sensitive search"
    )
    match_whole_word: bool = Field(
        default=False,
        description="Match whole words only"
    )
    match_regex: bool = Field(
        default=False,
        description="Enable regex search"
    )
    sort_by: int = Field(
        default=1,
        description="Sort order for results (Note: Not all sort options available on all platforms)"
    )

class MaliciousFileQuery(BaseModel):
    """恶意释放文件查询参数的模型。"""
    csv_file_path: str = Field(
        description="CSV 文件路径，包含释放文件信息"
    )
    max_search_depth: int = Field(
        default=2,
        ge=0,
        le=5,
        description="最大向上搜索目录层数（默认为2）"
    )

def query_malicious_files_from_csv(
    csv_path: str,
    search_provider: SearchProvider,
    max_search_depth: int = 2
) -> str:
    """
    从CSV文件查询恶意释放的文件。

    检查逻辑：
    - 第0层：在预期路径所在目录下，使用Everything查找文件
    - 第1层：在上一层目录下，使用Everything查找文件
    - 第2层：在上两层目录下，使用Everything查找文件
    - 第3层：在全局范围内，使用Everything查找文件

    Args:
        csv_path: CSV文件路径
        search_provider: 搜索提供者
        max_search_depth: 最大向上检查目录层数

    Returns:
        查询结果字符串
    """
    try:
        # 检查CSV文件是否存在
        if not os.path.exists(csv_path):
            return f"错误: CSV文件不存在: {csv_path}"

        # 读取CSV文件
        results_by_status = {
            "找到的文件": [],
            "文件存在": [],
            "上一层目录存在": [],
            "上两层目录存在": [],
            "全局范围存在": [],
            "未找到的文件": []
        }

        with open(csv_path, 'r', encoding='utf-8') as f:
            csv_reader = csv.DictReader(f)

            for row in csv_reader:
                file_path = row.get("文件路径", "").strip()
                file_name = row.get("文件名称", "").strip()
                sha256 = row.get("文件SHA256", "").strip()
                target = row.get("查询目标", "").strip()
                environment = row.get("环境", "").strip()

                if not file_path or not file_name:
                    continue

                # 文件信息记录
                file_info = {
                    "查询目标": target,
                    "环境": environment,
                    "文件名": file_name,
                    "预期路径": file_path,
                    "SHA256": sha256
                }

                found = False
                found_status = None
                check_result = None

                # 第0层：在预期路径所在目录下查找文件
                try:
                    file_dir = str(Path(file_path).parent)
                    search_query = f"path:{file_dir} {file_name}"
                    results = search_provider.search_files(query=search_query, max_results=10)
                    if results and any(file_name.lower() in r.filename.lower() for r in results):
                        found = True
                        found_status = "文件存在"
                        check_result = f"在预期目录 {file_dir} 中找到"
                except Exception as e:
                    print(f"第0层查询失败: {e}", file=sys.stderr)

                # 如果文件未找到，检查第1层：上一层目录下查找文件
                if not found and max_search_depth >= 1:
                    try:
                        parent_dir = str(Path(file_path).parent.parent)
                        search_query = f"path:{parent_dir} {file_name}"
                        results = search_provider.search_files(query=search_query, max_results=10)
                        if results and any(file_name.lower() in r.filename.lower() for r in results):
                            found = True
                            found_status = "上一层目录存在"
                            check_result = f"在上一层目录 {parent_dir} 中找到"
                    except Exception as e:
                        print(f"第1层查询失败: {e}", file=sys.stderr)

                # 如果仍未找到，检查第2层：上两层目录下查找文件
                if not found and max_search_depth >= 2:
                    try:
                        grandparent_dir = str(Path(file_path).parent.parent.parent)
                        search_query = f"path:{grandparent_dir} {file_name}"
                        results = search_provider.search_files(query=search_query, max_results=10)
                        if results and any(file_name.lower() in r.filename.lower() for r in results):
                            found = True
                            found_status = "上两层目录存在"
                            check_result = f"在上两层目录 {grandparent_dir} 中找到"
                    except Exception as e:
                        print(f"第2层查询失败: {e}", file=sys.stderr)

                # 如果仍未找到，检查第3层：在全局范围内查找文件
                if not found:
                    try:
                        search_query = file_name
                        results = search_provider.search_files(query=search_query, max_results=10)
                        if results and any(file_name.lower() in r.filename.lower() for r in results):
                            found = True
                            found_status = "全局范围存在"
                            found_paths = [r.path for r in results if file_name.lower() in r.filename.lower()]
                            check_result = f"在全局范围内找到: {', '.join(found_paths[:3])}"
                    except Exception as e:
                        print(f"第3层查询失败: {e}", file=sys.stderr)

                # 记录结果
                if found:
                    file_info["检查结果"] = check_result
                    file_info["状态"] = found_status
                    results_by_status["找到的文件"].append(file_info)
                    results_by_status[found_status].append(file_info)
                else:
                    results_by_status["未找到的文件"].append(file_info)

        # 格式化输出
        output_lines = []
        output_lines.append(f"恶意释放文件查询结果")
        output_lines.append(f"CSV文件: {csv_path}")
        output_lines.append("")

        # 统计信息
        total_files = len(results_by_status["找到的文件"]) + len(results_by_status["未找到的文件"])
        output_lines.append(f"统计信息:")
        output_lines.append(f"  总文件数: {total_files}")
        output_lines.append(f"  找到: {len(results_by_status['找到的文件'])}")
        output_lines.append(f"    ├─ 文件存在（第0层）: {len(results_by_status['文件存在'])}个 ⭐⭐⭐")
        output_lines.append(f"    ├─ 上一层目录存在（第1层）: {len(results_by_status['上一层目录存在'])}个 ⭐⭐")
        output_lines.append(f"    ├─ 上两层目录存在（第2层）: {len(results_by_status['上两层目录存在'])}个 ⭐")
        output_lines.append(f"    └─ 全局范围存在（第3层）: {len(results_by_status['全局范围存在'])}个 ⭐")
        output_lines.append(f"  未找到: {len(results_by_status['未找到的文件'])}个 ✓")
        output_lines.append("")

        # 文件存在
        if results_by_status["文件存在"]:
            output_lines.append("=" * 80)
            output_lines.append(f"【⭐⭐⭐ 文件直接存在】({len(results_by_status['文件存在'])}个)")
            output_lines.append("=" * 80)
            output_lines.append("状态: 恶意文件仍保留在系统中，风险最高")
            output_lines.append("")
            for file_info in results_by_status["文件存在"]:
                output_lines.append(f"  文件名: {file_info['文件名']}")
                output_lines.append(f"  查询目标: {file_info['查询目标']}")
                output_lines.append(f"  环境: {file_info['环境']}")
                output_lines.append(f"  预期路径: {file_info['预期路径']}")
                output_lines.append(f"  SHA256: {file_info['SHA256']}")
                output_lines.append("")

        # 上一层目录存在
        if results_by_status["上一层目录存在"]:
            output_lines.append("=" * 80)
            output_lines.append(f"【⭐⭐ 上一层目录存在】({len(results_by_status['上一层目录存在'])}个)")
            output_lines.append("=" * 80)
            output_lines.append("状态: 释放文件被删除，但释放目录仍存在（可能被清理工具部分清理）")
            output_lines.append("")
            for file_info in results_by_status["上一层目录存在"]:
                output_lines.append(f"  文件名: {file_info['文件名']}")
                output_lines.append(f"  查询目标: {file_info['查询目标']}")
                output_lines.append(f"  环境: {file_info['环境']}")
                output_lines.append(f"  预期路径: {file_info['预期路径']}")
                output_lines.append(f"  存在目录: {file_info['检查结果']}")
                output_lines.append(f"  SHA256: {file_info['SHA256']}")
                output_lines.append("")

        # 上两层目录存在
        if results_by_status["上两层目录存在"]:
            output_lines.append("=" * 80)
            output_lines.append(f"【⭐ 上两层目录存在】({len(results_by_status['上两层目录存在'])}个)")
            output_lines.append("=" * 80)
            output_lines.append("状态: 释放目录也被删除，但上层目录仍存在（清理相对彻底）")
            output_lines.append("")
            for file_info in results_by_status["上两层目录存在"]:
                output_lines.append(f"  文件名: {file_info['文件名']}")
                output_lines.append(f"  查询目标: {file_info['查询目标']}")
                output_lines.append(f"  环境: {file_info['环境']}")
                output_lines.append(f"  预期路径: {file_info['预期路径']}")
                output_lines.append(f"  存在目录: {file_info['检查结果']}")
                output_lines.append(f"  SHA256: {file_info['SHA256']}")
                output_lines.append("")

        # 全局范围存在
        if results_by_status["全局范围存在"]:
            output_lines.append("=" * 80)
            output_lines.append(f"【⭐ 全局范围存在】({len(results_by_status['全局范围存在'])}个)")
            output_lines.append("=" * 80)
            output_lines.append("状态: 文件在系统其他位置被找到（可能被移动或恶意软件仍在运行）")
            output_lines.append("")
            for file_info in results_by_status["全局范围存在"]:
                output_lines.append(f"  文件名: {file_info['文件名']}")
                output_lines.append(f"  查询目标: {file_info['查询目标']}")
                output_lines.append(f"  环境: {file_info['环境']}")
                output_lines.append(f"  预期路径: {file_info['预期路径']}")
                output_lines.append(f"  发现位置: {file_info['检查结果']}")
                output_lines.append(f"  SHA256: {file_info['SHA256']}")
                output_lines.append("")

        # 未找到的文件
        if results_by_status["未找到的文件"]:
            output_lines.append("=" * 80)
            output_lines.append(f"【✓ 完全未找到】({len(results_by_status['未找到的文件'])}个)")
            output_lines.append("=" * 80)
            output_lines.append("状态: 文件和目录均不存在，清理完全（最低风险）")
            output_lines.append("")
            for file_info in results_by_status["未找到的文件"]:
                output_lines.append(f"  文件名: {file_info['文件名']}")
                output_lines.append(f"  查询目标: {file_info['查询目标']}")
                output_lines.append(f"  环境: {file_info['环境']}")
                output_lines.append(f"  预期路径: {file_info['预期路径']}")
                output_lines.append(f"  SHA256: {file_info['SHA256']}")
                output_lines.append("")

        return "\n".join(output_lines)

    except Exception as e:
        return f"查询失败: {str(e)}"

async def serve() -> None:
    """运行服务器。"""
    current_platform = platform.system().lower()
    search_provider = SearchProvider.get_provider()

    server = Server("universal-search")

    @server.list_resources()
    async def list_resources() -> list[Resource]:
        """返回空列表，因为此服务器不提供任何资源。"""
        return []

    @server.list_resource_templates()
    async def list_resource_templates() -> list[ResourceTemplate]:
        """返回空列表，因为此服务器不提供任何资源模板。"""
        return []

    @server.list_prompts()
    async def list_prompts() -> list[Prompt]:
        """返回空列表，因为此服务器不提供任何提示。"""
        return []

    @server.list_tools()
    async def list_tools() -> List[Tool]:
        """返回具有平台特定文档和 schema 的搜索工具。"""
        platform_info = {
            'windows': "Using Everything SDK with full search capabilities",
            'darwin': "Using mdfind (Spotlight) with native macOS search capabilities",
            'linux': "Using locate with Unix-style search capabilities"
        }

        syntax_docs = {
            'darwin': """macOS Spotlight (mdfind) Search Syntax:
                
Basic Usage:
- Simple text search: Just type the words you're looking for
- Phrase search: Use quotes ("exact phrase")
- Filename search: -name "filename"
- Directory scope: -onlyin /path/to/dir

Special Parameters:
- Live updates: -live
- Literal search: -literal
- Interpreted search: -interpret

Metadata Attributes:
- kMDItemDisplayName
- kMDItemTextContent
- kMDItemKind
- kMDItemFSSize
- And many more OS X metadata attributes""",

            'linux': """Linux Locate Search Syntax:

Basic Usage:
- Simple pattern: locate filename
- Case-insensitive: -i pattern
- Regular expressions: -r pattern
- Existing files only: -e pattern
- Count matches: -c pattern

Pattern Wildcards:
- * matches any characters
- ? matches single character
- [] matches character classes

Examples:
- locate -i "*.pdf"
- locate -r "/home/.*\.txt$"
- locate -c "*.doc"
""",
            'windows': """Search for files and folders using Everything SDK.
                
Features:
- Fast file and folder search across all indexed drives
- Support for wildcards and boolean operators
- Multiple sort options (name, path, size, dates)
- Case-sensitive and whole word matching
- Regular expression support
- Path matching
Search Syntax Guide:
1. Basic Operators:
   - space: AND operator
   - |: OR operator
   - !: NOT operator
   - < >: Grouping
   - " ": Search for an exact phrase
2. Wildcards:
   - *: Matches zero or more characters
   - ?: Matches exactly one character
   Note: Wildcards match the whole filename by default. Disable Match whole filename to match wildcards anywhere.
3. Functions:
   Size and Count:
   - size:<size>[kb|mb|gb]: Search by file size
   - count:<max>: Limit number of results
   - childcount:<count>: Folders with specific number of children
   - childfilecount:<count>: Folders with specific number of files
   - childfoldercount:<count>: Folders with specific number of subfolders
   - len:<length>: Match filename length
   Dates:
   - datemodified:<date>, dm:<date>: Modified date
   - dateaccessed:<date>, da:<date>: Access date
   - datecreated:<date>, dc:<date>: Creation date
   - daterun:<date>, dr:<date>: Last run date
   - recentchange:<date>, rc:<date>: Recently changed date
   
   Date formats: YYYY[-MM[-DD[Thh[:mm[:ss[.sss]]]]]] or today, yesterday, lastweek, etc.
   
   File Attributes and Types:
   - attrib:<attributes>, attributes:<attributes>: Search by file attributes (A:Archive, H:Hidden, S:System, etc.)
   - type:<type>: Search by file type
   - ext:<list>: Search by semicolon-separated extensions
   
   Path and Name:
   - path:<path>: Search in specific path
   - parent:<path>, infolder:<path>, nosubfolders:<path>: Search in path excluding subfolders
   - startwith:<text>: Files starting with text
   - endwith:<text>: Files ending with text
   - child:<filename>: Folders containing specific child
   - depth:<count>, parents:<count>: Files at specific folder depth
   - root: Files with no parent folder
   - shell:<name>: Search in known shell folders
   Duplicates and Lists:
   - dupe, namepartdupe, attribdupe, dadupe, dcdupe, dmdupe, sizedupe: Find duplicates
   - filelist:<list>: Search pipe-separated (|) file list
   - filelistfilename:<filename>: Search files from list file
   - frn:<frnlist>: Search by File Reference Numbers
   - fsi:<index>: Search by file system index
   - empty: Find empty folders
4. Function Syntax:
   - function:value: Equal to value
   - function:<=value: Less than or equal
   - function:<value: Less than
   - function:=value: Equal to
   - function:>value: Greater than
   - function:>=value: Greater than or equal
   - function:start..end: Range of values
   - function:start-end: Range of values
5. Modifiers:
   - case:, nocase:: Enable/disable case sensitivity
   - file:, folder:: Match only files or folders
   - path:, nopath:: Match full path or filename only
   - regex:, noregex:: Enable/disable regex
   - wfn:, nowfn:: Match whole filename or anywhere
   - wholeword:, ww:: Match whole words only
   - wildcards:, nowildcards:: Enable/disable wildcards
Examples:
1. Find Python files modified today:
   ext:py datemodified:today
2. Find large video files:
   ext:mp4|mkv|avi size:>1gb
3. Find files in specific folder:
   path:C:\Projects *.js
"""
        }

        description = f"""Universal file search tool for {platform.system()}

Current Implementation:
{platform_info.get(current_platform, "Unknown platform")}

Search Syntax Guide:
{syntax_docs.get(current_platform, "Platform-specific syntax guide not available")}
"""

        malicious_file_description = """查询恶意释放的文件并检查清理痕迹。

该工具读取从威胁情报分析中生成的CSV文件，其中包含释放文件的详细信息。
通过分层检查目录存在性来判断系统清理程度和风险等级。

CSV文件应该包含以下列：
- 查询目标: IP地址或域名
- 样本SHA256: 样本文件的SHA256哈希
- 环境: 文件释放的环境信息
- 文件名称: 释放文件的名称
- 文件类型: 文件的类型描述
- 文件路径: 文件的完整释放路径
- 文件SHA256: 释放文件的SHA256哈希

检查策略（分层判断清理程度）：
1. 第0层：检查文件是否存在 ⭐⭐⭐ 风险最高
2. 第1层：检查上一层目录是否存在 ⭐⭐ 风险中等（文件被删除，目录保留）
3. 第2层：检查上两层目录是否存在 ⭐ 风险较低（目录也被删除）

结果分类：
- 文件存在：恶意文件仍保留在系统中
- 上一层目录存在：文件已删除，但释放目录保留（可能被清理工具部分清理）
- 上两层目录存在：释放目录也被删除，但上层目录保留（清理相对彻底）
- 完全未找到：文件和所有相关目录均不存在（清理最彻底）
"""

        return [
            Tool(
                name="search",
                description=description,
                inputSchema=UnifiedSearchQuery.get_schema_for_platform()
            ),
            Tool(
                name="query_malicious_release_files",
                description=malicious_file_description,
                inputSchema=MaliciousFileQuery.model_json_schema()
            )
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> List[TextContent]:
        if name == "query_malicious_release_files":
            # 处理恶意文件查询工具
            try:
                csv_path = arguments.get("csv_file_path")
                max_search_depth = arguments.get("max_search_depth", 2)

                if not csv_path:
                    raise ValueError("csv_file_path 是必需的参数")

                result_text = query_malicious_files_from_csv(
                    csv_path=csv_path,
                    search_provider=search_provider,
                    max_search_depth=max_search_depth
                )

                return [TextContent(
                    type="text",
                    text=result_text
                )]
            except Exception as e:
                return [TextContent(
                    type="text",
                    text=f"恶意文件查询失败: {str(e)}"
                )]

        elif name == "search":
            # 处理标准搜索工具
            try:
                # 解析和验证输入
                base_params = {}
                windows_params = {}

                # 处理基础参数
                if 'base' in arguments:
                    if isinstance(arguments['base'], str):
                        try:
                            base_params = json.loads(arguments['base'])
                        except json.JSONDecodeError:
                            # 如果不是有效的 JSON 字符串，将其视为简单的查询字符串
                            base_params = {'query': arguments['base']}
                    elif isinstance(arguments['base'], dict):
                        # 如果已经是字典，直接使用
                        base_params = arguments['base']
                    else:
                        raise ValueError("'base' 参数必须是字符串或字典")

                # 处理 Windows 特定参数
                if 'windows_params' in arguments:
                    if isinstance(arguments['windows_params'], str):
                        try:
                            windows_params = json.loads(arguments['windows_params'])
                        except json.JSONDecodeError:
                            raise ValueError("windows_params 中的 JSON 无效")
                    elif isinstance(arguments['windows_params'], dict):
                        # 如果已经是字典，直接使用
                        windows_params = arguments['windows_params']
                    else:
                        raise ValueError("'windows_params' 必须是字符串或字典")

                # 组合参数
                query_params = {
                    **base_params,
                    'windows_params': windows_params
                }

                # 创建统一查询
                query = UnifiedSearchQuery(**query_params)

                if current_platform == "windows":
                    # 直接使用 Everything SDK
                    platform_params = query.windows_params or WindowsSpecificParams()
                    results = search_provider.search_files(
                        query=query.query,
                        max_results=query.max_results,
                        match_path=platform_params.match_path,
                        match_case=platform_params.match_case,
                        match_whole_word=platform_params.match_whole_word,
                        match_regex=platform_params.match_regex,
                        sort_by=platform_params.sort_by
                    )
                else:
                    # 使用命令行工具（mdfind/locate）
                    platform_params = None
                    if current_platform == 'darwin':
                        platform_params = query.mac_params or {}
                    elif current_platform == 'linux':
                        platform_params = query.linux_params or {}

                    results = search_provider.search_files(
                        query=query.query,
                        max_results=query.max_results,
                        **platform_params.dict() if platform_params else {}
                    )

                return [TextContent(
                    type="text",
                    text="\n".join([
                        f"Path: {r.path}\n"
                        f"Filename: {r.filename}"
                        f"{f' ({r.extension})' if r.extension else ''}\n"
                        f"Size: {r.size:,} bytes\n"
                        f"Created: {r.created if r.created else 'N/A'}\n"
                        f"Modified: {r.modified if r.modified else 'N/A'}\n"
                        f"Accessed: {r.accessed if r.accessed else 'N/A'}\n"
                        for r in results
                    ])
                )]
            except Exception as e:
                return [TextContent(
                    type="text",
                    text=f"搜索失败: {str(e)}"
                )]

        else:
            raise ValueError(f"未知工具: {name}")

    options = server.create_initialization_options()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, options, raise_exceptions=True)

def configure_windows_console():
    """配置 Windows 控制台以输出 UTF-8。"""
    import ctypes

    if sys.platform == "win32":
        # 启用虚拟终端处理
        kernel32 = ctypes.windll.kernel32
        STD_OUTPUT_HANDLE = -11
        ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004

        handle = kernel32.GetStdHandle(STD_OUTPUT_HANDLE)
        mode = ctypes.c_ulong()
        kernel32.GetConsoleMode(handle, ctypes.byref(mode))
        mode.value |= ENABLE_VIRTUAL_TERMINAL_PROCESSING
        kernel32.SetConsoleMode(handle, mode)

        # 为控制台输出设置 UTF-8 编码
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')

def main() -> None:
    """主入口点。"""
    import asyncio
    import logging
    logging.basicConfig(
        level=logging.WARNING,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    configure_windows_console()

    try:
        asyncio.run(serve())
    except KeyboardInterrupt:
        logging.info("服务器被用户停止")
        sys.exit(0)
    except Exception as e:
        logging.error(f"服务器错误: {e}", exc_info=True)
        sys.exit(1)
