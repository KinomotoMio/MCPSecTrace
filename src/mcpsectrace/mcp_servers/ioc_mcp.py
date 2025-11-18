import csv
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
        chrome_exe_path = get_config_value("paths.chrome_exe", default="")
        chromedriver_exe_path = get_config_value("paths.chromedriver_exe", default="")
        user_data_dir = get_config_value("paths.chrome_user_data_dir", default="")

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
            md_content += f"![{config.markdown_title}](../../src/mcpsectrace/mcp_servers/artifacts/ioc/ioc_pic/{sanitized_target}_{config.filename_suffix}.png)\n"

            return True, screenshot_path, md_content

        except Exception as e:
            error_msg = f"截取元素 {config.element_selector} 时出错: {e}"
            print(error_msg)
            return False, None, f"## {config.markdown_title}\n{error_msg}\n"


class SampleReportAnalyzer:
    """样本报告分析类"""

    @staticmethod
    def analyze_sample_report(
        driver: webdriver.Chrome, sha256: str, pic_output_dir: str
    ) -> Tuple[bool, str]:
        """
        访问样本报告页面并进行分析

        Args:
            driver: WebDriver实例
            sha256: 样本的SHA256值
            pic_output_dir: 截图输出目录

        Returns:
            Tuple[bool, str]: (成功标志, Markdown内容)
        """
        md_content = f"\n### SHA256: {sha256}\n\n"

        try:
            sample_url = f"https://s.threatbook.com/report/file/{sha256}"
            print(f"正在分析样本: {sample_url}")
            driver.get(sample_url)

            # 等待页面加载
            page_load_wait = get_config_value("ioc.page_load_wait_seconds", default=10)
            time.sleep(page_load_wait)

            # 截图第一个位置
            try:
                element_timeout = get_config_value("ioc.element_timeout", default=10)
                screenshot_element = WebDriverWait(driver, element_timeout).until(
                    EC.presence_of_element_located(
                        (
                            By.XPATH,
                            "/html/body/div/span/div/span/div/div/section/main/div/div[1]/div",
                        )
                    )
                )

                # 滚动到元素位置
                driver.execute_script(
                    "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});",
                    screenshot_element,
                )
                time.sleep(2)

                # 保存截图
                sanitized_sha256 = sha256[:16]  # 只取前16个字符作为文件名
                screenshot_path = os.path.join(
                    pic_output_dir, f"sample_{sanitized_sha256}_report.png"
                )
                screenshot_element.screenshot(screenshot_path)
                print(f"样本报告截图已保存: {screenshot_path}")

                md_content += f"![样本报告](../../src/mcpsectrace/mcp_servers/artifacts/ioc/ioc_pic/sample_{sanitized_sha256}_report.png)\n\n"

            except Exception as e:
                error_msg = f"截取样本报告失败: {e}"
                print(error_msg)
                md_content += f"⚠️ {error_msg}\n\n"

            # 新增功能：处理环境列表和发行文件表格
            md_content += SampleReportAnalyzer.extract_environment_and_files(
                driver, sha256
            )

            return True, md_content

        except Exception as e:
            error_msg = f"样本报告分析失败: {e}"
            print(error_msg)
            md_content = f"\n#### SHA256: {sha256}\n\n❌ {error_msg}\n\n"
            return False, md_content

    @staticmethod
    def extract_environment_and_files(driver: webdriver.Chrome, sha256: str) -> str:
        """
        提取环境列表和发行文件表格信息

        Args:
            driver: WebDriver实例
            sha256: 样本SHA256值

        Returns:
            str: Markdown格式的内容
        """
        md_content = ""

        try:
            element_timeout = get_config_value("ioc.element_timeout", default=10)

            # 找到环境列表容器
            env_list_container = WebDriverWait(driver, element_timeout).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, ".styles_envList__C9sZQ")
                )
            )

            # 找到环境列表下的所有子元素（div）
            env_items = env_list_container.find_elements(By.CSS_SELECTOR, "div[role]")

            if not env_items:
                # 备用选择器
                env_items = env_list_container.find_elements(By.CSS_SELECTOR, "div")
                # 过滤掉容器本身，只要子元素
                env_items = [
                    item
                    for item in env_items
                    if item.get_attribute("class") and item != env_list_container
                ][:10]  # 限制数量，避免选择到过多元素

            if env_items:
                print(f"找到 {len(env_items)} 个环境项")
                # md_content += "### 不同环境文件释放位置\n\n"

                for idx, env_item in enumerate(env_items, 1):
                    try:
                        # 获取环境项的文本
                        env_text = env_item.text.strip()
                        if not env_text:
                            continue

                        print(f"处理环境项 {idx}: {env_text}")
                        md_content += f"#### {env_text}环境下常见释放路径\n\n"

                        # 点击环境项
                        driver.execute_script(
                            "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});",
                            env_item,
                        )
                        time.sleep(1)
                        env_item.click()

                        # 等待页面加载
                        wait_time = get_config_value("ioc.scroll_wait_time", default=2)
                        time.sleep(wait_time)

                        # 尝试获取发行文件表格
                        try:
                            # 获取id为releaseFile的元素
                            release_file_container = driver.find_element(
                                By.ID, "releaseFile"
                            )

                            # 找到表格的tbody
                            table_body = release_file_container.find_element(
                                By.CSS_SELECTOR, "tbody.ant-table-tbody"
                            )

                            # 找到所有表格行
                            table_rows = table_body.find_elements(
                                By.CSS_SELECTOR, ".ant-table-row.ant-table-row-level-0"
                            )

                            if table_rows:
                                md_content += f"**常见释放文件位置** ({len(table_rows)} 个)\n\n"

                                for row_idx, row in enumerate(table_rows, 1):
                                    try:
                                        # 找到第一个td（第一列）
                                        first_cell = row.find_element(
                                            By.CSS_SELECTOR, "td.ant-table-cell"
                                        )

                                        # 获取单元格中的所有文本内容
                                        cell_text = first_cell.text.strip()

                                        if cell_text:
                                            md_content += f"- {cell_text}\n\n"
                                            print(
                                                f"  发行版本 {row_idx}: {cell_text}"
                                            )

                                    except Exception as e:
                                        print(f"获取表格行 {row_idx} 失败: {e}")

                                md_content += "\n"
                            else:
                                md_content += "未找到发行版本数据\n\n"

                        except Exception as e:
                            error_msg = f"获取文件常见释放路径失败: {e}"
                            print(error_msg)
                            md_content += f"⚠️ {error_msg}\n\n"

                    except Exception as e:
                        error_msg = f"处理环境项 {idx} 失败: {e}"
                        print(error_msg)
                        md_content += f"- ❌ {error_msg}\n"

            else:
                print("未找到环境列表项")
                md_content += "⚠️ 未找到环境列表信息\n\n"

        except Exception as e:
            error_msg = f"提取环境和文件信息失败: {e}"
            print(error_msg)
            md_content += f"⚠️ {error_msg}\n\n"

        return md_content


class ThreatDataExtractor:
    """威胁数据提取类"""

    @staticmethod
    def click_xpath_element(driver: webdriver.Chrome, xpath: str) -> bool:
        """点击指定XPath元素"""
        try:
            element_timeout = get_config_value("ioc.element_timeout", default=10)
            element = WebDriverWait(driver, element_timeout).until(
                EC.element_to_be_clickable((By.XPATH, xpath))
            )
            driver.execute_script(
                "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});",
                element,
            )
            time.sleep(get_config_value("ioc.scroll_wait_time", default=2))
            element.click()
            return True
        except Exception as e:
            print(f"点击XPath元素失败 {xpath}: {e}")
            return False

    @staticmethod
    def get_element_text(driver: webdriver.Chrome, xpath: str) -> Optional[str]:
        """获取指定XPath元素的文本内容"""
        try:
            element_timeout = get_config_value("ioc.element_timeout", default=10)
            element = WebDriverWait(driver, element_timeout).until(
                EC.presence_of_element_located((By.XPATH, xpath))
            )
            return element.text.strip()
        except Exception as e:
            print(f"获取XPath元素文本失败 {xpath}: {e}")
            return None

    @staticmethod
    def parse_threat_count(text: str) -> Optional[int]:
        """
        解析威胁数量文本，支持K、M等缩写
        例如: "1K +" -> 1000, "1.5K" -> 1500, "2M" -> 2000000, "123" -> 123

        Args:
            text: 威胁数量文本

        Returns:
            解析后的整数，解析失败返回None
        """
        if not text:
            return None

        try:
            # 删除特殊符号（+、空格等）
            text = text.strip()
            # 移除尾部的特殊符号（+、空格等）
            while text and text[-1] in ['+', '-', ' ', '×', '×']:
                text = text[:-1].strip()

            # 检查是否包含单位缩写（K、M、G等）
            text_upper = text.upper()
            multiplier = 1

            if text_upper.endswith('K'):
                multiplier = 1_000
                text = text[:-1].strip()
            elif text_upper.endswith('M'):
                multiplier = 1_000_000
                text = text[:-1].strip()
            elif text_upper.endswith('G'):
                multiplier = 1_000_000_000
                text = text[:-1].strip()
            elif text_upper.endswith('B'):  # Billion
                multiplier = 1_000_000_000
                text = text[:-1].strip()

            # 转换为浮点数再乘以倍数，最后转为整数
            number = float(text)
            result = int(number * multiplier)
            return result

        except (ValueError, AttributeError) as e:
            print(f"威胁数量解析失败 '{text}': {e}")
            return None

    @staticmethod
    def extract_table_data(
        driver: webdriver.Chrome, tbody_xpath: str, target_value: str, output_dir: str
    ) -> Tuple[bool, Optional[List[List[str]]]]:
        """提取表格数据并保存为CSV，返回(成功标志, 表格数据)"""
        try:
            element_timeout = get_config_value("ioc.element_timeout", default=10)
            tbody = WebDriverWait(driver, element_timeout).until(
                EC.presence_of_element_located((By.XPATH, tbody_xpath))
            )

            # 查找所有tr元素
            rows = tbody.find_elements(
                By.CSS_SELECTOR,
                "tr.x-antd-comp-table-row.x-antd-comp-table-row-level-0",
            )

            if not rows:
                print("未找到表格数据行")
                return False, None

            # CSV数据
            csv_data = []
            headers = [
                "文件名称",
                "类型",
                "扫描时间",
                "SHA256",
                "多引擎检出",
                "木马家族和类型",
                "威胁等级",
            ]
            csv_data.append(headers)

            # 提取每行数据
            for row in rows:
                cells = row.find_elements(By.CSS_SELECTOR, "td.x-antd-comp-table-cell")
                if len(cells) >= 7:
                    row_data = []
                    for cell in cells[:7]:  # 只取前7列
                        # 获取最里层的文本内容
                        text = cell.get_attribute("textContent")
                        if text:
                            text = text.strip()
                        row_data.append(text or "")
                    csv_data.append(row_data)

            # 保存CSV文件
            sanitized_target = re.sub(r'[\\/:*?"<>|]', "_", target_value)
            csv_filename = f"{sanitized_target}_threat_data.csv"
            csv_path = os.path.join(output_dir, csv_filename)

            with open(csv_path, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerows(csv_data)

            print(f"相关样本数据CSV已保存: {csv_path}")
            return True, csv_data

        except Exception as e:
            print(f"提取表格数据失败: {e}")
            return False, None

    @staticmethod
    def csv_data_to_markdown(csv_data: List[List[str]]) -> str:
        """将CSV数据转换为Markdown表格格式"""
        if not csv_data or len(csv_data) < 1:
            return ""

        # 提取表头和行数据
        headers = csv_data[0]
        rows = csv_data[1:]

        # 构建Markdown表格
        md_table = "| " + " | ".join(headers) + " |\n"
        md_table += "| " + " | ".join(["---"] * len(headers)) + " |\n"

        for row in rows:
            # 确保行数据与表头列数一致
            row_with_padding = row + [""] * (len(headers) - len(row))
            md_table += "| " + " | ".join(row_with_padding[:len(headers)]) + " |\n"

        return md_table


class ThreatBookAnalyzer:
    """微步在线威胁分析类"""

    @staticmethod
    def create_output_directories():
        """创建输出目录"""
        output_dir = get_config_value("ioc.output_path", default="./logs/ioc")
        pic_output_dir = get_config_value(
            "ioc.screenshot_path", default="./src/mcpsectrace/mcp_servers/artifacts/ioc/ioc_pic"
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
                By.CSS_SELECTOR,
                ".ant-collapse.ant-collapse-icon-position-start.ant-collapse-ghost",
            )
            collapse_items = collapse_container.find_elements(
                By.CSS_SELECTOR, ".ant-collapse-item"
            )

            for i, item in enumerate(collapse_items):
                try:
                    # 获取clue-type标题
                    clue_type_element = item.find_element(By.CLASS_NAME, "clue-type")
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

                    header.click()
                    print("点击面板标题")
                    panel_expand_wait = get_config_value(
                        "ioc.panel_expand_wait_time", default=2
                    )

                    time.sleep(panel_expand_wait)
                    scroll_to_element_and_wait(driver, item, 2)
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
                    md_content += f"![{clue_title}](../../src/mcpsectrace/mcp_servers/artifacts/ioc/ioc_pic/{sanitized_target}_panel_{i}_{sanitized_title}.png)\n\n"

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
            ScreenshotConfig("summary-top", "class", "summary_top", "基本信息"),
            ScreenshotConfig(
                "result-intelInsight_con",
                "class",
                "result_intelInsight_con",
                "情报洞察",
            ),
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
            ScreenshotConfig("summary-top", "class", "summary_top", "基本信息"),
            ScreenshotConfig(
                "result-intelInsight_con",
                "class",
                "result_intelInsight_con",
                "情报洞察",
            ),
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

        # 新增功能：处理特定威胁数据提取
        try:
            # 点击指定的XPath元素 (li[8])
            li_xpath = "/html/body/div[1]/div[1]/main/div[1]/div/div[3]/div/div[1]/div/div/div/ul/li[8]"
            if ThreatDataExtractor.click_xpath_element(driver, li_xpath):
                print("成功点击目标元素")

                # 等待页面更新
                time.sleep(get_config_value("ioc.scroll_wait_time", default=2))

                # 读取数字内容
                
                span_xpath = "/html/body/div[1]/div[1]/main/div[1]/div/div[3]/div/div[1]/div/div/div/ul/li[8]/div/span[2]"
                number_text = ThreatDataExtractor.get_element_text(driver, span_xpath)
                # print(number_text)
                if number_text:
                    # 使用新的解析函数处理威胁数量（支持K、M等缩写）
                    threat_count = ThreatDataExtractor.parse_threat_count(number_text)
                    if threat_count is not None:
                        print(f"检测到威胁数量: {threat_count} (原始文本: {number_text})")
                        print("开始提取表格数据")

                        # 提取表格数据（无论威胁数量是多少）
                        tbody_xpath = "/html/body/div[1]/div[1]/main/div[1]/div/div[3]/div/div[2]/div/div[2]/div/div/div/div/div[1]/div/div/div/div/div/table/tbody"
                        success, csv_data = ThreatDataExtractor.extract_table_data(
                            driver, tbody_xpath, config.target_value, output_dir
                        )
                        if success and csv_data:
                            report_content += "\n---\n\n## 相关样本\n\n"
                            report_content += f"**相关样本数量**: {threat_count}\n\n"

                            # 如果数量 >= 5，显示数量限制说明
                            if threat_count >= 5:
                                report_content += "📝 由于数量限制，我们只获取第一页的内容。\n\n"

                            # 将表格数据转换为Markdown格式并添加到报告
                            md_table = ThreatDataExtractor.csv_data_to_markdown(csv_data)
                            report_content += md_table + "\n"
                            report_content += f"\n💾 详细数据已保存为CSV文件: `{sanitized_target}_threat_data.csv`\n\n"

                            # 新增功能：分析每个样本的详细报告
                            print("\n开始分析每个样本的详细报告...")
                            report_content += "\n---\n\n## 样本常见释放路径分析\n\n"

                            # 从CSV数据中提取SHA256（第4列，索引为3）
                            for row_idx, row in enumerate(csv_data[1:], 1):  # 跳过表头
                                if len(row) > 3 and row[3].strip():  # SHA256在第4列
                                    sha256 = row[3].strip()
                                    print(f"分析样本 {row_idx}/{len(csv_data)-1}: {sha256}")

                                    success, sample_md = (
                                        SampleReportAnalyzer.analyze_sample_report(
                                            driver, sha256, pic_output_dir
                                        )
                                    )
                                    if success:
                                        report_content += sample_md
                                    else:
                                        report_content += sample_md

                            print("样本详细分析完成")
                        else:
                            report_content += "\n---\n\n## 相关样本\n\n"
                            report_content += "⚠️ 表格数据提取失败\n\n"
                    else:
                        print(f"无法解析威胁数量: {number_text}")
                        report_content += "\n---\n\n## 相关样本\n\n"
                        report_content += f"⚠️ 无法解析相关样本数量: {number_text}\n\n"
                else:
                    print("无法获取威胁数量文本")
                    report_content += "\n---\n\n## 相关样本\n\n"
                    report_content += "⚠️ 无法获取相关样本数量信息\n\n"
            else:
                print("点击目标元素失败")
                report_content += "\n---\n\n## 相关样本\n\n"
                report_content += "⚠️ 无法点击目标相关样本元素\n\n"

        except Exception as e:
            print(f"相关样本提取过程出错: {e}")
            report_content += "\n---\n\n## 相关样本\n\n"
            report_content += f"❌ 相关样本提取失败: {str(e)}\n\n"

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
