"""
将 init.py 打包成 exe 可执行文件的脚本。
使用 PyInstaller 将 Python 脚本转换为独立的 Windows 可执行文件。
"""

import subprocess
import sys
import os
from pathlib import Path


def build_exe():
    """
    使用 PyInstaller 将 init.py 转换为 exe。
    输出到项目根目录，并自动清除临时文件。
    """
    print("=" * 60)
    print("MCPSecTrace 项目初始化脚本 - EXE 打包工具")
    print("=" * 60)

    # 1. 检查并安装 PyInstaller
    print("\n[Step 1] 检查 PyInstaller 是否已安装...")
    try:
        import PyInstaller
        print("[SUCCESS] PyInstaller 已安装。")
    except ImportError:
        print("[INFO] 正在安装 PyInstaller...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
            print("[SUCCESS] PyInstaller 安装完成。")
        except Exception as e:
            print(f"[ERROR] 安装 PyInstaller 失败: {e}")
            return False

    # 2. 获取项目路径
    print("\n[Step 2] 准备构建参数...")
    project_dir = Path(__file__).parent
    init_py_path = project_dir / "init.py"
    dist_dir = project_dir / "dist"
    build_dir = project_dir / "build"
    spec_file = project_dir / "init.spec"
    exe_output_path = project_dir / "MCPSecTrace_Init.exe"

    if not init_py_path.exists():
        print(f"[ERROR] init.py 文件未找到: {init_py_path}")
        return False

    print(f"源文件: {init_py_path}")
    print(f"输出位置: {exe_output_path}")

    # 3. 清理之前的构建文件
    print("\n[Step 3] 清理之前的构建文件...")
    import shutil
    for directory in [build_dir, dist_dir]:
        if directory.exists():
            try:
                shutil.rmtree(directory)
                print(f"已删除: {directory}")
            except Exception as e:
                print(f"[WARN] 删除 {directory} 失败: {e}")

    # 也删除旧的 spec 文件
    if spec_file.exists():
        try:
            spec_file.unlink()
            print(f"已删除: {spec_file}")
        except Exception as e:
            print(f"[WARN] 删除 {spec_file} 失败: {e}")

    # 4. 使用 PyInstaller 构建 exe
    print("\n[Step 4] 运行 PyInstaller 构建...")
    try:
        cmd = [
            sys.executable,
            "-m",
            "PyInstaller",
            "--onefile",  # 打包成单个 exe 文件
            "--name", "MCPSecTrace_Init",  # exe 文件名
            "--distpath", str(dist_dir),  # 临时输出目录
            "--workpath", str(build_dir),  # 构建临时目录
            "--specpath", str(project_dir),  # spec 文件输出目录
            "--icon", "NONE",  # 不使用图标
            str(init_py_path)
        ]

        print(f"执行命令: {' '.join(cmd)}\n")
        result = subprocess.run(cmd, check=True)

        if result.returncode == 0:
            print("\n[SUCCESS] exe 文件构建完成。")
        else:
            print(f"\n[ERROR] PyInstaller 构建失败，返回码: {result.returncode}")
            return False

    except subprocess.CalledProcessError as e:
        print(f"[ERROR] PyInstaller 执行失败: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] 构建过程出错: {e}")
        import traceback
        traceback.print_exc()
        return False

    # 5. 验证输出并复制到项目根目录
    print("\n[Step 5] 验证生成的 exe 文件...")
    exe_in_dist = dist_dir / "MCPSecTrace_Init.exe"
    if exe_in_dist.exists():
        file_size_mb = exe_in_dist.stat().st_size / (1024 * 1024)
        print(f"[SUCCESS] exe 文件已生成!")
        print(f"临时位置: {exe_in_dist}")
        print(f"文件大小: {file_size_mb:.2f} MB")

        # 6. 复制 exe 到项目根目录
        print(f"\n[Step 6] 复制 exe 到项目根目录...")
        try:
            shutil.copy2(exe_in_dist, exe_output_path)
            print(f"[SUCCESS] exe 已复制到: {exe_output_path}")
        except Exception as e:
            print(f"[ERROR] 复制 exe 失败: {e}")
            return False

        # 7. 清除临时文件（dist、build 目录和 spec 文件）
        print(f"\n[Step 7] 清除临时文件...")
        for directory in [dist_dir, build_dir]:
            if directory.exists():
                try:
                    shutil.rmtree(directory)
                    print(f"已删除目录: {directory}")
                except Exception as e:
                    print(f"[WARN] 删除目录失败: {e}")

        # 删除 spec 文件
        spec_file = project_dir / "MCPSecTrace_Init.spec"
        if spec_file.exists():
            try:
                spec_file.unlink()
                print(f"已删除文件: {spec_file}")
            except Exception as e:
                print(f"[WARN] 删除 spec 文件失败: {e}")

        print("\n" + "=" * 60)
        print("打包完成！exe 文件已生成在项目根目录。")
        print(f"位置: {exe_output_path}")
        print("=" * 60)
        return True
    else:
        print(f"[ERROR] exe 文件生成失败，未找到: {exe_in_dist}")
        return False


if __name__ == "__main__":
    success = build_exe()
    sys.exit(0 if success else 1)