import psutil
import os
from paddleocr import PaddleOCR
from PIL import Image

# 图片路径
image_path = r"D:\MCPSecTrace\assets\screenshots\hr\scan_complete.png"

# 获取当前进程
process = psutil.Process(os.getpid())

# 记录初始内存
print("=" * 50)
print("开始内存监控")
print("=" * 50)

initial_memory = process.memory_info().rss / 1024 / 1024  # 转换为 MB
print(f"初始内存: {initial_memory:.2f} MB")

# 初始化 PaddleOCR（中文，CPU，关闭角度分类以提速）
print("\n初始化 PaddleOCR...")
ocr = PaddleOCR(
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
    use_textline_orientation=False,
)

after_init_memory = process.memory_info().rss / 1024 / 1024
print(f"初始化后内存: {after_init_memory:.2f} MB")
print(f"初始化占用内存: {after_init_memory - initial_memory:.2f} MB")

# 读取图片并识别
print(f"\n开始识别图片: {image_path}")
result = ocr.predict(image_path)

after_predict_memory = process.memory_info().rss / 1024 / 1024
print(f"识别后内存: {after_predict_memory:.2f} MB")
print(f"识别占用内存: {after_predict_memory - after_init_memory:.2f} MB")

# 打印结果
print("\n识别结果:")
for res in result:
    print(res["rec_texts"])

print("\n" + "=" * 50)
print(f"总内存占用: {after_predict_memory - initial_memory:.2f} MB")
print("=" * 50)
