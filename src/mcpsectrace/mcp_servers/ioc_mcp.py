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
    description: str
    filename_suffix: str
    markdown_title: str
    is_required: bool = True


@dataclass
class ThreatBookConfig:
    """ThreatBook查询配置"""

    target_type: str  # "ip" or "domain"
    target_value: str
    url_template: str
    screenshot_configs: List[ScreenshotConfig]


class SeleniumDriver:
    """Selenium WebDriver 封装类"""

    def __init__(self):
        self.driver: Optional[webdriver.Chrome] = None

    def __enter__(self):
        return self.setup_driver()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()

    def setup_driver(self) -> webdriver.Chrome:
        """设置并返回WebDriver实例"""
        # 从配置获取路径
        chrome_exe_path = get_config_value("chrome.exe_path", default="")
        chromedriver_exe_path = get_config_value("chrome.driver_path", default="")
        user_data_dir = get_config_value("chrome.user_data_dir", default="")

        # 如果配置为空，使用系统默认路径
        if not chrome_exe_path:
            chrome_exe_path = "chrome"  # 使用系统PATH中的chrome
        if not chromedriver_exe_path:
            chromedriver_exe_path = "chromedriver"  # 使用系统PATH中的chromedriver

        # 检查路径是否存在（如果是完整路径）
        if chrome_exe_path != "chrome" and not os.path.exists(chrome_exe_path):
            raise FileNotFoundError(f"Chrome 浏览器路径不存在 -> {chrome_exe_path}")
        if chromedriver_exe_path != "chromedriver" and not os.path.exists(
            chromedriver_exe_path
        ):
            raise FileNotFoundError(
                f"ChromeDriver 路径不存在 -> {chromedriver_exe_path}"
            )

        # 配置 Chrome 选项
        chrome_options = Options()
        if chrome_exe_path != "chrome":
            chrome_options.binary_location = chrome_exe_path

        # 使用配置区的用户数据目录路径
        if user_data_dir:
            user_data_dir_abs = os.path.abspath(user_data_dir)
            print(f"使用持久化用户数据目录: {user_data_dir_abs}")
            chrome_options.add_argument(f"--user-data-dir={user_data_dir_abs}")

        # 从配置获取窗口尺寸
        window_size = get_config_value("ioc.window_size", default=[1920, 1200])

        # 其他浏览器选项
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument(f"--window-size={window_size[0]},{window_size[1]}")
        chrome_options.add_argument("--start-maximized")

        # 配置 ChromeDriver 服务
        service = Service(executable_path=chromedriver_exe_path)

        # 初始化 WebDriver
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.set_window_size(window_size[0], window_size[1])

        return self.driver

    def cleanup(self):
        """清理资源"""
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                print(f"清理WebDriver时出错: {e}")
            finally:
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
    ) -> Tuple[bool, str, str]:
        """
        对指定元素进行截图

        Returns:
            (成功标志, 截图路径, Markdown内容)
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

            # 截图并保存，文件名使用配置的替换规则
            sanitized_target = sanitize_filename(target_value)
            screenshot_path = os.path.join(
                output_dir, f"{sanitized_target}_{config.filename_suffix}.png"
            )
            element.screenshot(screenshot_path)
            print(f"{config.description}截图已保存: {screenshot_path}")

            # 生成Markdown内容
            md_content = f"## {config.markdown_title}\n"
            md_content += f"![{config.markdown_title}](ioc_pic/{sanitized_target}_{config.filename_suffix}.png)\n"

            return True, screenshot_path, md_content

        except Exception as e:
            print(f"截图{config.description}时出错: {e}")
            md_content = f"## {config.markdown_title}\n"
            md_content += f"无法获取{config.description}截图\n"
            return False, "", md_content


class ThreatBookAnalyzer:
    """ThreatBook分析器主类"""

    @staticmethod
    def create_output_directories():
        """创建输出目录"""
        output_dir = get_config_value("output_path", default="./logs/ioc")
        pic_output_dir = get_config_value(
            "screenshot_path", default="./logs/ioc/ioc_pic"
        )

        output_dir_abs = os.path.abspath(output_dir)
        pic_output_dir_abs = os.path.abspath(pic_output_dir)
        os.makedirs(output_dir_abs, exist_ok=True)
        os.makedirs(pic_output_dir_abs, exist_ok=True)
        return output_dir_abs, pic_output_dir_abs

    @staticmethod
    def generate_report_header(target_type: str, target_value: str) -> List[str]:
        """生成报告头部"""
        type_name = "IP地址" if target_type == "ip" else "域名"
        md_content = [
            f"# {type_name}分析报告: {target_value}",
            f"\n**分析时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n",
        ]
        return md_content

    @staticmethod
    def save_markdown_report(
        md_content: List[str], output_dir: str, target_value: str, target_type: str
    ):
        """保存Markdown报告"""
        sanitized_target = sanitize_filename(target_value)
        md_filename = os.path.join(
            output_dir, f"{sanitized_target}_{target_type}_analysis.md"
        )
        with open(md_filename, "w", encoding="utf-8") as f:
            f.write("\n".join(md_content))
        print(f"Markdown分析报告已保存: {md_filename}")
        return md_filename


def sanitize_filename(filename: str) -> str:
    """根据配置规则替换文件名中的特殊字符"""
    replacements = get_config_value(
        "ioc.filename_replacements",
        default={
            " ": "_",
            "/": "_",
            ":": "_",
            "\\": "_",
            "*": "_",
            "?": "_",
            '"': "_",
            "<": "_",
            ">": "_",
            "|": "_",
        },
    )

    result = filename
    for old_char, new_char in replacements.items():
        result = result.replace(old_char, new_char)
    return result


def get_screenshot_configs_for_ip() -> List[ScreenshotConfig]:
    """获取IP查询的截图配置"""
    return [
        ScreenshotConfig(
            element_selector=get_config_value(
                "ioc.css_selectors.summary", default="summary-top"
            ),
            selector_type="class",
            description="概要信息",
            filename_suffix="summary_top",
            markdown_title="概要信息",
        ),
        ScreenshotConfig(
            element_selector=get_config_value(
                "ioc.css_selectors.insight_container", default="result-intelInsight_con"
            ),
            selector_type="class",
            description="情报洞察",
            filename_suffix="insight",
            markdown_title="情报洞察",
        ),
    ]


def get_screenshot_configs_for_domain() -> List[ScreenshotConfig]:
    """获取域名查询的截图配置"""
    return [
        ScreenshotConfig(
            element_selector=get_config_value(
                "ioc.css_selectors.summary", default="summary-top"
            ),
            selector_type="class",
            description="概要信息",
            filename_suffix="summary_top",
            markdown_title="概要信息",
        ),
        ScreenshotConfig(
            element_selector=get_config_value(
                "ioc.css_selectors.insight_container", default="result-intelInsight_con"
            ),
            selector_type="class",
            description="情报洞察",
            filename_suffix="insight",
            markdown_title="情报洞察",
        ),
    ]


@mcp.tool()
def query_threatbook_ip_and_save_with_screenshots(ip_address: str) -> str:
    """
    查询威胁情报平台上指定IP地址的信息，并截图保存分析结果为Markdown格式。

    此工具会自动访问威胁情报平台，查询IP地址的相关信息，截图保存重要内容，
    并生成包含截图的Markdown分析报告。

    Args:
        ip_address (str): 需要查询的 IP 地址。
    """
    config = ThreatBookConfig(
        target_type="ip",
        target_value=ip_address,
        url_template=get_config_value(
            "ioc.url_templates.ip", default="https://x.threatbook.com/v5/ip/{target}"
        ),
        screenshot_configs=get_screenshot_configs_for_ip(),
    )

    return analyze_target_with_config(config)


@mcp.tool()
def query_threatbook_domain_and_save_with_screenshots(domain_name: str) -> str:
    """
    查询威胁情报平台上指定域名的信息，并截图保存分析结果为Markdown格式。

    此工具会自动访问威胁情报平台，查询域名的相关信息，截图保存重要内容，
    并生成包含截图的Markdown分析报告。

    Args:
        domain_name (str): 需要查询的域名。
    """
    config = ThreatBookConfig(
        target_type="domain",
        target_value=domain_name,
        url_template=get_config_value(
            "ioc.url_templates.domain",
            default="https://x.threatbook.com/v5/domain/{target}",
        ),
        screenshot_configs=get_screenshot_configs_for_domain(),
    )

    return analyze_target_with_config(config)


def analyze_target_with_config(config: ThreatBookConfig) -> str:
    """分析目标（IP或域名）的通用方法"""
    try:
        # 创建输出目录
        output_dir_abs, pic_output_dir_abs = (
            ThreatBookAnalyzer.create_output_directories()
        )

        with SeleniumDriver() as driver:
            # 构建URL并访问
            url = config.url_template.format(target=config.target_value)
            print(f"正在访问: {url}")
            driver.get(url)

            # 等待页面加载
            page_load_wait = get_config_value("ioc.page_load_wait_seconds", default=10)
            print(f"页面加载中，请等待 {page_load_wait} 秒...")
            time.sleep(page_load_wait)

            # 生成报告头部
            md_content = ThreatBookAnalyzer.generate_report_header(
                config.target_type, config.target_value
            )

            # 处理配置的截图任务
            for screenshot_config in config.screenshot_configs:
                success, screenshot_path, md_section = (
                    ElementScreenshot.take_element_screenshot(
                        driver,
                        screenshot_config,
                        config.target_value,
                        pic_output_dir_abs,
                    )
                )
                md_content.append(md_section)

            # 处理折叠面板
            collapse_md = process_collapse_panels(
                driver, config.target_value, pic_output_dir_abs
            )
            if collapse_md:
                md_content.append(collapse_md)

            # 保存报告
            report_path = ThreatBookAnalyzer.save_markdown_report(
                md_content, output_dir_abs, config.target_value, config.target_type
            )

            return f"分析完成！报告已保存至: {report_path}"

    except Exception as e:
        error_msg = f"分析过程中发生错误: {str(e)}"
        print(error_msg)
        return error_msg


def process_collapse_panels(
    driver: webdriver.Chrome, target_value: str, output_dir: str
) -> str:
    """处理ant-collapse折叠面板"""
    md_content = ""

    try:
        # 从配置获取折叠面板选择器
        collapse_selector = get_config_value(
            "ioc.css_selectors.collapse_container",
            default=".ant-collapse.ant-collapse-icon-position-start.ant-collapse-ghost",
        )
        collapse_item_selector = get_config_value(
            "ioc.css_selectors.collapse_item", default=".ant-collapse-item"
        )

        collapse_container = driver.find_element(By.CSS_SELECTOR, collapse_selector)

        # 滚动到折叠容器并等待
        ElementScreenshot.scroll_to_element_and_wait(driver, collapse_container)

        collapse_items = collapse_container.find_elements(
            By.CSS_SELECTOR, collapse_item_selector
        )

        if collapse_items:
            md_content += "## 详细分析\n"
            print(f"找到 {len(collapse_items)} 个折叠面板项")

            for i, item in enumerate(collapse_items, 1):
                try:
                    # 获取clue-type标题
                    clue_type_selector = get_config_value(
                        "ioc.css_selectors.clue_type", default="clue-type"
                    )
                    clue_type_element = item.find_element(
                        By.CLASS_NAME, clue_type_selector
                    )
                    clue_title = (
                        clue_type_element.text.strip()
                        if clue_type_element
                        else f"分析项{i}"
                    )
                    print(f"处理折叠面板项: {clue_title}")

                    # 滚动到当前项并等待
                    ElementScreenshot.scroll_to_element_and_wait(driver, item, 1)

                    # 点击展开面板
                    header_selector = get_config_value(
                        "ioc.css_selectors.collapse_header",
                        default="ant-collapse-header",
                    )
                    header = item.find_element(By.CLASS_NAME, header_selector)
                    is_active = "ant-collapse-item-active" in item.get_attribute(
                        "class"
                    )

                    if not is_active:
                        header.click()
                        panel_expand_wait = get_config_value(
                            "ioc.panel_expand_wait_time", default=2
                        )
                        time.sleep(panel_expand_wait)

                    # 截图当前面板项，使用配置的文件名处理
                    sanitized_target = sanitize_filename(target_value)
                    sanitized_title = sanitize_filename(clue_title)
                    panel_screenshot_path = os.path.join(
                        output_dir,
                        f"{sanitized_target}_panel_{i}_{sanitized_title}.png",
                    )
                    item.screenshot(panel_screenshot_path)
                    print(f"面板项截图已保存: {panel_screenshot_path}")

                    # 添加到Markdown
                    md_content += f"### {clue_title}\n"
                    md_content += f"![{clue_title}](ioc_pic/{sanitized_target}_panel_{i}_{sanitized_title}.png)\n\n"

                except Exception as e:
                    print(f"处理第{i}个折叠面板项时出错: {e}")
                    continue

    except Exception as e:
        print(f"处理折叠面板时出错: {e}")

    return md_content


if __name__ == "__main__":
    mcp.run(transport="stdio")
