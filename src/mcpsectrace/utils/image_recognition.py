"""
GUI自动化图像识别工具
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import cv2
import numpy as np
import pyautogui

try:
    from paddleocr import PaddleOCR
except ImportError:
    PaddleOCR = None

logger = logging.getLogger(__name__)


class ImageRecognition:
    """图像识别和GUI自动化辅助类（单例模式）"""

    _instance = None
    _ocr_instance = None
    _ocr_initialized = False

    def __new__(cls, assets_dir: Union[str, Path] = "assets/screenshots"):
        """实现单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_attributes(assets_dir)
        return cls._instance

    def _init_attributes(self, assets_dir: Union[str, Path]):
        """初始化属性"""
        self.assets_dir = Path(assets_dir)
        self.confidence_threshold = 0.8

    @classmethod
    def get_ocr(cls):
        """获取全局 OCR 实例（延迟初始化）"""
        if not cls._ocr_initialized:
            cls._init_ocr()
            cls._ocr_initialized = True
        return cls._ocr_instance

    @classmethod
    def _init_ocr(cls):
        """初始化 PaddleOCR 识别器（仅执行一次）"""
        if PaddleOCR is None:
            logger.warning("PaddleOCR 未安装，OCR 功能不可用")
            return

        try:
            # 初始化 PaddleOCR（中文，关闭不必要的模块以提速）
            cls._ocr_instance = PaddleOCR(
                use_doc_orientation_classify=False, use_doc_unwarping=False
            )
            logger.info("PaddleOCR 初始化成功")
        except Exception as e:
            logger.error(f"PaddleOCR 初始化失败: {e}")
            cls._ocr_instance = None

    def find_image_on_screen(
        self, image_name: str, tool_name: str, confidence: float = None
    ) -> Optional[Tuple[int, int, int, int]]:
        """
        在屏幕上查找图像

        Args:
            image_name: 图像文件名
            tool_name: 工具名称（用于确定子目录）
            confidence: 匹配置信度阈值

        Returns:
            找到的图像位置 (left, top, width, height) 或 None
        """
        if confidence is None:
            confidence = self.confidence_threshold

        image_path = self.assets_dir / tool_name / image_name

        if not image_path.exists():
            logger.error(f"图像文件不存在: {image_path}")
            return None

        try:
            location = pyautogui.locateOnScreen(str(image_path), confidence=confidence)

            if location:
                logger.info(f"找到图像 {image_name}: {location}")
                return location
            else:
                logger.warning(f"未找到图像 {image_name}")
                return None

        except Exception as e:
            logger.error(f"查找图像 {image_name} 时出错: {e}")
            return None

    def click_image(
        self,
        image_name: str,
        tool_name: str,
        confidence: float = None,
        timeout: int = 10,
    ) -> bool:
        """
        点击屏幕上的图像

        Args:
            image_name: 图像文件名
            tool_name: 工具名称
            confidence: 匹配置信度阈值
            timeout: 超时时间（秒）

        Returns:
            是否成功点击
        """
        import time

        start_time = time.time()

        while time.time() - start_time < timeout:
            location = self.find_image_on_screen(image_name, tool_name, confidence)

            if location:
                center_x = location.left + location.width // 2
                center_y = location.top + location.height // 2

                pyautogui.click(center_x, center_y)
                logger.info(f"点击图像 {image_name} 在位置 ({center_x}, {center_y})")
                return True

            time.sleep(0.5)

        logger.error(f"超时：未能找到并点击图像 {image_name}")
        return False

    def wait_for_image(
        self,
        image_name: str,
        tool_name: str,
        timeout: int = 30,
        confidence: float = None,
    ) -> bool:
        """
        等待图像出现在屏幕上

        Args:
            image_name: 图像文件名
            tool_name: 工具名称
            timeout: 超时时间（秒）
            confidence: 匹配置信度阈值

        Returns:
            图像是否在超时前出现
        """
        import time

        start_time = time.time()

        while time.time() - start_time < timeout:
            location = self.find_image_on_screen(image_name, tool_name, confidence)

            if location:
                logger.info(f"检测到图像 {image_name}")
                return True

            time.sleep(1)

        logger.error(f"超时：图像 {image_name} 未出现")
        return False

    def capture_screenshot(self, save_path: Optional[str] = None) -> str:
        """
        截取当前屏幕

        Args:
            save_path: 保存路径（可选）

        Returns:
            截图文件路径
        """
        if save_path is None:
            from datetime import datetime

            timestamp = datetime.now().strftime("%Y%m%d")
            save_path = f"screenshot_{timestamp}.png"

        screenshot = pyautogui.screenshot()
        screenshot.save(save_path)
        logger.info(f"截图保存到: {save_path}")

        return save_path

    def recognize_text_in_image(self, image_path: Union[str, Path]) -> List[str]:
        """
        从图片中识别文本

        Args:
            image_path: 图片路径

        Returns:
            识别出的文本列表
        """
        # 获取全局 OCR 实例
        ocr = self.get_ocr()

        if ocr is None:
            logger.error("PaddleOCR 初始化失败")
            return []

        try:
            result = ocr.predict(str(image_path))
            # 提取识别文本
            texts = [res["rec_texts"] for res in result]
            return texts

        except Exception as e:
            logger.error(f"识别图片时出错: {e}")
            return []

    def contains_text(
        self,
        image_path: Union[str, Path],
        target_text: str,
        case_sensitive: bool = False,
    ) -> bool:
        """
        检查图片中是否包含指定的文本

        Args:
            image_path: 图片路径
            target_text: 目标文本（要查找的字符串）
            case_sensitive: 是否区分大小写

        Returns:
            图片中是否包含该文本
        """
        texts = self.recognize_text_in_image(image_path)

        # 递归展平嵌套列表
        def flatten_texts(text_list):
            result = []
            for item in text_list:
                if isinstance(item, (list, tuple)):
                    result.extend(flatten_texts(item))
                else:
                    result.append(str(item))
            return result

        flat_texts = flatten_texts(texts)

        # 根据 case_sensitive 进行比较
        if case_sensitive:
            return any(target_text in text for text in flat_texts)
        else:
            target_lower = target_text.lower()
            return any(target_lower in text.lower() for text in flat_texts)

    def find_text_in_images(
        self,
        image_dir: Union[str, Path],
        target_text: str,
        case_sensitive: bool = False,
        file_pattern: str = "*.png",
    ) -> Dict[str, bool]:
        """
        在图片目录中查找包含指定文本的图片

        Args:
            image_dir: 图片目录
            target_text: 目标文本
            case_sensitive: 是否区分大小写
            file_pattern: 文件匹配模式（默认为 *.png）

        Returns:
            字典，key 为图片文件名，value 为是否包含目标文本
        """
        image_dir = Path(image_dir)
        if not image_dir.is_dir():
            logger.error(f"不是有效的目录: {image_dir}")
            return {}

        results = {}
        image_files = list(image_dir.glob(file_pattern))

        if not image_files:
            logger.warning(f"目录 {image_dir} 中未找到 {file_pattern} 文件")
            return {}

        logger.info(f"在目录 {image_dir} 中找到 {len(image_files)} 个图片文件")

        for image_path in image_files:
            try:
                contains = self.contains_text(image_path, target_text, case_sensitive)
                results[image_path.name] = contains
                status = "包含" if contains else "不包含"
                logger.info(f"图片 {image_path.name} {status}目标文本")
            except Exception as e:
                logger.error(f"处理图片 {image_path.name} 时出错: {e}")
                results[image_path.name] = False

        return results
