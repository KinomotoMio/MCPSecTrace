import winreg
import os
import json
import shutil
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


def configure_workflow():
    """
    配置溯源工作流：
    将 assets/workflow 目录下的所有 markdown 文件
    复制到 C:/Users/{username}/Documents/Cline/Workflows/ 目录下
    """
    print("[Step 4] 配置溯源工作流...")

    try:
        # 获取源目录路径
        mcp_sectrace_dir = Path(__file__).parent
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


def configure_mcp_tools():
    """
    配置 MCPTools：
    将 mcpsetting.json 复制到 Cline 的配置目录，
    命名为 cline_mcp_settings.json（覆盖现有文件）
    """
    print("[Step 3] 配置 MCPTools...")

    try:
        # 获取源文件路径
        mcp_sectrace_dir = Path(__file__).parent
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


def configure_vscode_extensions():
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
        mcp_sectrace_dir = Path(__file__).parent
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


def configure_uv_environment():
    """
    配置 MCPTools/uv 环境：
    将 MCPTools/uv 路径添加到系统环境变量的 PATH 中。
    """
    print("[Step 1] 配置 MCPTools/uv 路径...")
    try:
        # 获取 MCPSecTrace 的父目录
        mcp_sectrace_dir = Path(__file__).parent
        mcp_tools_uv_path = mcp_sectrace_dir.parent / "MCPTools" / "uv"

        # 验证路径是否存在
        if not mcp_tools_uv_path.exists():
            print(f"[ERROR] MCPTools/uv 路径不存在: {mcp_tools_uv_path}")
            return False

        mcp_tools_uv_str = str(mcp_tools_uv_path)
        print(f"准备添加路径: {mcp_tools_uv_str}")
        add_to_path_windows(mcp_tools_uv_str)
        print("[SUCCESS] MCPTools/uv 路径配置完成。")
        return True

    except Exception as e:
        print(f"[ERROR] 配置 MCPTools/uv 路径失败: {e}")
        return False


def initialize_environment():
    """
    初始化项目环境配置，执行所有初始化步骤。
    """
    print("开始初始化环境配置...")
    print("-" * 50)

    # Step 1: 配置 uv 环境
    if not configure_uv_environment():
        return False

    print()

    # Step 2: 配置 VSCode 插件
    if not configure_vscode_extensions():
        return False

    print()

    # Step 3: 配置 MCPTools
    if not configure_mcp_tools():
        return False

    print()

    # Step 4: 配置溯源工作流
    if not configure_workflow():
        return False

    print("-" * 50)
    print("环境配置初始化完成！")
    return True


def main():
    """
    主函数，执行项目初始化。
    """
    initialize_environment()


if __name__ == "__main__":
    main()
