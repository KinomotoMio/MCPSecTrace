"""
GUI自动化基类
"""

import time
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from ..utils.image_recognition import ImageRecognition
from ..utils.logging_setup import setup_logger


class BaseAutomation(ABC):
    """GUI自动化工具基类"""

    def __init__(self, tool_name: str, assets_dir: str = "assets/screenshots"):
        """
        初始化自动化工具

        Args:
            tool_name: 工具名称
            assets_dir: 截图资源目录
        """
        self.tool_name = tool_name
        self.logger = setup_logger(
            name=f"automation.{tool_name}",
            log_file=f"data/logs/{tool_name}/{tool_name}_automation.log",
        )
        self.image_recognition = ImageRecognition(assets_dir)
        self.is_running = False

    @abstractmethod
    def start_scan(self) -> bool:
        """
        启动扫描过程

        Returns:
            是否成功启动
        """
        pass

    @abstractmethod
    def wait_for_completion(self, timeout: int = 300) -> bool:
        """
        等待扫描完成

        Args:
            timeout: 超时时间（秒）

        Returns:
            是否在超时前完成
        """
        pass

    @abstractmethod
    def export_results(self, output_path: Optional[str] = None) -> bool:
        """
        导出扫描结果

        Args:
            output_path: 输出路径（可选）

        Returns:
            是否成功导出
        """
        pass

    def run_full_automation(self, output_path: Optional[str] = None) -> bool:
        """
        运行完整的自动化流程

        Args:
            output_path: 输出路径（可选）

        Returns:
            是否成功完成
        """
        try:
            self.logger.info(f"开始 {self.tool_name} 自动化流程")

            # 启动扫描
            if not self.start_scan():
                self.logger.error("启动扫描失败")
                return False

            self.is_running = True

            # 等待完成
            if not self.wait_for_completion():
                self.logger.error("扫描未能在规定时间内完成")
                return False

            # 导出结果
            if not self.export_results(output_path):
                self.logger.error("导出结果失败")
                return False

            self.logger.info(f"{self.tool_name} 自动化流程完成")
            return True

        except Exception as e:
            self.logger.error(f"自动化流程出错: {e}")
            return False
        finally:
            self.is_running = False

    def click_and_wait(
        self,
        image_name: str,
        wait_image: Optional[str] = None,
        click_timeout: int = 10,
        wait_timeout: int = 30,
    ) -> bool:
        """
        点击图像并等待下一个状态

        Args:
            image_name: 要点击的图像名称
            wait_image: 等待出现的图像名称
            click_timeout: 点击超时时间
            wait_timeout: 等待超时时间

        Returns:
            是否成功
        """
        # 点击图像
        if not self.image_recognition.click_image(
            image_name, self.tool_name, timeout=click_timeout
        ):
            return False

        # 如果指定了等待图像，则等待其出现
        if wait_image:
            return self.image_recognition.wait_for_image(
                wait_image, self.tool_name, timeout=wait_timeout
            )

        # 否则只是等待一段时间
        time.sleep(2)
        return True

    def take_screenshot(self, description: str = "") -> str:
        """
        截取当前状态的屏幕截图

        Args:
            description: 截图描述

        Returns:
            截图文件路径
        """
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.tool_name}_{description}_{timestamp}.png"

        screenshot_path = f"data/logs/{self.tool_name}/{filename}"
        return self.image_recognition.capture_screenshot(screenshot_path)
