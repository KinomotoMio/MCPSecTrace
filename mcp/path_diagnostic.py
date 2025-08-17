import os
import platform
from pathlib import Path


def run_diagnostics():
    """
    执行浏览器路径诊断，并打印所有找到的路径。
    """
    print("--- 开始浏览器路径诊断 ---")

    if platform.system() != "Windows":
        print("[错误] 此诊断工具仅支持Windows操作系统。")
        return

    try:
        profile_path = Path(os.environ['USERPROFILE'])
        print(f"\n[1] 成功获取用户根目录: {profile_path}")
    except Exception as e:
        print(f"\n[1] 失败：无法获取用户根目录。错误: {e}")
        return

    # 定义要检查的浏览器基础路径
    browser_base_paths = {
        "Google Chrome": profile_path / "AppData/Local/Google/Chrome/User Data",
        "Microsoft Edge": profile_path / "AppData/Local/Microsoft/Edge/User Data"
    }

    for browser, base_path in browser_base_paths.items():
        print(f"\n--- 正在检查 {browser} ---")
        print(f"[2] 预期的 'User Data' 路径是: {base_path}")

        if base_path.exists() and base_path.is_dir():
            print(f"[3] 成功: '{base_path.name}' 目录存在！")

            # 查找所有Profile目录
            found_profiles = []
            try:
                for item in base_path.iterdir():
                    if item.is_dir() and (item.name.startswith("Profile") or item.name == "Default"):
                        found_profiles.append(item)

                if found_profiles:
                    print(f"[4] 成功: 在 '{base_path.name}' 中找到以下 Profile 目录:")
                    for profile_dir in found_profiles:
                        print(f"    - {profile_dir.name}")
                        # 检查History文件是否存在
                        history_path = profile_dir / "History"
                        if history_path.exists() and history_path.is_file():
                            print(f"      [✓] 找到了 'History' 文件: {history_path}")
                        else:
                            print(f"      [✗] 未找到 'History' 文件。")
                else:
                    print(f"[4] 警告: '{base_path.name}' 目录中没有找到名为 'Default' 或 'Profile' 的子目录。")

            except Exception as e:
                print(f"[4] 错误: 在扫描 Profile 目录时出错。错误: {e}")

        else:
            print(f"[3] 失败: '{base_path.name}' 目录不存在或不是一个目录。")

    print("\n--- 诊断结束 ---")


if __name__ == "__main__":
    run_diagnostics()