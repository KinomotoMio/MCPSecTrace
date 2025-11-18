"""跨平台文件搜索的 MCP 服务器实现。"""

import json
import platform
import sys
from typing import List
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

        return [
            Tool(
                name="search",
                description=description,
                inputSchema=UnifiedSearchQuery.get_schema_for_platform()
            )
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> List[TextContent]:
        if name != "search":
            raise ValueError(f"未知工具: {name}")

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
