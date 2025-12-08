import winreg
import os
import json
import shutil
import subprocess
import ctypes
import sys
from pathlib import Path

try:
    import tomlkit
except ImportError:
    tomlkit = None


def add_to_path_windows(new_path):
    """
    将指定路径添加到 Windows 用户环境变量的 PATH 中。

    Args:
        new_path: 要添加的路径字符串
    """
    # 1. 定义注册表路径 (当前用户的环境变量)
    key_path = r"Environment"

    try:
        # 2. 打开注册表键
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_ALL_ACCESS)

        try:
            # 3. 获取当前的 PATH 值
            current_path_value, _ = winreg.QueryValueEx(key, "Path")
        except FileNotFoundError:
            # 如果 Path 不存在，则初始化为空
            current_path_value = ""

        # 4. 检查路径是否已存在，避免重复添加
        if new_path.lower() in current_path_value.lower():
            print(f"路径已存在，无需添加: {new_path}")
        else:
            # 5. 拼接新路径 (注意 Windows 使用分号 ; 分隔)
            # 如果当前值不为空且末尾没有分号，加一个分号
            if current_path_value and not current_path_value.endswith(";"):
                new_path_value = current_path_value + ";" + new_path
            else:
                new_path_value = current_path_value + new_path

            # 6. 写入注册表
            winreg.SetValueEx(key, "Path", 0, winreg.REG_EXPAND_SZ, new_path_value)
            print(f"成功将路径添加到用户环境变量: {new_path}")
            print("注意：您可能需要注销或重启电脑才能使更改在所有程序中生效。")

            # (可选) 通知系统环境发生变化，让部分程序立即感知
            # ctypes.windll.user32.SendMessageTimeoutW(0xFFFF, 0x001A, 0, "Environment", 0, 5000, None)

        winreg.CloseKey(key)

    except Exception as e:
        print(f"发生错误: {e}")


def everything_search(dll_path: str, filename_with_suffix: str, search_type: str) -> list:
    """
    使用 Everything SDK 搜索文件并返回所有匹配项的完整路径列表。

    Args:
        dll_path: Everything64.dll 的路径
        filename_with_suffix: 要搜索的文件名（包含后缀）
        search_type: 搜索类型，'file' 或 'folder'

    Returns:
        匹配结果的完整路径列表
    """
    if search_type not in ('file', 'folder'):
        print(f"[ERROR] 无效的 search_type '{search_type}'。必须是 'file' 或 'folder'。")
        return []

    # Everything SDK 常量定义
    EVERYTHING_REQUEST_FILE_NAME = 0x00000001
    EVERYTHING_REQUEST_PATH = 0x00000002
    REQUEST_FLAGS = EVERYTHING_REQUEST_FILE_NAME | EVERYTHING_REQUEST_PATH

    try:
        everything_dll = ctypes.WinDLL(dll_path)

        # 设置函数参数和返回类型
        everything_dll.Everything_SetSearchW.argtypes = [ctypes.c_wchar_p]
        everything_dll.Everything_SetRequestFlags.argtypes = [ctypes.c_uint]
        everything_dll.Everything_QueryW.argtypes = [ctypes.c_bool]
        everything_dll.Everything_QueryW.restype = ctypes.c_bool
        everything_dll.Everything_GetNumResults.restype = ctypes.c_int
        everything_dll.Everything_GetResultFullPathNameW.argtypes = [ctypes.c_int, ctypes.c_wchar_p, ctypes.c_int]

    except OSError as e:
        print(f"[ERROR] 无法加载 Everything64.dll: {e}")
        return []
    except AttributeError as e:
        print(f"[ERROR] DLL 中缺少必要的函数: {e}")
        return []

    try:
        # 1. 设置搜索词（处理空格）
        search_query = f'"{filename_with_suffix}"' if ' ' in filename_with_suffix else filename_with_suffix
        search_query = search_type + ': wfn:' + search_query
        everything_dll.Everything_SetSearchW(search_query)

        # 2. 设置请求标志
        everything_dll.Everything_SetRequestFlags(REQUEST_FLAGS)

        # 3. 执行查询
        if not everything_dll.Everything_QueryW(True):
            print("[ERROR] Everything 查询执行失败，请确保 Everything 服务已启动")
            return []

        # 4. 获取结果数量
        num_results = everything_dll.Everything_GetNumResults()

        if num_results == 0:
            return []

        # 5. 遍历所有结果
        results_list = []
        path_buffer = ctypes.create_unicode_buffer(260)

        for i in range(num_results):
            everything_dll.Everything_GetResultFullPathNameW(i, path_buffer, 260)
            results_list.append(ctypes.wstring_at(path_buffer))

        return results_list

    except Exception as e:
        print(f"[ERROR] 搜索过程中发生异常: {e}")
        return []


def _filter_search_results(results: list, path_patterns: list) -> str | None:
    """
    根据配置的路径模式过滤搜索结果

    Args:
        results: Everything 搜索返回的所有结果
        path_patterns: 路径必须匹配的模式列表（支持多个，OR关系）
                      如果为空列表，则返回第一个结果

    Returns:
        过滤后选中的最佳结果，如果未找到则返回 None
    """
    if not results:
        return None

    # 如果没有指定路径模式，直接返回第一个结果
    if not path_patterns:
        return results[0]

    # 逐个检查路径模式（OR关系）
    for pattern in path_patterns:
        pattern_lower = pattern.lower()
        for result in results:
            if pattern_lower in result.lower():
                return result

    # 所有模式都匹配失败时返回 None
    return None


def configure_tool_paths(mcp_sectrace_dir):
    """
    配置工具路径：
    使用 Everything 工具自动搜索并填写 user_settings.toml 中的工具路径
    从 [tools.entries] 配置中读取要搜索的工具列表
    """
    print("[Step 5] 配置工具路径...")

    try:
        # 检查 tomlkit 是否可用
        if tomlkit is None:
            print("[WARN] tomlkit 库未安装，跳过工具路径配置")
            print("[INFO] 可以手动编辑 config/user_settings.toml 配置工具路径")
            return True

        # 获取 Everything DLL 路径
        everything_dll_path = "D:/Everything/Everything-SDK/dll/Everything64.dll"

        if not Path(everything_dll_path).exists():
            print(f"[WARN] Everything SDK 未找到: {everything_dll_path}")
            print("[INFO] 可以手动编辑 config/user_settings.toml 配置工具路径")
            return True

        # 获取 user_settings.toml 路径
        toml_path = mcp_sectrace_dir / "config" / "user_settings.toml"

        if not toml_path.exists():
            print(f"[ERROR] user_settings.toml 不存在: {toml_path}")
            return False

        # 读取配置文件，获取工具列表
        try:
            with open(toml_path, 'r', encoding='utf-8') as f:
                content = f.read()
            doc = tomlkit.parse(content)
        except Exception as e:
            print(f"[ERROR] 读取 user_settings.toml 失败: {e}")
            return False

        # 从配置中提取工具定义
        if 'tools' not in doc or 'entries' not in doc['tools']:
            print("[WARN] 未找到 [tools.entries] 配置，跳过工具路径配置")
            return True

        tool_entries = doc['tools']['entries']
        if not tool_entries:
            print("[WARN] [tools.entries] 为空，跳过工具路径配置")
            return True

        print(f"开始搜索工具文件，这可能需要几秒钟...")

        # 搜索工具并收集结果
        update_dict = {}
        found_count = 0

        for entry in tool_entries:
            config_key = entry.get('config_key')
            filename = entry.get('filename')
            search_type = entry.get('type', 'file')
            path_patterns = entry.get('path_patterns', [])

            if not config_key or not filename:
                print(f"  [SKIP] 工具配置不完整: {entry}")
                continue

            print(f"  搜索 {filename}...", end='', flush=True)
            results = everything_search(everything_dll_path, filename, search_type)

            if results:
                # 根据配置的路径模式过滤结果
                tool_path = _filter_search_results(results, path_patterns)
                if tool_path:
                    update_dict[f'paths.{config_key}'] = tool_path
                    found_count += 1
                    print(f" [OK] 找到")
                else:
                    print(f" [SKIP] 找到文件但不符合路径要求")
            else:
                print(f" [NOT FOUND] 未找到")

        # 更新 TOML 文件
        if update_dict:
            try:
                for key_path, value in update_dict.items():
                    keys = key_path.split('.')
                    d = doc
                    for k in keys[:-1]:
                        if k not in d or not isinstance(d[k], (tomlkit.items.Table, dict)):
                            d[k] = tomlkit.table()
                        d = d[k]
                    d[keys[-1]] = value

                with open(toml_path, 'w', encoding='utf-8') as f:
                    f.write(tomlkit.dumps(doc))

                print(f"[SUCCESS] 工具路径配置完成，共更新 {found_count} 个路径。")
                return True

            except Exception as e:
                print(f"[ERROR] 更新 user_settings.toml 失败: {e}")
                return False
        else:
            print("[WARN] 未找到任何符合条件的工具，请手动编辑 config/user_settings.toml 配置工具路径")
            return True

    except Exception as e:
        print(f"[ERROR] 配置工具路径失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def configure_workflow(mcp_sectrace_dir):
    """
    配置溯源工作流：
    将 assets/workflow 目录下的所有 markdown 文件
    复制到 C:/Users/{username}/Documents/Cline/Workflows/ 目录下
    """
    print("[Step 4] 配置溯源工作流...")

    try:
        # 获取源目录路径
        source_dir = mcp_sectrace_dir / "assets" / "workflow"

        if not source_dir.exists():
            print(f"[ERROR] workflow 目录不存在: {source_dir}")
            return False

        # 获取目标目录路径
        username = os.getenv("USERNAME")
        target_dir = Path(f"C:\\Users\\{username}\\Documents\\Cline\\Workflows")

        # 如果目标目录不存在则创建
        if not target_dir.exists():
            print(f"创建目标目录: {target_dir}")
            target_dir.mkdir(parents=True, exist_ok=True)

        # 查找所有 markdown 文件
        md_files = list(source_dir.glob("*.md"))
        if not md_files:
            print(f"[WARN] 未找到任何 markdown 文件在: {source_dir}")
            return True

        print(f"找到 {len(md_files)} 个 markdown 文件，开始复制...")

        # 复制每个 markdown 文件
        for md_file in md_files:
            target_file = target_dir / md_file.name
            print(f"复制: {md_file.name} -> {target_dir.name}/")
            shutil.copy2(md_file, target_file)

        print(f"[SUCCESS] 溯源工作流配置已完成，共复制 {len(md_files)} 个文件。")
        return True

    except Exception as e:
        print(f"[ERROR] 配置溯源工作流失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def configure_mcp_tools(mcp_sectrace_dir):
    """
    配置 MCPTools：
    将 mcpsetting.json 复制到 Cline 的配置目录，
    命名为 cline_mcp_settings.json（覆盖现有文件）
    """
    print("[Step 3] 配置 MCPTools...")

    try:
        # 获取源文件路径
        source_file = mcp_sectrace_dir / "assets" / "mcpsetting.json"

        if not source_file.exists():
            print(f"[ERROR] mcpsetting.json 文件不存在: {source_file}")
            return False

        # 获取目标目录和文件路径
        username = os.getenv("USERNAME")
        target_dir = Path(
            f"C:\\Users\\{username}\\AppData\\Roaming\\Code\\User\\globalStorage\\saoudrizwan.claude-dev\\settings"
        )
        target_file = target_dir / "cline_mcp_settings.json"

        # 如果目标目录不存在，则创建它
        if not target_dir.exists():
            print(f"[INFO] 目标目录不存在，创建目录: {target_dir}")
            target_dir.mkdir(parents=True, exist_ok=True)
            print(f"[SUCCESS] 目录创建完成。")

        # 复制文件（覆盖现有文件）
        print(f"复制: {source_file}")
        print(f"到: {target_file}")
        shutil.copy2(source_file, target_file)
        print(f"[SUCCESS] MCPTools 配置已完成。")
        return True

    except Exception as e:
        print(f"[ERROR] 配置 MCPTools 失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def configure_vscode_extensions(mcp_sectrace_dir):
    """
    配置 VSCode 插件：
    1. 将 Cline 插件配置添加到 extensions.json
    2. 复制 claude-dev 插件文件夹到 extensions 目录
    """
    print("[Step 2] 配置 VSCode 插件...")

    try:
        # 获取当前用户路径
        username = os.getenv("USERNAME")
        vscode_extensions_dir = Path(f"C:\\Users\\{username}\\.vscode\\extensions")
        extensions_json_path = vscode_extensions_dir / "extensions.json"

        # 如果 extensions 目录不存在，创建它
        if not vscode_extensions_dir.exists():
            print(f"[INFO] VSCode extensions 目录不存在，创建目录: {vscode_extensions_dir}")
            vscode_extensions_dir.mkdir(parents=True, exist_ok=True)

        # 如果 extensions.json 不存在，创建空的配置文件
        if not extensions_json_path.exists():
            print(f"[INFO] extensions.json 不存在，创建空配置: {extensions_json_path}")
            extensions_data = []
            with open(extensions_json_path, "w", encoding="utf-8") as f:
                json.dump(extensions_data, f, indent=4, ensure_ascii=False)
        else:
            # 1. 读取 extensions.json
            print(f"读取 extensions.json: {extensions_json_path}")
            with open(extensions_json_path, "r", encoding="utf-8") as f:
                extensions_data = json.load(f)

        # 2. 读取 clinesetting.json
        cline_setting_path = mcp_sectrace_dir / "assets" / "clinesetting.json"

        if not cline_setting_path.exists():
            print(f"[ERROR] clinesetting.json 文件不存在: {cline_setting_path}")
            return False

        with open(cline_setting_path, "r", encoding="utf-8") as f:
            cline_config = json.load(f)

        # 3. 检查是否已存在相同的插件（根据 identifier.id）
        cline_id = cline_config["identifier"]["id"]
        extension_exists = any(
            ext.get("identifier", {}).get("id") == cline_id
            for ext in extensions_data
        )

        if extension_exists:
            print(f"[INFO] 插件'{cline_id}'已存在，无需添加。")
        else:
            # 4. 添加新配置到 extensions.json
            extensions_data.append(cline_config)
            with open(extensions_json_path, "w", encoding="utf-8") as f:
                json.dump(extensions_data, f, indent=4, ensure_ascii=False)
            print(f"[SUCCESS] 已将'{cline_id}'添加到 extensions.json。")

        # 5. 复制 claude-dev 插件文件夹
        print("\n复制 claude-dev 插件文件夹...")
        source_dir = mcp_sectrace_dir / "assets" / "saoudrizwan.claude-dev-3.38.2"
        target_dir = vscode_extensions_dir / "saoudrizwan.claude-dev-3.38.2"

        if not source_dir.exists():
            print(f"[ERROR] 源目录不存在: {source_dir}")
            return False

        if target_dir.exists():
            print(f"[INFO] 目标目录已存在: {target_dir}，跳过复制。")
        else:
            print(f"复制: {source_dir} -> {target_dir}")
            shutil.copytree(source_dir, target_dir)
            print(f"[SUCCESS] claude-dev 插件已复制完成。")

        print("[SUCCESS] VSCode 插件配置完成。")
        return True

    except Exception as e:
        print(f"[ERROR] 配置 VSCode 插件失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def get_mcp_sectrace_dir():
    """
    获取 MCPSecTrace 项目目录。
    支持从 py 文件和 exe 文件运行。
    """
    # 首先尝试从脚本文件所在目录
    script_dir = Path(__file__).parent
    if (script_dir / "assets").exists():
        return script_dir

    # 如果不存在，尝试从当前工作目录
    cwd = Path.cwd()
    if (cwd / "assets").exists():
        return cwd

    # 尝试从环境变量获取
    env_path = os.getenv("MCPSECTRACE_PATH")
    if env_path:
        project_path = Path(env_path)
        if project_path.exists() and (project_path / "assets").exists():
            return project_path

    # 最后尝试常见的默认路径
    common_paths = [
        Path("D:\\MCPSecTrace"),
        Path("D:\\MCPSecTrace"),
        Path.home() / "MCPSecTrace",
        Path("C:\\MCPSecTrace"),
    ]

    for potential_path in common_paths:
        if potential_path.exists() and (potential_path / "assets").exists():
            return potential_path

    # 如果都找不到，返回错误信息
    print("[ERROR] 无法自动定位 MCPSecTrace 项目目录")
    print("\n解决方案：")
    print("1. 运行本 exe 时，请在 MCPSecTrace 项目目录下运行")
    print("2. 或者设置环境变量: set MCPSECTRACE_PATH=D:\\MCPSecTrace")
    print("3. 或者将本 exe 放在 MCPSecTrace 目录下运行")
    return None


def configure_uv_environment():
    """
    配置 MCPTools/uv 环境：
    1. 将 MCPTools/uv 路径添加到系统环境变量的 PATH 中
    2. 验证 uv 安装
    3. 运行 uv sync 同步依赖
    """
    print("[Step 1] 配置 MCPTools/uv 路径...")
    try:
        # 获取 MCPSecTrace 的父目录
        mcp_sectrace_dir = get_mcp_sectrace_dir()
        if mcp_sectrace_dir is None:
            return False

        mcp_tools_uv_path = mcp_sectrace_dir.parent / "MCPTools" / "uv"

        # 验证路径是否存在
        if not mcp_tools_uv_path.exists():
            print(f"[ERROR] MCPTools/uv 路径不存在: {mcp_tools_uv_path}")
            return False

        mcp_tools_uv_str = str(mcp_tools_uv_path)
        print(f"准备添加路径: {mcp_tools_uv_str}")
        add_to_path_windows(mcp_tools_uv_str)
        print("[SUCCESS] MCPTools/uv 路径配置完成。")

        # 验证 uv 安装
        print("\n验证 uv 安装...")
        try:
            result = subprocess.run(
                ["uv", "--help"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                print("[SUCCESS] uv 已成功安装并可用。")
            else:
                print(f"[ERROR] uv 命令执行失败，返回码: {result.returncode}")
                print(f"错误信息: {result.stderr}")
                return False
        except FileNotFoundError:
            print("[ERROR] 未找到 uv 命令。请确保已正确添加路径并重启终端。")
            return False
        except subprocess.TimeoutExpired:
            print("[ERROR] uv 命令执行超时。")
            return False

        # 运行 uv sync 同步依赖
        print("\n正在同步项目依赖 (uv sync)，这可能需要几分钟...")
        try:
            result = subprocess.run(
                ["uv", "sync"],
                cwd=str(mcp_sectrace_dir),
                capture_output=True,
                text=True,
                timeout=600  # 10分钟超时
            )
            if result.returncode == 0:
                print("[SUCCESS] 项目依赖同步完成。")
                return True
            else:
                print(f"[ERROR] uv sync 执行失败，返回码: {result.returncode}")
                print(f"错误信息: {result.stderr}")
                return False
        except FileNotFoundError:
            print("[ERROR] 未找到 uv 命令。请确保已正确添加路径并重启终端。")
            return False
        except subprocess.TimeoutExpired:
            print("[ERROR] uv sync 执行超时（10分钟），请手动运行 'uv sync'。")
            return False

    except Exception as e:
        print(f"[ERROR] 配置 MCPTools/uv 环境失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def initialize_environment():
    """
    初始化项目环境配置，执行所有初始化步骤。
    """
    print("开始初始化环境配置...")
    print("-" * 50)

    # 获取 MCPSecTrace 项目目录
    mcp_sectrace_dir = get_mcp_sectrace_dir()
    if mcp_sectrace_dir is None:
        return False

    print(f"[INFO] 项目目录: {mcp_sectrace_dir}\n")

    # Step 1: 配置 uv 环境
    if not configure_uv_environment():
        return False

    print()

    # Step 2: 配置 VSCode 插件
    if not configure_vscode_extensions(mcp_sectrace_dir):
        return False

    print()

    # Step 3: 配置 MCPTools
    if not configure_mcp_tools(mcp_sectrace_dir):
        return False

    print()

    # Step 4: 配置溯源工作流
    if not configure_workflow(mcp_sectrace_dir):
        return False

    print()

    # Step 5: 配置工具路径
    if not configure_tool_paths(mcp_sectrace_dir):
        return False

    print("-" * 50)
    print("环境配置初始化完成！")
    return True


def wait_for_user():
    """
    等待用户按任意键。
    用于 exe 执行时保持窗口打开，让用户看到完整的输出结果。
    """
    print("\n" + "=" * 50)
    print("按任意键关闭窗口...")
    print("=" * 50)
    try:
        # Windows 系统上使用 msvcrt
        import msvcrt
        msvcrt.getch()
    except ImportError:
        # Linux/Mac 系统上使用 input
        input()


def main():
    """
    主函数，执行项目初始化。
    """
    try:
        success = initialize_environment()
        if success:
            wait_for_user()
    except Exception as e:
        print(f"\n[FATAL ERROR] 初始化过程中发生异常: {e}")
        import traceback
        traceback.print_exc()
        wait_for_user()


if __name__ == "__main__":
    main()
