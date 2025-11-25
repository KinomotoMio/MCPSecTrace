import winreg
import os
import json
import shutil
import subprocess
from pathlib import Path


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

        # 验证目标目录是否存在
        if not target_dir.exists():
            print(f"[ERROR] 目标目录不存在: {target_dir}")
            return False

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

        # 验证 extensions.json 是否存在
        if not extensions_json_path.exists():
            print(f"[ERROR] extensions.json 文件不存在: {extensions_json_path}")
            return False

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
