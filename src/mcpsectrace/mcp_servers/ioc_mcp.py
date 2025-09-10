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

from mcpsectrace.utils import get_settings

# ==============================================================================
# ---                           CONFIGURATION                            ---
# ==============================================================================
# 从配置加载设置
SETTINGS = get_settings()

# Chrome 和 ChromeDriver 的可执行文件路径
CHROME_EXE_PATH = SETTINGS.get("selenium", {}).get("chrome_exe_path", "")
CHROMEDRIVER_EXE_PATH = SETTINGS.get("selenium", {}).get("chromedriver_exe_path", "")

# 持久化的用户数据目录路径
# 指定一个Chrome用户配置文件夹，脚本将加载并使用其中的Cookies、会话等信息。
# 如果想从一个全新的状态开始，可以指向一个空文件夹。
USER_DATA_DIR = SETTINGS.get("selenium", {}).get(
    "user_data_dir", r"C:\Users\Sssu\AppData\Local\Google\Chrome for Testing\User Data"
)

# 页面加载等待时间（秒）
PAGE_LOAD_WAIT_SECONDS = SETTINGS.get("selenium", {}).get("page_load_wait_seconds", 10)

# 结果输出目录，将结果保存在指定的子文件夹中
OUTPUT_DIR = (
    SETTINGS.get("ioc", {})
    .get("output", {})
    .get("html_output_dir", "data/logs/ioc/html")
)
PIC_OUTPUT_DIR = (
    SETTINGS.get("ioc", {})
    .get("output", {})
    .get("pic_output_dir", "data/logs/ioc/ioc_pic")
)

# ==============================================================================

_mcp_cfg = SETTINGS.get("mcp", {}).get("ioc", {})
mcp = FastMCP(
    _mcp_cfg.get("name", "ioc"),
    log_level=_mcp_cfg.get("log_level", "ERROR"),
    port=_mcp_cfg.get("port", 8888),
)


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
        # 检查路径是否存在
        if not os.path.exists(CHROME_EXE_PATH):
            raise FileNotFoundError(f"Chrome 浏览器路径不存在 -> {CHROME_EXE_PATH}")
        if not os.path.exists(CHROMEDRIVER_EXE_PATH):
            raise FileNotFoundError(
                f"ChromeDriver 路径不存在 -> {CHROMEDRIVER_EXE_PATH}"
            )

        # 配置 Chrome 选项
        chrome_options = Options()
        chrome_options.binary_location = CHROME_EXE_PATH

        # 使用配置区的用户数据目录路径
        user_data_dir_abs = os.path.abspath(USER_DATA_DIR)
        print(f"使用持久化用户数据目录: {user_data_dir_abs}")
        chrome_options.add_argument(f"--user-data-dir={user_data_dir_abs}")

        # 其他浏览器选项 - 增大窗口尺寸以获得更好的截图效果
        # chrome_options.add_argument("--headless")  # 如果需要后台运行，请取消此行注释
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--window-size=1920,1200")
        chrome_options.add_argument("--start-maximized")

        # 配置 ChromeDriver 服务
        service = Service(executable_path=CHROMEDRIVER_EXE_PATH)

        # 初始化 WebDriver
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.set_window_size(1920, 1200)

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
        driver: webdriver.Chrome, element: WebElement, wait_seconds: int = 2
    ):
        """滚动到元素位置并等待指定时间"""
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
            # 根据选择器类型查找元素
            if config.selector_type == "class":
                element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located(
                        (By.CLASS_NAME, config.element_selector)
                    )
                )
            elif config.selector_type == "css":
                element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, config.element_selector)
                    )
                )
            elif config.selector_type == "id":
                element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, config.element_selector))
                )
            else:
                raise ValueError(f"不支持的选择器类型: {config.selector_type}")

            # 滚动到元素并等待
            ElementScreenshot.scroll_to_element_and_wait(driver, element, 2)

            # 截图并保存
            screenshot_path = os.path.join(
                output_dir, f"{target_value}_{config.filename_suffix}.png"
            )
            element.screenshot(screenshot_path)
            print(f"{config.description}截图已保存: {screenshot_path}")

            # 生成Markdown内容
            md_content = f"## {config.markdown_title}\n"
            md_content += f"![{config.markdown_title}](ioc_pic/{target_value}_{config.filename_suffix}.png)\n"

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
        output_dir_abs = os.path.abspath(OUTPUT_DIR)
        pic_output_dir_abs = os.path.abspath(PIC_OUTPUT_DIR)
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
        md_filename = os.path.join(
            output_dir, f"{target_value}_{target_type}_analysis.md"
        )
        with open(md_filename, "w", encoding="utf-8") as f:
            f.write("\n".join(md_content))
        print(f"Markdown分析报告已保存: {md_filename}")
        return md_filename


def scroll_to_element_and_wait(driver, element, wait_seconds=2):
    """滚动到元素位置并等待指定时间"""
    try:
        # 滚动到元素位置
        driver.execute_script(
            "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});",
            element,
        )
        time.sleep(wait_seconds)  # 等待滚动和渲染完成
    except Exception as e:
        print(f"滚动到元素时出错: {e}")


# MCP工具定义
@mcp.tool()
def query_threatbook_ip_and_save_with_screenshots(ip_address: str) -> str:
    """
    使用 Selenium 打开微步在线（ThreatBook）查询指定 IP，并对指定元素进行截图保存。
    此版本会使用持久化的用户数据目录来保留会话信息（如 Cookies）。
    截图summary-top、result-intelInsight_con和ant-collapse类元素，并生成分析报告。

    Args:
        ip_address (str): 需要查询的 IP 地址。
    """
    # 定义IP查询的截图配置
    screenshot_configs = [
        ScreenshotConfig(
            element_selector="summary-top",
            selector_type="class",
            description="概要信息",
            filename_suffix="summary_top",
            markdown_title="概要信息",
        ),
        ScreenshotConfig(
            element_selector="result-intelInsight_con",
            selector_type="class",
            description="情报洞察",
            filename_suffix="insight",
            markdown_title="情报洞察",
        ),
    ]

    config = ThreatBookConfig(
        target_type="ip",
        target_value=ip_address,
        url_template="https://x.threatbook.com/v5/ip/{target}",
        screenshot_configs=screenshot_configs,
    )

    return analyze_target_with_config(config)


@mcp.tool()
def query_threatbook_domain_and_save_with_screenshots(domain_name: str) -> str:
    """
    使用 Selenium 打开微步在线（ThreatBook）查询指定域名，并对指定元素进行截图保存。
    截图summary-top、result-intelInsight_con和ant-collapse类元素，并生成分析报告。

    Args:
        domain_name (str): 需要查询的域名。
    """
    # 定义域名查询的截图配置
    screenshot_configs = [
        ScreenshotConfig(
            element_selector="summary-top",
            selector_type="class",
            description="概要信息",
            filename_suffix="summary_top",
            markdown_title="概要信息",
        ),
        ScreenshotConfig(
            element_selector="result-intelInsight_con",
            selector_type="class",
            description="情报洞察",
            filename_suffix="insight",
            markdown_title="情报洞察",
        ),
    ]

    config = ThreatBookConfig(
        target_type="domain",
        target_value=domain_name,
        url_template="https://x.threatbook.com/v5/domain/{target}",
        screenshot_configs=screenshot_configs,
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
            print(f"页面加载中，请等待 {PAGE_LOAD_WAIT_SECONDS} 秒...")
            time.sleep(PAGE_LOAD_WAIT_SECONDS)

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
        collapse_container = driver.find_element(
            By.CSS_SELECTOR,
            ".ant-collapse.ant-collapse-icon-position-start.ant-collapse-ghost",
        )

        # 滚动到折叠容器并等待
        ElementScreenshot.scroll_to_element_and_wait(driver, collapse_container, 2)

        collapse_items = collapse_container.find_elements(
            By.CSS_SELECTOR, ".ant-collapse-item"
        )

        if collapse_items:
            md_content += "## 详细分析\n"
            print(f"找到 {len(collapse_items)} 个折叠面板项")

            for i, item in enumerate(collapse_items, 1):
                try:
                    # 获取clue-type标题
                    clue_type_element = item.find_element(By.CLASS_NAME, "clue-type")
                    clue_title = (
                        clue_type_element.text.strip()
                        if clue_type_element
                        else f"分析项{i}"
                    )
                    print(f"处理折叠面板项: {clue_title}")

                    # 滚动到当前项并等待
                    ElementScreenshot.scroll_to_element_and_wait(driver, item, 1)

                    # 点击展开面板
                    header = item.find_element(By.CLASS_NAME, "ant-collapse-header")
                    is_active = "ant-collapse-item-active" in item.get_attribute(
                        "class"
                    )

                    if not is_active:
                        header.click()
                        time.sleep(2)

                    # 截图当前面板项
                    panel_screenshot_path = os.path.join(
                        output_dir,
                        f"{target_value}_panel_{i}_{clue_title.replace(' ', '_')}.png",
                    )
                    item.screenshot(panel_screenshot_path)
                    print(f"面板项截图已保存: {panel_screenshot_path}")

                    # 添加到Markdown
                    md_content += f"### {clue_title}\n"
                    md_content += f"![{clue_title}](ioc_pic/{target_value}_panel_{i}_{clue_title.replace(' ', '_')}.png)\n\n"

                except Exception as e:
                    print(f"处理第{i}个折叠面板项时出错: {e}")
                    continue

    except Exception as e:
        print(f"处理折叠面板时出错: {e}")

    return md_content


if __name__ == "__main__":
    mcp.run(transport=_mcp_cfg.get("transport", "stdio"))
