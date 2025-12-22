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

            # 7. 更新当前进程的 PATH 环境变量（让后续子进程能立即使用）
            current_process_path = os.environ.get("PATH", "")
            if new_path.lower() not in current_process_path.lower():
                os.environ["PATH"] = new_path + ";" + current_process_path
                print(f"已更新当前进程的 PATH 环境变量")

            # 8. 广播 WM_SETTINGCHANGE 消息，通知其他程序环境变量已更改
            try:
                HWND_BROADCAST = 0xFFFF
                WM_SETTINGCHANGE = 0x001A
                SMTO_ABORTIFHUNG = 0x0002

                # 设置函数参数类型，确保正确传递参数
                SendMessageTimeoutW = ctypes.windll.user32.SendMessageTimeoutW
                SendMessageTimeoutW.argtypes = [
                    ctypes.c_void_p,  # hWnd
                    ctypes.c_uint,    # Msg
                    ctypes.c_void_p,  # wParam
                    ctypes.c_wchar_p, # lParam (字符串指针)
                    ctypes.c_uint,    # fuFlags
                    ctypes.c_uint,    # uTimeout
                    ctypes.POINTER(ctypes.c_ulong)  # lpdwResult
                ]
                SendMessageTimeoutW.restype = ctypes.c_long

                # 用于接收返回结果
                result_value = ctypes.c_ulong()

                result = SendMessageTimeoutW(
                    HWND_BROADCAST,
                    WM_SETTINGCHANGE,
                    0,
                    "Environment",
                    SMTO_ABORTIFHUNG,
                    5000,
                    ctypes.byref(result_value)
                )
                if result:
                    print(f"已通知系统环境变量更改，新开的终端窗口将立即生效")
                else:
                    print(f"[WARN] 广播消息返回失败，错误码: {ctypes.get_last_error()}")
            except Exception as e:
                print(f"[WARN] 广播环境变量更改通知失败: {e}")
                print("[INFO] 新开的终端窗口可能需要重启后才能使用新路径")

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
    1. 从配置文件读取 Everything 根目录
    2. 启动 Everything 服务
    3. 使用 Everything SDK 自动搜索并填写 user_settings.toml 中的工具路径
    """
    print("[Step 7] 配置工具路径...")

    try:
        # 检查 tomlkit 是否可用
        if tomlkit is None:
            print("[WARN] tomlkit 库未安装，跳过工具路径配置")
            print("[INFO] 可以手动编辑 config/user_settings.toml 配置工具路径")
            return True

        # 获取 user_settings.toml 路径
        toml_path = mcp_sectrace_dir / "config" / "user_settings.toml"

        if not toml_path.exists():
            print(f"[ERROR] user_settings.toml 不存在: {toml_path}")
            return False

        # 读取配置文件
        try:
            with open(toml_path, 'r', encoding='utf-8') as f:
                content = f.read()
            doc = tomlkit.parse(content)
        except Exception as e:
            print(f"[ERROR] 读取 user_settings.toml 失败: {e}")
            return False

        # 从配置文件获取 Everything 根目录（类似 get_config_value 的方式）
        try:
            everything_root = doc['paths']['everything_root']
            print(f"从配置读取 Everything 根目录: {everything_root}")
        except (KeyError, TypeError):
            print("[WARN] 配置文件中未找到 paths.everything_root，使用默认路径")
            everything_root = "D:/MCPTools/Everything"

        everything_root_path = Path(everything_root)

        # 构建 Everything.exe 和 DLL 路径
        everything_exe = everything_root_path / "Everything.exe"
        everything_dll_path = everything_root_path / "Everything-SDK" / "dll" / "Everything64.dll"

        # 启动 Everything 服务（以管理员身份）
        print(f"\n启动 Everything 服务...")
        if everything_exe.exists():
            try:
                # 使用 ShellExecute 以管理员身份启动
                import ctypes
                import time

                # 参数说明：
                # "runas" - 以管理员身份运行
                # SW_HIDE (0) - 隐藏窗口
                result = ctypes.windll.shell32.ShellExecuteW(
                    None,                      # hwnd
                    "runas",                   # lpOperation (以管理员身份)
                    str(everything_exe),       # lpFile
                    "",                        # lpParameters
                    str(everything_root_path), # lpDirectory
                    0                          # nShowCmd (0=SW_HIDE 隐藏窗口)
                )

                if result > 32:  # ShellExecute 成功返回值 > 32
                    print(f"[SUCCESS] Everything 服务已启动: {everything_exe}")
                    # 等待服务启动完成
                    time.sleep(2)
                else:
                    print(f"[WARN] 启动 Everything 失败，返回码: {result}")
                    print("[INFO] 如果 Everything 已在运行，可以忽略此警告")

            except Exception as e:
                print(f"[WARN] 启动 Everything 失败: {e}")
                print("[INFO] 如果 Everything 已在运行，可以忽略此警告")
        else:
            print(f"[WARN] Everything.exe 未找到: {everything_exe}")

        # 检查 DLL 是否存在
        if not everything_dll_path.exists():
            print(f"[WARN] Everything SDK 未找到: {everything_dll_path}")
            print("[INFO] 可以手动编辑 config/user_settings.toml 配置工具路径")
            return True

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
            results = everything_search(str(everything_dll_path), filename, search_type)

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

                # 替换配置中的 {username} 占位符
                username = os.getenv("USERNAME")
                if username and 'paths' in doc:
                    for key, value in doc['paths'].items():
                        if isinstance(value, str) and '{username}' in value:
                            doc['paths'][key] = value.replace('{username}', username)
                            print(f"  [INFO] 已替换 {key} 中的 {{username}} 为 {username}")

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


def configure_paddlex_models(mcp_sectrace_dir):
    """
    配置 PaddleX 模型文件：
    将 MCPTools/official_models 目录复制到 C:/Users/{username}/.paddlex 路径下
    """
    print("[Step 6] 配置 PaddleX 模型文件...")

    try:
        # 获取当前用户名
        username = os.getenv("USERNAME")
        if not username:
            print("[ERROR] 无法获取当前用户名")
            return False

        # 源目录：MCPTools/official_models
        source_dir = mcp_sectrace_dir.parent / "MCPTools" / "official_models"

        # 目标目录：C:/Users/{username}/.paddlex
        target_dir = Path(f"C:/Users/{username}/.paddlex")

        # 检查源目录是否存在
        if not source_dir.exists():
            print(f"[ERROR] 源目录不存在: {source_dir}")
            print("[INFO] 请确保 MCPTools/official_models 目录存在")
            return False

        # 检查源目录是否为空
        if not any(source_dir.iterdir()):
            print(f"[WARN] 源目录为空: {source_dir}")
            print("[INFO] 跳过模型文件复制")
            return True

        # 如果目标目录不存在，创建它
        if not target_dir.exists():
            print(f"创建目标目录: {target_dir}")
            target_dir.mkdir(parents=True, exist_ok=True)

        # 复制 official_models 文件夹
        target_models_dir = target_dir / "official_models"

        if target_models_dir.exists():
            print(f"[INFO] 目标目录已存在: {target_models_dir}")
            print("[INFO] 跳过复制，保留现有文件")
        else:
            print(f"复制模型文件...")
            print(f"  源: {source_dir}")
            print(f"  目标: {target_models_dir}")
            shutil.copytree(source_dir, target_models_dir)
            print(f"[SUCCESS] 模型文件已复制完成")

        print("[SUCCESS] PaddleX 模型配置完成")
        return True

    except Exception as e:
        print(f"[ERROR] 配置 PaddleX 模型失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def configure_browser_login(mcp_sectrace_dir):
    """
    配置浏览器并引导用户登录微步：
    1. 从 user_settings.toml 读取 Chrome 浏览器路径
    2. 打开浏览器访问 x.threatbook.com
    3. 提示用户登录微步网站
    """
    print("[Step 5] 配置浏览器并引导微步登录...")

    try:
        # 检查 tomlkit 是否可用
        if tomlkit is None:
            print("[WARN] tomlkit 库未安装，跳过浏览器配置")
            print("[INFO] 请手动编辑 config/user_settings.toml 配置 Chrome 路径后，访问 https://x.threatbook.com 登录")
            return True

        # 获取 user_settings.toml 路径
        toml_path = mcp_sectrace_dir / "config" / "user_settings.toml"

        if not toml_path.exists():
            print(f"[ERROR] user_settings.toml 不存在: {toml_path}")
            return False

        # 读取配置文件
        try:
            with open(toml_path, 'r', encoding='utf-8') as f:
                content = f.read()
            doc = tomlkit.parse(content)
        except Exception as e:
            print(f"[ERROR] 读取 user_settings.toml 失败: {e}")
            return False

        # 从配置文件获取 Chrome 浏览器路径
        chrome_path = None
        try:
            chrome_path = doc['paths']['chrome_exe']
            print(f"从配置读取 Chrome 路径: {chrome_path}")
        except (KeyError, TypeError):
            print("[WARN] 配置文件中未找到 paths.chrome_exe")
            print("[INFO] 请先配置 Chrome 浏览器路径，然后手动访问 https://x.threatbook.com 登录")
            return True

        # 检查 Chrome 路径是否存在
        if not chrome_path or not Path(chrome_path).exists():
            print(f"[WARN] Chrome 浏览器未找到: {chrome_path}")
            print("[INFO] 请在 user_settings.toml 中配置正确的 Chrome 路径，然后手动访问 https://x.threatbook.com 登录")
            return True

        # 微步登录网址
        threatbook_url = "https://x.threatbook.com"

        # 打开浏览器
        try:
            print(f"\n正在打开 Chrome 浏览器访问微步...")
            subprocess.Popen([chrome_path, threatbook_url])
            print(f"[SUCCESS] 已打开浏览器: {threatbook_url}")

            # 提示用户登录
            print("\n" + "=" * 60)
            print("[重要提示]")
            print("=" * 60)
            print("1. 浏览器已打开微步在线网站 (x.threatbook.com)")
            print("2. 请在浏览器中完成登录操作")
            print("3. IOC_MCP 服务器需要使用已登录的浏览器会话")
            print("4. 登录完成后，请按任意键继续...")
            print("=" * 60)

            # 等待用户确认登录完成
            try:
                import msvcrt
                msvcrt.getch()
            except ImportError:
                input()

            print("[SUCCESS] 浏览器配置完成。")
            return True

        except Exception as e:
            print(f"[ERROR] 打开浏览器失败: {e}")
            print(f"[INFO] 请手动访问 {threatbook_url} 并登录")
            return True  # 不阻止后续步骤

    except Exception as e:
        print(f"[ERROR] 配置浏览器失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def configure_workflow(mcp_sectrace_dir):
    """
    配置溯源工作流：
    1. 将 assets/workflow 目录下的所有 markdown 文件复制到 .clinerules/workflows/ 目录
    2. 将 assets/rule.md 复制到 .clinerules/ 目录
    """
    print("[Step 4] 配置溯源工作流...")

    try:
        # 1. 复制 workflow 文件夹下的所有 markdown 文件
        source_workflow_dir = mcp_sectrace_dir / "assets" / "workflow"

        if not source_workflow_dir.exists():
            print(f"[ERROR] workflow 目录不存在: {source_workflow_dir}")
            return False

        # 获取目标目录路径 (.clinerules/workflows/)
        target_workflow_dir = mcp_sectrace_dir / ".clinerules" / "workflows"

        # 如果目标目录不存在则创建
        if not target_workflow_dir.exists():
            print(f"创建目标目录: {target_workflow_dir}")
            target_workflow_dir.mkdir(parents=True, exist_ok=True)

        # 查找所有 markdown 文件
        md_files = list(source_workflow_dir.glob("*.md"))
        if not md_files:
            print(f"[WARN] 未找到任何 markdown 文件在: {source_workflow_dir}")
        else:
            print(f"找到 {len(md_files)} 个 workflow 文件，开始复制...")

            # 复制每个 markdown 文件
            for md_file in md_files:
                target_file = target_workflow_dir / md_file.name
                print(f"  复制: {md_file.name} -> .clinerules/workflows/")
                shutil.copy2(md_file, target_file)

            print(f"[SUCCESS] workflow 文件复制完成，共 {len(md_files)} 个文件。")

        # 2. 复制 rule.md 文件到 .clinerules/ 目录
        source_rule_file = mcp_sectrace_dir / "assets" / "rule.md"
        target_clinerules_dir = mcp_sectrace_dir / ".clinerules"

        # 确保 .clinerules 目录存在
        if not target_clinerules_dir.exists():
            print(f"创建目标目录: {target_clinerules_dir}")
            target_clinerules_dir.mkdir(parents=True, exist_ok=True)

        if source_rule_file.exists():
            target_rule_file = target_clinerules_dir / "rule.md"
            print(f"  复制: rule.md -> .clinerules/")
            shutil.copy2(source_rule_file, target_rule_file)
            print(f"[SUCCESS] rule.md 文件复制完成。")
        else:
            print(f"[WARN] rule.md 文件不存在: {source_rule_file}")

        print(f"[SUCCESS] 溯源工作流配置已完成。")
        return True

    except Exception as e:
        print(f"[ERROR] 配置溯源工作流失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def configure_mcp_tools(mcp_sectrace_dir):
    """
    配置 MCPTools：
    1. 将 mcpsetting.json 复制到 Cline 的配置目录
    2. 启动并关闭 VSCode 以初始化配置
    3. 修改 state.vscdb 中的 Cline 配置
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
        print(f"[SUCCESS] MCP 配置文件复制完成。")

        # 启动 VSCode 以初始化配置（以管理员身份）
        print("\n初始化 VSCode 配置...")
        vscode_exe = mcp_sectrace_dir.parent / "MCPTools" / "VSCode" / "Code.exe"

        if not vscode_exe.exists():
            print(f"[WARN] VSCode 未找到: {vscode_exe}")
            print("[INFO] 跳过 VSCode 初始化，请手动启动一次 VSCode")
        else:
            try:
                import time

                print(f"启动 VSCode: {vscode_exe}")
                # 使用 Popen 启动 VSCode，这样可以获取进程对象
                vscode_process = subprocess.Popen(
                    [str(vscode_exe)],
                    cwd=str(vscode_exe.parent),
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )

                print("[SUCCESS] VSCode 已启动")
                # 等待 VSCode 初始化
                print("等待 VSCode 初始化 (5秒)...")
                time.sleep(5)

                # 使用 terminate() 温和地关闭 VSCode
                print("关闭 VSCode...")
                vscode_process.terminate()

                # 等待进程退出，最多等待 5 秒
                try:
                    vscode_process.wait(timeout=5)
                    print("[SUCCESS] VSCode 已关闭")
                except subprocess.TimeoutExpired:
                    # 如果超时，强制杀掉
                    print("[INFO] VSCode 未响应，强制关闭...")
                    vscode_process.kill()
                    vscode_process.wait()
                    print("[SUCCESS] VSCode 已强制关闭")

                # 额外等待确保完全退出
                time.sleep(2)

            except Exception as e:
                print(f"[WARN] VSCode 初始化失败: {e}")
                print("[INFO] 请手动启动一次 VSCode 后再运行初始化")

        # 修改 state.vscdb 中的 Cline 配置
        print("\n配置 Cline 插件设置...")
        state_vscdb_path = Path(
            f"C:\\Users\\{username}\\AppData\\Roaming\\Code\\User\\globalStorage\\state.vscdb"
        )
        cline_sqlite_file = mcp_sectrace_dir / "assets" / "clinesqlite.txt"

        if not state_vscdb_path.exists():
            print(f"[WARN] state.vscdb 不存在: {state_vscdb_path}")
            print("[INFO] 请先启动一次 VSCode 以创建配置文件")
        elif not cline_sqlite_file.exists():
            print(f"[WARN] clinesqlite.txt 不存在: {cline_sqlite_file}")
        else:
            try:
                import sqlite3

                # 读取要写入的值
                with open(cline_sqlite_file, 'r', encoding='utf-8') as f:
                    cline_value = f.read().strip()

                # 连接 SQLite 数据库
                conn = sqlite3.connect(str(state_vscdb_path))
                cursor = conn.cursor()

                # 检查键是否存在
                cursor.execute(
                    "SELECT value FROM ItemTable WHERE key = ?",
                    ("saoudrizwan.claude-dev",)
                )
                existing = cursor.fetchone()

                if existing:
                    # 更新现有记录
                    cursor.execute(
                        "UPDATE ItemTable SET value = ? WHERE key = ?",
                        (cline_value, "saoudrizwan.claude-dev")
                    )
                    print("[SUCCESS] 已更新 Cline 配置")
                else:
                    # 插入新记录
                    cursor.execute(
                        "INSERT INTO ItemTable (key, value) VALUES (?, ?)",
                        ("saoudrizwan.claude-dev", cline_value)
                    )
                    print("[SUCCESS] 已插入 Cline 配置")

                conn.commit()
                conn.close()

            except Exception as e:
                print(f"[WARN] 修改 state.vscdb 失败: {e}")
                print("[INFO] Cline 配置将在首次使用时自动创建")

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

        # 3. 替换 location.path 中的 {username} 占位符
        if "location" in cline_config and "path" in cline_config["location"]:
            original_path = cline_config["location"]["path"]
            if "{username}" in original_path:
                cline_config["location"]["path"] = original_path.replace("{username}", username)
                print(f"  [INFO] 替换路径中的 {{username}} 为 {username}")
                print(f"    原路径: {original_path}")
                print(f"    新路径: {cline_config['location']['path']}")

        # 4. 检查是否已存在相同的插件（根据 identifier.id）
        cline_id = cline_config["identifier"]["id"]
        extension_exists = any(
            ext.get("identifier", {}).get("id") == cline_id
            for ext in extensions_data
        )

        if extension_exists:
            print(f"[INFO] 插件'{cline_id}'已存在，无需添加。")
        else:
            # 5. 添加新配置到 extensions.json
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
    wait_for_user()
    return None


def configure_uv_environment():
    """
    配置 MCPTools/uv 环境：
    1. 将 MCPTools/uv 路径添加到系统环境变量的 PATH 中
    2. 复制预装的 Python 环境到 uv 目录
    3. 修改 .venv/pyvenv.cfg 指向正确的 Python 路径
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
            wait_for_user()
            return False

        mcp_tools_uv_str = str(mcp_tools_uv_path)
        print(f"准备添加路径: {mcp_tools_uv_str}")
        add_to_path_windows(mcp_tools_uv_str)
        print("[SUCCESS] MCPTools/uv 路径配置完成。")

        # 获取当前用户名
        username = os.getenv("USERNAME")
        if not username:
            print("[ERROR] 无法获取当前用户名")
            wait_for_user()
            return False

        # 复制预装的 Python 环境
        print("\n配置 Python 环境...")
        python_folder_name = "cpython-3.13.5-windows-x86_64-none"
        source_python_dir = mcp_sectrace_dir / "assets" / python_folder_name
        target_python_dir = Path(f"C:/Users/{username}/AppData/Roaming/uv/python")
        target_python_path = target_python_dir / python_folder_name

        # 检查源目录是否存在
        if not source_python_dir.exists():
            print(f"[ERROR] 预装 Python 环境不存在: {source_python_dir}")
            wait_for_user()
            return False

        # 创建目标目录（如果不存在）
        if not target_python_dir.exists():
            print(f"创建目录: {target_python_dir}")
            target_python_dir.mkdir(parents=True, exist_ok=True)

        # 复制 Python 环境
        if target_python_path.exists():
            print(f"[INFO] Python 环境已存在: {target_python_path}")
            print("[INFO] 跳过复制，保留现有文件")
        else:
            print(f"复制 Python 环境...")
            print(f"  源: {source_python_dir}")
            print(f"  目标: {target_python_path}")
            shutil.copytree(source_python_dir, target_python_path)
            print(f"[SUCCESS] Python 环境复制完成")

        # 修改 .venv/pyvenv.cfg 文件
        print("\n配置虚拟环境...")
        pyvenv_cfg_path = mcp_sectrace_dir / ".venv" / "pyvenv.cfg"

        if not pyvenv_cfg_path.exists():
            print(f"[ERROR] pyvenv.cfg 不存在: {pyvenv_cfg_path}")
            wait_for_user()
            return False

        # 读取原文件内容
        try:
            with open(pyvenv_cfg_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except Exception as e:
            print(f"[ERROR] 读取 pyvenv.cfg 失败: {e}")
            wait_for_user()
            return False

        # 构建新的 home 路径（使用反斜杠，符合 Windows 习惯）
        new_home_path = f"C:\\Users\\{username}\\AppData\\Roaming\\uv\\python\\{python_folder_name}"

        # 修改第一行
        if lines:
            old_first_line = lines[0].strip()
            lines[0] = f"home = {new_home_path}\n"
            print(f"  修改 pyvenv.cfg:")
            print(f"    原: {old_first_line}")
            print(f"    新: home = {new_home_path}")

        # 写回文件
        try:
            with open(pyvenv_cfg_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            print(f"[SUCCESS] pyvenv.cfg 配置完成")
        except Exception as e:
            print(f"[ERROR] 写入 pyvenv.cfg 失败: {e}")
            wait_for_user()
            return False

        print("[SUCCESS] MCPTools/uv 环境配置完成。")
        return True

    except Exception as e:
        print(f"[ERROR] 配置 MCPTools/uv 环境失败: {e}")
        import traceback
        traceback.print_exc()
        wait_for_user()
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
        wait_for_user()
        return False

    print(f"[INFO] 项目目录: {mcp_sectrace_dir}\n")

    # Step 1: 配置 uv 环境
    if not configure_uv_environment():
        wait_for_user()
        return False

    print()

    # Step 2: 配置 VSCode 插件
    if not configure_vscode_extensions(mcp_sectrace_dir):
        wait_for_user()
        return False

    print()

    # Step 3: 配置 MCPTools
    if not configure_mcp_tools(mcp_sectrace_dir):
        wait_for_user()
        return False

    print()

    # Step 4: 配置溯源工作流
    if not configure_workflow(mcp_sectrace_dir):
        wait_for_user()
        return False

    print()

    # Step 5: 配置浏览器并引导微步登录
    if not configure_browser_login(mcp_sectrace_dir):
        wait_for_user()
        return False

    print()

    # Step 6: 配置 PaddleX 模型
    if not configure_paddlex_models(mcp_sectrace_dir):
        wait_for_user()
        return False

    print()

    # Step 7: 配置工具路径
    if not configure_tool_paths(mcp_sectrace_dir):
        wait_for_user()
        return False

    print("-" * 50)
    print("环境配置初始化完成！")
    return True


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
