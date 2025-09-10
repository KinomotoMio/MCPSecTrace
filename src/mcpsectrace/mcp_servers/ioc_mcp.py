import os
import re
import time
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Tuple

from mcp.server.fastmcp import FastMCP
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from mcpsectrace.config import get_config_value

mcp = FastMCP("ioc", log_level="ERROR", port=8888)


@dataclass
class ScreenshotConfig:
    """截图配置信息"""

    element_selector: str
    selector_type: str  # "class", "css", "id"
    filename_suffix: str
    markdown_title: str


@dataclass
class ThreatBookConfig:
    """微步在线查询配置"""

    target_type: str  # "ip" 或 "domain"
    target_value: str
    base_url: str
    screenshot_configs: List[ScreenshotConfig]


class SeleniumDriver:
    """Selenium WebDriver 管理类"""

    def __init__(self):
        self.driver = None

    def setup_driver(self) -> webdriver.Chrome:
        """设置并返回WebDriver实例"""
        # 从配置获取路径
        chrome_exe_path = get_config_value("chrome.exe_path", default="")
        chromedriver_exe_path = get_config_value("chrome.chromedriver_path", default="")
        user_data_dir = get_config_value("chrome.user_data_dir", default="")

        # 检查路径是否存在
        if (
            chrome_exe_path
            and chrome_exe_path != "chrome"
            and not os.path.exists(chrome_exe_path)
        ):
            raise FileNotFoundError(f"Chrome 路径不存在 -> {chrome_exe_path}")

        if chromedriver_exe_path and not os.path.exists(chromedriver_exe_path):
            raise FileNotFoundError(
                f"ChromeDriver 路径不存在 -> {chromedriver_exe_path}"
            )

        # 配置 Chrome 选项
        chrome_options = Options()
        if chrome_exe_path and chrome_exe_path != "chrome":
            chrome_options.binary_location = chrome_exe_path

        # 添加必要的选项
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-infobars")
        chrome_options.add_argument("--disable-notifications")

        # 如果提供了用户数据目录，则使用它
        if user_data_dir:
            chrome_options.add_argument(f"--user-data-dir={user_data_dir}")

        # 创建ChromeDriver服务
        if chromedriver_exe_path:
            service = Service(chromedriver_exe_path)
        else:
            service = Service()  # 使用系统PATH中的chromedriver

        # 创建WebDriver实例
        self.driver = webdriver.Chrome(service=service, options=chrome_options)

        # 从配置获取窗口大小
        window_size = get_config_value("ioc.window_size", default=[1920, 1200])
        self.driver.set_window_size(window_size[0], window_size[1])

        return self.driver

    def quit_driver(self):
        """关闭WebDriver"""
        if self.driver:
            self.driver.quit()
            self.driver = None


class ElementScreenshot:
    """元素截图处理类"""

    @staticmethod
    def scroll_to_element_and_wait(
        driver: webdriver.Chrome, element: WebElement, wait_seconds: int = None
    ):
        """滚动到元素位置并等待指定时间"""
        if wait_seconds is None:
            wait_seconds = get_config_value("ioc.scroll_wait_time", default=2)

        try:
            driver.execute_script(
                "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});",
                element,
            )
            time.sleep(wait_seconds)
        except Exception as e:
            print(f"滚动到元素时出错: {e}")

    @staticmethod
    def take_element_screenshot(
        driver: webdriver.Chrome,
        config: ScreenshotConfig,
        target_value: str,
        output_dir: str,
    ) -> Tuple[bool, Optional[str], str]:
        """
        根据配置截取指定元素的截图

        Returns:
            Tuple[bool, Optional[str], str]: (成功状态, 截图路径, Markdown内容)
        """
        try:
            # 从配置获取超时时间
            element_timeout = get_config_value("ioc.element_timeout", default=10)

            # 根据选择器类型查找元素
            if config.selector_type == "class":
                element = WebDriverWait(driver, element_timeout).until(
                    EC.presence_of_element_located(
                        (By.CLASS_NAME, config.element_selector)
                    )
                )
            elif config.selector_type == "css":
                element = WebDriverWait(driver, element_timeout).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, config.element_selector)
                    )
                )
            elif config.selector_type == "id":
                element = WebDriverWait(driver, element_timeout).until(
                    EC.presence_of_element_located((By.ID, config.element_selector))
                )
            else:
                raise ValueError(f"不支持的选择器类型: {config.selector_type}")

            # 滚动到元素并等待
            ElementScreenshot.scroll_to_element_and_wait(driver, element)

            # 生成安全的文件名
            sanitized_target = re.sub(r'[\\/:*?"<>|]', "_", target_value)
            screenshot_path = os.path.join(
                output_dir, f"{sanitized_target}_{config.filename_suffix}.png"
            )
            element.screenshot(screenshot_path)

            print(f"截图已保存: {screenshot_path}")

            # 生成Markdown内容
            md_content = f"## {config.markdown_title}\n"
            md_content += f"![{config.markdown_title}](ioc_pic/{sanitized_target}_{config.filename_suffix}.png)\n"

            return True, screenshot_path, md_content

        except Exception as e:
            error_msg = f"截取元素 {config.element_selector} 时出错: {e}"
            print(error_msg)
            return False, None, f"## {config.markdown_title}\n{error_msg}\n"


class ThreatBookAnalyzer:
    """微步在线威胁分析类"""

    @staticmethod
    def create_output_directories():
        """创建输出目录"""
        output_dir = get_config_value("output_path", default="./logs/ioc")
        pic_output_dir = get_config_value(
            "screenshot_path", default="./logs/ioc/ioc_pic"
        )

        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(pic_output_dir, exist_ok=True)
        return output_dir, pic_output_dir

    @staticmethod
    def expand_threat_panels(
        driver: webdriver.Chrome, target_value: str, output_dir: str
    ) -> str:
        """展开威胁情报面板并截图"""
        md_content = ""

        # 生成安全的文件名
        sanitized_target = re.sub(r'[\\/:*?"<>|]', "_", target_value)

        try:
            # 微步网站的固定CSS结构
            collapse_container = driver.find_element(
                By.CSS_SELECTOR, ".ant-collapse.ant-collapse-borderless"
            )
            collapse_items = collapse_container.find_elements(
                By.CSS_SELECTOR, ".ant-collapse-item"
            )

            for i, item in enumerate(collapse_items):
                try:
                    # 获取clue-type标题
                    clue_type_element = item.find_element(
                        By.CLASS_NAME, "clue-type"
                    )
                    clue_title = (
                        clue_type_element.text.strip()
                        .replace("/", "_")
                        .replace("\\", "_")
                        .replace(":", "_")
                        .replace("*", "_")
                        .replace("?", "_")
                        .replace('"', "_")
                        .replace("<", "_")
                        .replace(">", "_")
                        .replace("|", "_")
                        .replace(" ", "_")
                    )

                    # 点击展开面板
                    header = item.find_element(By.CLASS_NAME, "ant-collapse-header")
                    is_active = "ant-collapse-item-active" in item.get_attribute(
                        "class"
                    )

                    if not is_active:
                        header.click()
                        panel_expand_wait = get_config_value(
                            "ioc.panel_expand_wait_time", default=2
                        )
                        time.sleep(panel_expand_wait)

                    # 截图面板
                    sanitized_title = clue_title.replace(" ", "_")
                    panel_screenshot_path = os.path.join(
                        output_dir,
                        f"{sanitized_target}_panel_{i}_{sanitized_title}.png",
                    )
                    item.screenshot(panel_screenshot_path)
                    print(f"面板截图已保存: {panel_screenshot_path}")

                    # 添加到Markdown
                    md_content += f"### {clue_title}\n"
                    md_content += f"![{clue_title}](ioc_pic/{sanitized_target}_panel_{i}_{sanitized_title}.png)\n\n"

                except Exception as e:
                    print(f"处理面板 {i} 时出错: {e}")
                    continue

        except Exception as e:
            error_msg = f"展开威胁面板时出错: {e}"
            print(error_msg)
            md_content += f"### 威胁面板截图失败\n{error_msg}\n\n"

        return md_content


@mcp.tool()
def analyze_ip_threat(ip_address: str) -> str:
    """
    分析IP地址的威胁情报信息并生成报告。

    Args:
        ip_address (str): 需要查询的 IP 地址。
    """
    config = ThreatBookConfig(
        target_type="ip",
        target_value=ip_address,
        base_url=f"https://x.threatbook.com/v5/ip/{ip_address}",
        screenshot_configs=[
            ScreenshotConfig("basic-info", "class", "basic_info", "基本信息"),
            ScreenshotConfig("verdict-info", "class", "verdict_info", "判定信息"),
        ],
    )

    return analyze_target_with_config(config)


@mcp.tool()
def analyze_domain_threat(domain_name: str) -> str:
    """
    分析域名的威胁情报信息并生成报告。

    Args:
        domain_name (str): 需要查询的域名。
    """
    config = ThreatBookConfig(
        target_type="domain",
        target_value=domain_name,
        base_url=f"https://x.threatbook.com/v5/domain/{domain_name}",
        screenshot_configs=[
            ScreenshotConfig("basic-info", "class", "basic_info", "基本信息"),
            ScreenshotConfig("verdict-info", "class", "verdict_info", "判定信息"),
        ],
    )

    return analyze_target_with_config(config)


def analyze_target_with_config(config: ThreatBookConfig) -> str:
    """使用配置分析目标并生成报告"""
    selenium_driver = SeleniumDriver()
    output_dir, pic_output_dir = ThreatBookAnalyzer.create_output_directories()

    try:
        # 设置WebDriver
        driver = selenium_driver.setup_driver()

        # 访问目标页面
        print(f"正在访问: {config.base_url}")
        driver.get(config.base_url)

        # 等待页面加载
        page_load_wait = get_config_value("ioc.page_load_wait_seconds", default=10)
        print(f"页面加载中，请等待 {page_load_wait} 秒...")
        time.sleep(page_load_wait)

        # 生成报告头部
        # 生成安全的文件名
        sanitized_target = re.sub(r'[\\/:*?"<>|]', "_", config.target_value)

        report_content = f"""# {config.target_type.upper()} 威胁分析报告

**目标**: {config.target_value}  
**查询时间**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  
**数据来源**: 微步在线威胁情报平台

---

"""

        # 截取基础截图
        for screenshot_config in config.screenshot_configs:
            success, screenshot_path, md_content = (
                ElementScreenshot.take_element_screenshot(
                    driver, screenshot_config, config.target_value, pic_output_dir
                )
            )
            report_content += md_content + "\n"

        # 展开威胁面板并截图
        threat_panels_md = ThreatBookAnalyzer.expand_threat_panels(
            driver, config.target_value, pic_output_dir
        )
        if threat_panels_md:
            report_content += "---\n\n## 威胁情报详情\n\n" + threat_panels_md

        # 保存报告
        report_filename = f"{sanitized_target}_{config.target_type}_threat_report.md"
        report_path = os.path.join(output_dir, report_filename)
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_content)

        print(f"\n✅ 报告已生成: {report_path}")
        return f"报告已成功生成并保存至: {report_path}"

    except Exception as e:
        error_message = f"分析过程中出现错误: {str(e)}"
        print(f"\n❌ {error_message}")
        return error_message

    finally:
        # 确保WebDriver被正确关闭
        selenium_driver.quit_driver()


if __name__ == "__main__":
    # 测试IP分析
    result = analyze_ip_threat("8.8.8.8")
    print(result)
