"""
OCR 性能测试脚本

测试 PaddleOCR 的识别速度和准确率
"""

import time
from pathlib import Path

from mcpsectrace.utils.image_recognition import ImageRecognition


def test_ocr_single_image():
    """测试单张图片的 OCR 识别速度"""
    print("=" * 60)
    print("测试 1: 单张图片 OCR 识别速度")
    print("=" * 60)

    # 创建 ImageRecognition 实例
    recognizer = ImageRecognition()

    # 使用项目中现有的截图进行测试
    # 你需要替换为实际存在的图片路径
    test_images = [
        "src/mcpsectrace/mcp_servers/artifacts/focus_pack/scan_progress.png",
        "src/mcpsectrace/mcp_servers/artifacts/focus_pack/scan_check_20251209.png",
        "src/mcpsectrace/mcp_servers/artifacts/hrkill/scan_progress.png",
    ]

    project_root = Path(__file__).parent.parent

    for image_rel_path in test_images:
        image_path = project_root / image_rel_path

        if not image_path.exists():
            print(f"⚠️  图片不存在: {image_path}")
            continue

        print(f"\n📷 测试图片: {image_path.name}")
        print(f"   路径: {image_path}")

        # 测试识别速度
        start_time = time.time()
        texts = recognizer.recognize_text_in_image(image_path)
        elapsed_time = time.time() - start_time

        print(f"   ⏱️  识别耗时: {elapsed_time:.3f} 秒")
        print(f"   📝 识别到 {len(texts)} 个文本块")

        # 显示识别结果(前5个)
        if texts:
            print(f"   识别内容预览:")
            for i, text in enumerate(texts[:5], 1):
                print(f"      {i}. {text}")
            if len(texts) > 5:
                print(f"      ... (还有 {len(texts) - 5} 个)")


def test_ocr_contains_text():
    """测试 contains_text 方法的速度"""
    print("\n" + "=" * 60)
    print("测试 2: contains_text 方法速度")
    print("=" * 60)

    recognizer = ImageRecognition()
    project_root = Path(__file__).parent.parent

    test_cases = [
        ("src/mcpsectrace/mcp_servers/artifacts/focus_pack/scan_progress.png", "提示"),
        ("src/mcpsectrace/mcp_servers/artifacts/focus_pack/scan_check_20251209.png", "当前模式"),
        ("src/mcpsectrace/mcp_servers/artifacts/hrkill/scan_progress.png", "查杀完成"),
        ("src/mcpsectrace/mcp_servers/artifacts/hrkill/scan_check.png", "暂停"),
    ]

    for image_rel_path, target_text in test_cases:
        image_path = project_root / image_rel_path

        if not image_path.exists():
            print(f"\n⚠️  图片不存在: {image_path}")
            continue

        print(f"\n📷 测试图片: {image_path.name}")
        print(f"   目标文本: '{target_text}'")

        start_time = time.time()
        contains = recognizer.contains_text(image_path, target_text, case_sensitive=False)
        elapsed_time = time.time() - start_time

        result_icon = "✅" if contains else "❌"
        print(f"   {result_icon} 识别结果: {'包含' if contains else '不包含'}")
        print(f"   ⏱️  识别耗时: {elapsed_time:.3f} 秒")


def test_ocr_initialization():
    """测试 OCR 初始化时间"""
    print("\n" + "=" * 60)
    print("测试 3: OCR 初始化时间")
    print("=" * 60)

    print("\n🔄 首次初始化 OCR 引擎...")
    start_time = time.time()

    # 触发 OCR 初始化
    recognizer = ImageRecognition()
    ocr = recognizer.get_ocr()

    elapsed_time = time.time() - start_time

    if ocr is not None:
        print(f"   ✅ OCR 初始化成功")
        print(f"   ⏱️  初始化耗时: {elapsed_time:.3f} 秒")
    else:
        print(f"   ❌ OCR 初始化失败")

    # 测试第二次获取(应该很快,因为是单例)
    print("\n🔄 再次获取 OCR 实例(单例模式)...")
    start_time = time.time()
    ocr2 = recognizer.get_ocr()
    elapsed_time = time.time() - start_time

    print(f"   ✅ 获取 OCR 实例")
    print(f"   ⏱️  获取耗时: {elapsed_time:.6f} 秒")
    print(f"   🔗 是否为同一实例: {ocr is ocr2}")


def test_ocr_batch_recognition():
    """测试批量识别性能"""
    print("\n" + "=" * 60)
    print("测试 4: 批量识别性能")
    print("=" * 60)

    recognizer = ImageRecognition()
    project_root = Path(__file__).parent.parent

    # 查找所有可用的截图
    artifacts_dir = project_root / "src" / "mcpsectrace" / "mcp_servers" / "artifacts"

    if not artifacts_dir.exists():
        print(f"⚠️  artifacts 目录不存在: {artifacts_dir}")
        return

    image_paths = list(artifacts_dir.rglob("*.png"))

    if not image_paths:
        print(f"⚠️  未找到任何 PNG 图片")
        return

    print(f"\n📁 找到 {len(image_paths)} 张图片")

    total_time = 0
    success_count = 0
    fail_count = 0

    for i, image_path in enumerate(image_paths, 1):
        print(f"\n[{i}/{len(image_paths)}] 处理: {image_path.name}")

        try:
            start_time = time.time()
            texts = recognizer.recognize_text_in_image(image_path)
            elapsed_time = time.time() - start_time

            total_time += elapsed_time
            success_count += 1

            print(f"   ✅ 成功 - 耗时: {elapsed_time:.3f}秒, 文本块: {len(texts)}")

        except Exception as e:
            fail_count += 1
            print(f"   ❌ 失败 - {e}")

    # 统计结果
    print("\n" + "=" * 60)
    print("批量识别统计")
    print("=" * 60)
    print(f"   总图片数: {len(image_paths)}")
    print(f"   成功: {success_count}")
    print(f"   失败: {fail_count}")
    print(f"   总耗时: {total_time:.3f} 秒")

    if success_count > 0:
        avg_time = total_time / success_count
        print(f"   平均耗时: {avg_time:.3f} 秒/张")
        print(f"   识别速率: {1 / avg_time:.2f} 张/秒")


def main():
    """主测试函数"""
    print("\n" + "🔍" * 30)
    print("OCR 性能测试")
    print("🔍" * 30)

    # 测试 1: OCR 初始化
    test_ocr_initialization()

    # 测试 2: 单张图片识别
    test_ocr_single_image()

    # 测试 3: contains_text 方法
    test_ocr_contains_text()

    # 测试 4: 批量识别
    test_ocr_batch_recognition()

    print("\n" + "=" * 60)
    print("✅ 所有测试完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
