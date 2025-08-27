"""
GUI自动化图像识别工具
"""

import cv2
import numpy as np
import pyautogui
from pathlib import Path
from typing import Optional, Tuple, Union
import logging

logger = logging.getLogger(__name__)


class ImageRecognition:
    """图像识别和GUI自动化辅助类"""

    def __init__(self, assets_dir: Union[str, Path] = "assets/screenshots"):
        """
        初始化图像识别器

        Args:
            assets_dir: 截图资源目录
        """
        self.assets_dir = Path(assets_dir)
        self.confidence_threshold = 0.8

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

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = f"screenshot_{timestamp}.png"

        screenshot = pyautogui.screenshot()
        screenshot.save(save_path)
        logger.info(f"截图保存到: {save_path}")

        return save_path
