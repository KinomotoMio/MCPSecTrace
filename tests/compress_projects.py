"""
项目压缩脚本

功能：
- 将 D:\MCPSecTrace 压缩为 D:\MCPSecTrace.zip（排除 .venv 目录）
- 将 D:\MCPTools 压缩为 D:\MCPTools.zip
"""
import io
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

# 设置输出编码为UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


def compress_directory(source_dir, output_zip, exclude_dirs=None):
    """
    压缩目录为ZIP文件

    Args:
        source_dir: 源目录路径
        output_zip: 输出ZIP文件路径
        exclude_dirs: 要排除的目录名称列表
    """
    if exclude_dirs is None:
        exclude_dirs = []

    source_path = Path(source_dir)
    if not source_path.exists():
        print(f"[错误] 源目录不存在: {source_dir}")
        return False

    print(f"\n开始压缩: {source_dir}")
    print(f"输出文件: {output_zip}")
    if exclude_dirs:
        print(f"排除目录: {', '.join(exclude_dirs)}")

    try:
        # 如果输出文件已存在，先删除
        if os.path.exists(output_zip):
            print(f"删除已存在的文件: {output_zip}")
            os.remove(output_zip)

        file_count = 0
        total_size = 0

        with ZipFile(output_zip, 'w', ZIP_DEFLATED) as zipf:
            # 遍历目录
            for root, dirs, files in os.walk(source_dir):
                # 排除指定目录
                dirs[:] = [d for d in dirs if d not in exclude_dirs]

                # 计算相对路径
                rel_root = os.path.relpath(root, source_dir)

                # 添加文件到压缩包
                for file in files:
                    file_path = os.path.join(root, file)

                    # 计算压缩包内的路径
                    if rel_root == '.':
                        arcname = os.path.join(source_path.name, file)
                    else:
                        arcname = os.path.join(source_path.name, rel_root, file)

                    try:
                        zipf.write(file_path, arcname)
                        file_count += 1
                        file_size = os.path.getsize(file_path)
                        total_size += file_size

                        # 每100个文件显示一次进度
                        if file_count % 100 == 0:
                            print(f"  已处理 {file_count} 个文件...")
                    except Exception as e:
                        print(f"  [警告] 无法添加文件 {file_path}: {e}")

        # 获取压缩文件大小
        zip_size = os.path.getsize(output_zip)
        compression_ratio = (1 - zip_size / total_size) * 100 if total_size > 0 else 0

        print(f"[成功] 压缩完成!")
        print(f"  文件数量: {file_count}")
        print(f"  原始大小: {total_size / (1024*1024):.2f} MB")
        print(f"  压缩大小: {zip_size / (1024*1024):.2f} MB")
        print(f"  压缩率: {compression_ratio:.1f}%")

        return True

    except Exception as e:
        print(f"[错误] 压缩失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("=" * 60)
    print("项目压缩脚本")
    print(f"执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # 定义压缩任务
    tasks = [
        {
            "source": r"D:\MCPSecTrace",
            "output": r"D:\MCPSecTrace.zip",
            "exclude": [".venv", "__pycache__", ".pytest_cache", ".git", "node_modules"]
        },
        {
            "source": r"D:\MCPTools",
            "output": r"D:\MCPTools.zip",
            "exclude": ["__pycache__", ".pytest_cache", ".git", "node_modules"]
        }
    ]

    # 执行压缩任务
    success_count = 0
    total_tasks = len(tasks)

    for i, task in enumerate(tasks, 1):
        print(f"\n[{i}/{total_tasks}] 处理任务...")
        if compress_directory(task["source"], task["output"], task["exclude"]):
            success_count += 1

    # 总结
    print("\n" + "=" * 60)
    print(f"压缩任务完成: {success_count}/{total_tasks} 成功")
    print("=" * 60)

    if success_count == total_tasks:
        print("\n[成功] 所有任务成功完成!")
        return 0
    else:
        print(f"\n[失败] 有 {total_tasks - success_count} 个任务失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
