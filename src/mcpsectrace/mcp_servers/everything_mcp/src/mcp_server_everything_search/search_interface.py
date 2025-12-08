"""MCP 的平台无关搜索接口。"""

import abc
import platform
import subprocess
import os
from datetime import datetime
from typing import Optional, List
from dataclasses import dataclass
from pathlib import Path


@dataclass
class SearchResult:
    """通用搜索结果结构。"""

    path: str
    filename: str
    extension: Optional[str] = None
    size: Optional[int] = None
    created: Optional[datetime] = None
    modified: Optional[datetime] = None
    accessed: Optional[datetime] = None
    attributes: Optional[str] = None


class SearchProvider(abc.ABC):
    """平台特定搜索实现的抽象基类。"""

    @abc.abstractmethod
    def search_files(
        self,
        query: str,
        max_results: int = 100,
        match_path: bool = False,
        match_case: bool = False,
        match_whole_word: bool = False,
        match_regex: bool = False,
        sort_by: Optional[int] = None,
    ) -> List[SearchResult]:
        """使用平台特定方法执行文件搜索。"""
        pass

    @classmethod
    def get_provider(cls) -> "SearchProvider":
        """工厂方法：获取当前平台的适当搜索提供者。"""
        system = platform.system().lower()
        if system == "darwin":
            return MacSearchProvider()
        elif system == "linux":
            return LinuxSearchProvider()
        elif system == "windows":
            return WindowsSearchProvider()
        else:
            raise NotImplementedError(f"没有可用的搜索提供者用于 {system}")

    def _convert_path_to_result(self, path: str) -> SearchResult:
        """将路径转换为带有文件信息的 SearchResult。"""
        try:
            path_obj = Path(path)
            stat = path_obj.stat()
            return SearchResult(
                path=str(path_obj),
                filename=path_obj.name,
                extension=path_obj.suffix[1:] if path_obj.suffix else None,
                size=stat.st_size,
                created=datetime.fromtimestamp(stat.st_ctime),
                modified=datetime.fromtimestamp(stat.st_mtime),
                accessed=datetime.fromtimestamp(stat.st_atime),
            )
        except (OSError, ValueError) as e:
            # 如果无法访问文件，返回基本信息
            return SearchResult(path=str(path), filename=os.path.basename(path))


class MacSearchProvider(SearchProvider):
    """使用 mdfind 的 macOS 搜索实现。"""

    def search_files(
        self,
        query: str,
        max_results: int = 100,
        match_path: bool = False,
        match_case: bool = False,
        match_whole_word: bool = False,
        match_regex: bool = False,
        sort_by: Optional[int] = None,
    ) -> List[SearchResult]:
        try:
            # 构建 mdfind 命令
            cmd = ["mdfind"]
            if match_path:
                # 匹配路径时，不使用 -name
                cmd.append(query)
            else:
                cmd.extend(["-name", query])

            # 执行搜索
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise RuntimeError(f"mdfind 失败: {result.stderr}")

            # 处理结果
            paths = result.stdout.splitlines()[:max_results]
            return [self._convert_path_to_result(path) for path in paths]

        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"搜索失败: {e}")


class LinuxSearchProvider(SearchProvider):
    """使用 locate/plocate 的 Linux 搜索实现。"""

    def __init__(self):
        """检查 locate/plocate 是否已安装且数据库是否就绪。"""
        self.locate_cmd = None
        self.locate_type = None

        # 首先检查 plocate（更新的版本）
        plocate_check = subprocess.run(["which", "plocate"], capture_output=True)
        if plocate_check.returncode == 0:
            self.locate_cmd = "plocate"
            self.locate_type = "plocate"
        else:
            # 检查 mlocate
            mlocate_check = subprocess.run(["which", "locate"], capture_output=True)
            if mlocate_check.returncode == 0:
                self.locate_cmd = "locate"
                self.locate_type = "mlocate"
            else:
                raise RuntimeError(
                    "Neither 'locate' nor 'plocate' is installed. Please install one:\n"
                    "Ubuntu/Debian: sudo apt-get install plocate\n"
                    "              or\n"
                    "              sudo apt-get install mlocate\n"
                    "Fedora: sudo dnf install mlocate\n"
                    "After installation, the database will be updated automatically, or run:\n"
                    "For plocate: sudo updatedb\n"
                    "For mlocate: sudo /etc/cron.daily/mlocate"
                )

    def _update_database(self):
        """更新 locate 数据库。"""
        if self.locate_type == "plocate":
            subprocess.run(["sudo", "updatedb"], check=True)
        else:  # mlocate
            subprocess.run(["sudo", "/etc/cron.daily/mlocate"], check=True)

    def search_files(
        self,
        query: str,
        max_results: int = 100,
        match_path: bool = False,
        match_case: bool = False,
        match_whole_word: bool = False,
        match_regex: bool = False,
        sort_by: Optional[int] = None,
    ) -> List[SearchResult]:
        try:
            # 构建 locate 命令
            cmd = [self.locate_cmd]
            if not match_case:
                cmd.append("-i")
            if match_regex:
                cmd.append("--regex" if self.locate_type == "mlocate" else "-r")
            cmd.append(query)

            # 执行搜索
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                error_msg = result.stderr.lower()
                if "no such file or directory" in error_msg or "database" in error_msg:
                    raise RuntimeError(
                        f"{self.locate_type} 数据库需要创建。" f"请运行: sudo updatedb"
                    )
                raise RuntimeError(f"{self.locate_cmd} 失败: {result.stderr}")

            # 处理结果
            paths = result.stdout.splitlines()[:max_results]
            return [self._convert_path_to_result(path) for path in paths]

        except FileNotFoundError:
            raise RuntimeError(
                f"{self.locate_cmd} 命令消失了。请重新安装:\n"
                "Ubuntu/Debian: sudo apt-get install plocate\n"
                "              或\n"
                "              sudo apt-get install mlocate\n"
                "Fedora: sudo dnf install mlocate"
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"搜索失败: {e}")


class WindowsSearchProvider(SearchProvider):
    """使用 Everything SDK 的 Windows 搜索实现。"""

    def __init__(self):
        """初始化 Everything SDK。"""
        import os
        from .everything_sdk import EverythingSDK

        dll_path = os.getenv(
            "EVERYTHING_SDK_PATH",
            "D:\\dev\\tools\\Everything-SDK\\dll\\Everything64.dll",
        )
        self.everything_sdk = EverythingSDK(dll_path)

    def search_files(
        self,
        query: str,
        max_results: int = 100,
        match_path: bool = False,
        match_case: bool = False,
        match_whole_word: bool = False,
        match_regex: bool = False,
        sort_by: Optional[int] = None,
    ) -> List[SearchResult]:
        # 将双反斜杠替换为单反斜杠
        query = query.replace("\\\\", "\\")
        # 如果查询包含正斜杠，将其替换为反斜杠
        query = query.replace("/", "\\")

        return self.everything_sdk.search_files(
            query=query,
            max_results=max_results,
            match_path=match_path,
            match_case=match_case,
            match_whole_word=match_whole_word,
            match_regex=match_regex,
            sort_by=sort_by,
        )
