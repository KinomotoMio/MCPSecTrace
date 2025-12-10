# OCR 性能测试说明

## 测试脚本: test_ocr_performance.py

这个测试脚本用于评估 PaddleOCR 在 MCPSecTrace 项目中的识别速度和性能。

## 测试内容

### 1. OCR 初始化测试
- 测试首次初始化 PaddleOCR 引擎的时间
- 验证单例模式(第二次获取应该非常快)
- 检查 OCR 实例是否正确创建

### 2. 单张图片识别测试
- 测试对单张图片的文本识别速度
- 显示识别到的文本内容
- 使用项目中现有的截图文件

### 3. contains_text 方法测试
- 测试检查图片中是否包含特定文本的速度
- 模拟实际使用场景(扫描完成检测)
- 测试常见关键词: "提示", "当前模式", "查杀完成", "暂停"

### 4. 批量识别性能测试
- 批量处理 artifacts 目录下的所有截图
- 计算平均识别速度
- 统计成功率和失败率

## 运行方法

### 方法 1: 直接运行
```bash
cd D:\MCPSecTrace
python tests/test_ocr_performance.py
```

### 方法 2: 使用 UV
```bash
cd D:\MCPSecTrace
uv run python tests/test_ocr_performance.py
```

### 方法 3: 使用 pytest
```bash
cd D:\MCPSecTrace
uv run pytest tests/test_ocr_performance.py -v -s
```

## 预期输出

```
🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍
OCR 性能测试
🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍

============================================================
测试 3: OCR 初始化时间
============================================================

🔄 首次初始化 OCR 引擎...
   ✅ OCR 初始化成功
   ⏱️  初始化耗时: 2.345 秒

🔄 再次获取 OCR 实例(单例模式)...
   ✅ 获取 OCR 实例
   ⏱️  获取耗时: 0.000012 秒
   🔗 是否为同一实例: True

============================================================
测试 1: 单张图片 OCR 识别速度
============================================================

📷 测试图片: scan_progress.png
   路径: D:\MCPSecTrace\src\mcpsectrace\mcp_servers\artifacts\focus_pack\scan_progress.png
   ⏱️  识别耗时: 0.234 秒
   📝 识别到 15 个文本块
   识别内容预览:
      1. 提示
      2. 扫描完成
      3. 发现威胁
      4. 查杀成功
      5. 继续
      ... (还有 10 个)

...
```

## 性能指标参考

### 典型性能(仅供参考):
- **初始化时间**: 2-5 秒(仅首次)
- **单张图片识别**: 0.2-0.5 秒
- **contains_text 检测**: 0.2-0.5 秒
- **识别速率**: 2-5 张/秒

### 影响因素:
1. **图片分辨率**: 分辨率越高,识别越慢
2. **文本密度**: 文字越多,识别越慢
3. **硬件性能**: CPU 性能影响识别速度
4. **首次运行**: 首次初始化需要加载模型(2-5秒)

## 优化建议

### 1. 截图区域优化
- ✅ 只截取包含关键文字的区域(如 focus_pack_mcp 中的 0-0.2 比例)
- ✅ 避免截取整个屏幕

### 2. 检查间隔优化
- ✅ focus_pack: 30秒检查间隔 (较慢扫描)
- ✅ hrkill: 15秒检查间隔 (较快扫描)
- 根据实际扫描时长调整间隔

### 3. 单例模式
- ✅ 已实现 ImageRecognition 单例模式
- ✅ OCR 实例仅初始化一次

### 4. 缓存优化
- 可以考虑对相同图片的识别结果进行缓存
- 当前未实现,如需要可以添加

## 常见问题

### Q1: PaddleOCR 初始化很慢?
**A**: 首次初始化需要加载模型,这是正常的。后续使用会很快(单例模式)。

### Q2: 识别速度太慢?
**A**:
- 减小截图区域
- 降低图片分辨率
- 增加检查间隔时间

### Q3: 识别不准确?
**A**:
- 确保截图清晰
- 检查字体大小是否太小
- 尝试调整截图区域

### Q4: 找不到测试图片?
**A**:
- 先运行 focus_pack_mcp 或 hrkill_mcp 生成截图
- 或者使用自己的测试图片,修改脚本中的路径

## 项目中的 OCR 使用

### hrkill_mcp.py
```python
# Step 3: 检测扫描启动
recognizer = ImageRecognition()
if recognizer.contains_text(screenshot_path, "暂停", case_sensitive=False):
    print("正在执行病毒查杀")

# Step 4: 检测扫描完成
if recognizer.contains_text(screenshot_path, "查杀完成", case_sensitive=False):
    print("病毒查杀已完成")
```

### focus_pack_mcp.py
```python
# Step 3: 验证扫描启动
recognizer = ImageRecognition()
if recognizer.contains_text(screenshot_path, "当前模式", case_sensitive=False):
    print("正在执行快速扫描")

# Step 4: 检测扫描完成
if recognizer.contains_text(screenshot_path, "提示", case_sensitive=False):
    print("快速扫描已完成")
```

## 性能监控建议

如果需要长期监控 OCR 性能,可以:

1. 在 `debug_print()` 中记录 OCR 调用时间
2. 收集统计数据到日志文件
3. 定期分析日志,优化性能瓶颈

## 参考资料

- PaddleOCR 文档: https://github.com/PaddlePaddle/PaddleOCR
- ImageRecognition 源码: `src/mcpsectrace/utils/image_recognition.py`
