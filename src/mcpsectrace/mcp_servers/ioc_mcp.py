import os
import re
import time
from datetime import datetime

from mcp.server.fastmcp import FastMCP
from mcpsectrace.utils import get_settings
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# ==============================================================================
# ---                           CONFIGURATION                            ---
# ==============================================================================
# 请在此处修改所有路径和设置

# 从配置加载 Selenium 路径
SETTINGS = get_settings()
CHROME_EXE_PATH = SETTINGS.get("selenium", {}).get("chrome_exe_path", "")
CHROMEDRIVER_EXE_PATH = SETTINGS.get("selenium", {}).get("chromedriver_exe_path", "")

# 持久化的用户数据目录路径
# 指定一个Chrome用户配置文件夹，脚本将加载并使用其中的Cookies、会话等信息。
# 如果想从一个全新的状态开始，可以指向一个空文件夹。
USER_DATA_DIR = r"C:\Users\Sssu\AppData\Local\Google\Chrome for Testing\User Data"

# 页面加载等待时间（秒）
PAGE_LOAD_WAIT_SECONDS = 10

# 结果输出目录，将结果保存在指定的子文件夹中
OUTPUT_DIR = SETTINGS.get("ioc", {}).get("output", {}).get("html_output_dir", "data/logs/ioc/html")
PIC_OUTPUT_DIR = SETTINGS.get("ioc", {}).get("output", {}).get("pic_output_dir", "data/logs/ioc/ioc_pic")

# ==============================================================================

_mcp_cfg = SETTINGS.get("mcp", {}).get("ioc", {})
mcp = FastMCP(
    _mcp_cfg.get("name", "ioc"),
    log_level=_mcp_cfg.get("log_level", "ERROR"),
    port=_mcp_cfg.get("port", 8888),
)


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


@mcp.tool()
def query_threatbook_ip_and_save_with_screenshots(ip_address: str) -> str:
    """
    使用 Selenium 打开微步在线（ThreatBook）查询指定 IP，并对指定元素进行截图保存。
    此版本会使用持久化的用户数据目录来保留会话信息（如 Cookies）。
    截图summary-top、result-intelInsight_con和ant-collapse类元素，并生成分析报告。

    Args:
        ip_address (str): 需要查询的 IP 地址。
    """
    # 检查路径是否存在
    if not os.path.exists(CHROME_EXE_PATH):
        return f"错误：Chrome 浏览器路径不存在 -> {CHROME_EXE_PATH}"
    if not os.path.exists(CHROMEDRIVER_EXE_PATH):
        return f"错误：ChromeDriver 路径不存在 -> {CHROMEDRIVER_EXE_PATH}"

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
    chrome_options.add_argument("--window-size=1920,1200")  # 增加窗口高度
    chrome_options.add_argument("--start-maximized")  # 最大化窗口

    # 配置 ChromeDriver 服务
    service = Service(executable_path=CHROMEDRIVER_EXE_PATH)

    driver = None
    try:
        # 初始化 WebDriver
        driver = webdriver.Chrome(service=service, options=chrome_options)

        # 设置窗口大小
        driver.set_window_size(1920, 1200)

        url = f"https://x.threatbook.com/v5/ip/{ip_address}"
        print(f"正在访问: {url}")
        driver.get(url)

        # 使用配置区的等待时间
        _wait = SETTINGS.get("selenium", {}).get("page_load_wait_seconds", 10)
        print(f"页面加载中，请等待 {_wait} 秒...")
        time.sleep(_wait)

        # 创建输出目录
        output_dir_abs = os.path.abspath(OUTPUT_DIR)
        pic_output_dir_abs = os.path.abspath(PIC_OUTPUT_DIR)
        os.makedirs(output_dir_abs, exist_ok=True)
        os.makedirs(pic_output_dir_abs, exist_ok=True)

        # 创建Markdown内容
        md_content = []

        md_content.append(f"# IP地址分析报告: {ip_address}")
        md_content.append(
            f"\n**分析时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        )

        # 截图summary-top元素
        try:
            summary_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "summary-top"))
            )

            # 滚动到元素并等待
            scroll_to_element_and_wait(driver, summary_element, 2)

            # 截图并保存
            summary_screenshot_path = os.path.join(
                pic_output_dir_abs, f"{ip_address}_summary_top.png"
            )
            summary_element.screenshot(summary_screenshot_path)
            print(f"summary-top元素截图已保存: {summary_screenshot_path}")

            md_content.append(f"## 概要信息")
            md_content.append(f"![概要信息](ioc_pic/{ip_address}_summary_top.png)\n")

        except Exception as e:
            print(f"截图summary-top元素时出错: {e}")
            md_content.append(f"## 概要信息")
            md_content.append(f"无法获取概要信息截图\n")

        # 截图result-intelInsight_con元素
        try:
            insight_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (By.CLASS_NAME, "result-intelInsight_con")
                )
            )

            # 滚动到元素并等待
            scroll_to_element_and_wait(driver, insight_element, 2)

            insight_screenshot_path = os.path.join(
                pic_output_dir_abs, f"{ip_address}_insight.png"
            )
            insight_element.screenshot(insight_screenshot_path)
            print(f"情报洞察元素截图已保存: {insight_screenshot_path}")

            md_content.append(f"## 情报洞察")
            md_content.append(f"![情报洞察](ioc_pic/{ip_address}_insight.png)\n")

        except Exception as e:
            print(f"截图情报洞察元素时出错: {e}")
            md_content.append(f"## 情报洞察")
            md_content.append(f"无法获取情报洞察截图\n")

        # 新增：截图ant-collapse元素
        try:
            collapse_container = driver.find_element(
                By.CSS_SELECTOR,
                ".ant-collapse.ant-collapse-icon-position-start.ant-collapse-ghost",
            )

            # 滚动到折叠容器并等待
            scroll_to_element_and_wait(driver, collapse_container, 2)

            collapse_items = collapse_container.find_elements(
                By.CSS_SELECTOR, ".ant-collapse-item"
            )

            if collapse_items:
                md_content.append(f"## 详细分析")
                print(f"找到 {len(collapse_items)} 个折叠面板项")

                for i, item in enumerate(collapse_items, 1):
                    try:
                        # 获取clue-type标题
                        clue_type_element = item.find_element(
                            By.CLASS_NAME, "clue-type"
                        )
                        clue_title = (
                            clue_type_element.text.strip()
                            if clue_type_element
                            else f"分析项{i}"
                        )
                        print(f"处理折叠面板项: {clue_title}")

                        # 滚动到当前项并等待
                        scroll_to_element_and_wait(driver, item, 2)

                        # 点击展开面板
                        header = item.find_element(
                            By.CSS_SELECTOR, ".ant-collapse-header"
                        )
                        driver.execute_script("arguments[0].click();", header)
                        time.sleep(3)  # 增加等待时间，确保展开动画完成和内容加载

                        # 再次滚动确保完整显示
                        scroll_to_element_and_wait(driver, item, 2)

                        # 检查是否是"相关情报"面板
                        if clue_title == "相关情报":
                            try:
                                # 在当前面板内查找x-comp-nav-list
                                nav_list = item.find_element(
                                    By.CLASS_NAME, "x-comp-nav-list"
                                )
                                print(f"在'{clue_title}'面板中找到导航列表")

                                # 查找所有标签按钮
                                tab_buttons = nav_list.find_elements(
                                    By.CLASS_NAME, "x-comp-tab-btn"
                                )

                                if tab_buttons:
                                    md_content.append(f"### {clue_title}")
                                    print(f"找到 {len(tab_buttons)} 个相关情报标签")

                                    for j, tab_btn in enumerate(tab_buttons, 1):
                                        try:
                                            # 获取标签文本作为标题
                                            tab_text = (
                                                tab_btn.text.strip()
                                                if tab_btn.text
                                                else f"标签{j}"
                                            )
                                            print(f"处理相关情报标签: {tab_text}")

                                            # 滚动到标签并等待
                                            scroll_to_element_and_wait(
                                                driver, tab_btn, 2
                                            )

                                            # 点击标签
                                            driver.execute_script(
                                                "arguments[0].click();", tab_btn
                                            )
                                            time.sleep(3)  # 等待内容加载

                                            # 查找并截图标签内容区域
                                            try:
                                                # 在当前面板内查找内容区域
                                                content_area = item.find_element(
                                                    By.CSS_SELECTOR,
                                                    ".x-comp-tab-content, .tab-content, .related-intel-content",
                                                )

                                                # 滚动到内容区域并等待
                                                scroll_to_element_and_wait(
                                                    driver, content_area, 2
                                                )

                                                # 处理文件名中的特殊字符
                                                # 第506行 - 处理相关情报标签fallback文件名
                                                safe_tab_text = sanitize_filename(
                                                    tab_text
                                                )

                                                # 第519行 - 处理折叠面板标题文件名
                                                safe_title = sanitize_filename(
                                                    clue_title
                                                )

                                                # 第530行 - 处理导航列表错误时的文件名
                                                safe_title = (
                                                    clue_title.replace(" ", "_")
                                                    .replace("/", "_")
                                                    .replace(":", "_")
                                                    .replace("\\", "_")
                                                    .replace("*", "_")
                                                    .replace("?", "_")
                                                    .replace('"', "_")
                                                    .replace("<", "_")
                                                    .replace(">", "_")
                                                    .replace("|", "_")
                                                )

                                                # 第539行 - 处理非相关情报面板的文件名
                                                safe_title = (
                                                    clue_title.replace(" ", "_")
                                                    .replace("/", "_")
                                                    .replace(":", "_")
                                                    .replace("\\", "_")
                                                    .replace("*", "_")
                                                    .replace("?", "_")
                                                    .replace('"', "_")
                                                    .replace("<", "_")
                                                    .replace(">", "_")
                                                    .replace("|", "_")
                                                )
                                                related_screenshot_path = os.path.join(
                                                    pic_output_dir_abs,
                                                    f"{ip_address}_related_{j}_{safe_tab_text}.png",
                                                )
                                                content_area.screenshot(
                                                    related_screenshot_path
                                                )
                                                print(
                                                    f"相关情报标签截图已保存: {related_screenshot_path}"
                                                )

                                                md_content.append(f"#### {tab_text}")
                                                md_content.append(
                                                    f"![{tab_text}](ioc_pic/{ip_address}_related_{j}_{safe_tab_text}.png)\n"
                                                )

                                            except Exception as content_e:
                                                print(
                                                    f"截图标签内容时出错: {content_e}"
                                                )
                                                # 如果找不到内容区域，截图整个面板
                                                safe_tab_text = (
                                                    tab_text.replace(" ", "_")
                                                    .replace("/", "_")
                                                    .replace(":", "_")
                                                    .replace("\\", "_")
                                                    .replace("*", "_")
                                                    .replace("?", "_")
                                                    .replace('"', "_")
                                                    .replace("<", "_")
                                                    .replace(">", "_")
                                                    .replace("|", "_")
                                                )
                                                fallback_screenshot_path = os.path.join(
                                                    pic_output_dir_abs,
                                                    f"{ip_address}_related_{j}_{safe_tab_text}.png",
                                                )
                                                item.screenshot(
                                                    fallback_screenshot_path
                                                )

                                                md_content.append(f"#### {tab_text}")
                                                md_content.append(
                                                    f"![{tab_text}](ioc_pic/{ip_address}_related_{j}_{safe_tab_text}.png)\n"
                                                )

                                        except Exception as tab_e:
                                            print(
                                                f"处理第{j}个相关情报标签时出错: {tab_e}"
                                            )
                                            md_content.append(f"#### 相关情报标签 {j}")
                                            md_content.append(
                                                f"无法获取相关情报标签{j}截图\n"
                                            )
                                else:
                                    # 如果没有标签按钮，按原来的方式截图整个面板
                                    safe_title = (
                                        clue_title.replace("/", "_")
                                        .replace(":", "_")
                                        .replace("\\", "_")
                                        .replace("*", "_")
                                        .replace("?", "_")
                                        .replace('"', "_")
                                        .replace("<", "_")
                                        .replace(">", "_")
                                        .replace("|", "_")
                                    )
                                    collapse_screenshot_path = os.path.join(
                                        pic_output_dir_abs,
                                        f"{domain_name}_collapse_{i}_{safe_title}.png",
                                    )
                                    item.screenshot(collapse_screenshot_path)
                                    print(
                                        f"折叠面板项截图已保存: {collapse_screenshot_path}"
                                    )

                                    md_content.append(f"### {clue_title}")
                                    md_content.append(
                                        f"![{clue_title}](ioc_pic/{domain_name}_collapse_{i}_{safe_title}.png)\n"
                                    )

                            except Exception as nav_e:
                                print(
                                    f"在'{clue_title}'面板中查找导航列表时出错: {nav_e}"
                                )
                                # 如果找不到导航列表，按原来的方式处理
                                safe_title = (
                                    clue_title.replace("/", "_")
                                    .replace(":", "_")
                                    .replace("\\", "_")
                                    .replace("*", "_")
                                    .replace("?", "_")
                                    .replace('"', "_")
                                    .replace("<", "_")
                                    .replace(">", "_")
                                    .replace("|", "_")
                                )
                                collapse_screenshot_path = os.path.join(
                                    pic_output_dir_abs,
                                    f"{ip_address}_collapse_{i}_{safe_title}.png",
                                )
                                item.screenshot(collapse_screenshot_path)
                                print(
                                    f"折叠面板项截图已保存: {collapse_screenshot_path}"
                                )

                                md_content.append(f"### {clue_title}")
                                md_content.append(
                                    f"![{clue_title}](ioc_pic/{ip_address}_collapse_{i}_{safe_title}.png)\n"
                                )
                        else:
                            # 如果不是相关情报面板，按原来的方式处理
                            safe_title = (
                                clue_title.replace("/", "_")
                                .replace(":", "_")
                                .replace("\\", "_")
                                .replace("*", "_")
                                .replace("?", "_")
                                .replace('"', "_")
                                .replace("<", "_")
                                .replace(">", "_")
                                .replace("|", "_")
                            )
                            collapse_screenshot_path = os.path.join(
                                pic_output_dir_abs,
                                f"{ip_address}_collapse_{i}_{safe_title}.png",
                            )
                            item.screenshot(collapse_screenshot_path)
                            print(f"折叠面板项截图已保存: {collapse_screenshot_path}")

                            md_content.append(f"### {clue_title}")
                            md_content.append(
                                f"![{clue_title}](ioc_pic/{ip_address}_collapse_{i}_{safe_title}.png)\n"
                            )

                    except Exception as item_e:
                        print(f"处理第{i}个折叠面板项时出错: {item_e}")
                        md_content.append(f"### 分析项 {i}")
                        md_content.append(f"无法获取分析项{i}截图\n")
            else:
                md_content.append(f"## 详细分析")
                md_content.append(f"未找到折叠面板内容\n")

        except Exception as e:
            print(f"截图折叠面板元素时出错: {e}")
            md_content.append(f"## 详细分析")
            md_content.append(f"无法获取详细分析截图\n")

        # 保存完整页面截图
        try:
            # 滚动到页面顶部
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(2)

            full_page_screenshot_path = os.path.join(
                pic_output_dir_abs, f"{ip_address}_full_page.png"
            )
            driver.save_screenshot(full_page_screenshot_path)
            print(f"完整页面截图已保存: {full_page_screenshot_path}")

            md_content.append(f"## 完整页面")
            md_content.append(f"![完整页面](ioc_pic/{ip_address}_full_page.png)\n")

        except Exception as e:
            print(f"保存完整页面截图时出错: {e}")

        # 保存Markdown报告
        md_filename = f"{ip_address}_分析报告.md"
        md_filepath = os.path.join(output_dir_abs, md_filename)

        with open(md_filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(md_content))
        print(f"分析报告已保存到: {md_filepath}")

        return md_filepath

    except Exception as e:
        error_message = f"在查询 IP {ip_address} 时发生错误: {e}"
        print(error_message)
        return error_message

    finally:
        # 确保浏览器被关闭
        if driver:
            driver.quit()


@mcp.tool()
def query_threatbook_domain_and_save_with_screenshots(domain_name: str) -> str:
    """
    使用 Selenium 打开微步在线（ThreatBook）查询指定域名，并对指定元素进行截图保存。
    截图summary-top、result-intelInsight_con和ant-collapse类元素，并生成分析报告。

    Args:
        domain_name (str): 需要查询的域名。
    """
    # 检查路径是否存在
    if not os.path.exists(CHROME_EXE_PATH):
        return f"错误：Chrome 浏览器路径不存在 -> {CHROME_EXE_PATH}"
    if not os.path.exists(CHROMEDRIVER_EXE_PATH):
        return f"错误：ChromeDriver 路径不存在 -> {CHROMEDRIVER_EXE_PATH}"

    # 配置 Chrome 选项
    chrome_options = Options()
    chrome_options.binary_location = CHROME_EXE_PATH
    user_data_dir_abs = os.path.abspath(USER_DATA_DIR)
    print(f"使用持久化用户数据目录: {user_data_dir_abs}")
    chrome_options.add_argument(f"--user-data-dir={user_data_dir_abs}")
    # chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--window-size=1920,1200")  # 增加窗口高度
    chrome_options.add_argument("--start-maximized")  # 最大化窗口

    # 配置 ChromeDriver 服务
    service = Service(executable_path=CHROMEDRIVER_EXE_PATH)
    driver = None
    try:
        driver = webdriver.Chrome(service=service, options=chrome_options)

        # 设置窗口大小
        driver.set_window_size(1920, 1200)

        url = f"https://x.threatbook.com/v5/domain/{domain_name}"
        print(f"正在访问: {url}")
        driver.get(url)

        print(f"页面加载中，请等待 {PAGE_LOAD_WAIT_SECONDS} 秒...")
        time.sleep(PAGE_LOAD_WAIT_SECONDS)

        # 创建输出目录
        output_dir_abs = os.path.abspath(OUTPUT_DIR)
        pic_output_dir_abs = os.path.abspath(PIC_OUTPUT_DIR)
        os.makedirs(output_dir_abs, exist_ok=True)
        os.makedirs(pic_output_dir_abs, exist_ok=True)

        # 创建Markdown内容
        md_content = []

        md_content.append(f"# 域名分析报告: {domain_name}")
        md_content.append(
            f"\n**分析时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        )

        # 截图summary-top元素
        try:
            summary_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "summary-top"))
            )

            # 滚动到元素并等待
            scroll_to_element_and_wait(driver, summary_element, 2)

            # 截图并保存
            summary_screenshot_path = os.path.join(
                pic_output_dir_abs, f"{domain_name}_summary_top.png"
            )
            summary_element.screenshot(summary_screenshot_path)
            print(f"summary-top元素截图已保存: {summary_screenshot_path}")

            md_content.append(f"## 概要信息")
            md_content.append(f"![概要信息](ioc_pic/{domain_name}_summary_top.png)\n")

        except Exception as e:
            print(f"截图summary-top元素时出错: {e}")
            md_content.append(f"## 概要信息")
            md_content.append(f"无法获取概要信息截图\n")

        # 截图result-intelInsight_con元素
        try:
            insight_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (By.CLASS_NAME, "result-intelInsight_con")
                )
            )

            # 滚动到元素并等待
            scroll_to_element_and_wait(driver, insight_element, 2)

            insight_screenshot_path = os.path.join(
                pic_output_dir_abs, f"{domain_name}_insight.png"
            )
            insight_element.screenshot(insight_screenshot_path)
            print(f"情报洞察元素截图已保存: {insight_screenshot_path}")

            md_content.append(f"## 情报洞察")
            md_content.append(f"![情报洞察](ioc_pic/{domain_name}_insight.png)\n")

        except Exception as e:
            print(f"截图情报洞察元素时出错: {e}")
            md_content.append(f"## 情报洞察")
            md_content.append(f"未找到情报洞察内容\n无法获取情报洞察截图\n")
        # 新增：截图ant-collapse元素
        try:
            collapse_container = driver.find_element(
                By.CSS_SELECTOR,
                ".ant-collapse.ant-collapse-icon-position-start.ant-collapse-ghost",
            )

            # 滚动到折叠容器并等待
            scroll_to_element_and_wait(driver, collapse_container, 2)

            collapse_items = collapse_container.find_elements(
                By.CSS_SELECTOR, ".ant-collapse-item"
            )

            if collapse_items:
                md_content.append(f"## 详细分析")
                print(f"找到 {len(collapse_items)} 个折叠面板项")

                for i, item in enumerate(collapse_items, 1):
                    try:
                        # 获取clue-type标题
                        clue_type_element = item.find_element(
                            By.CLASS_NAME, "clue-type"
                        )
                        clue_title = (
                            clue_type_element.text.strip()
                            if clue_type_element
                            else f"分析项{i}"
                        )
                        print(f"处理折叠面板项: {clue_title}")

                        # 滚动到当前项并等待
                        scroll_to_element_and_wait(driver, item, 2)

                        # 点击展开面板
                        header = item.find_element(
                            By.CSS_SELECTOR, ".ant-collapse-header"
                        )
                        driver.execute_script("arguments[0].click();", header)
                        time.sleep(3)  # 增加等待时间，确保展开动画完成和内容加载

                        # 再次滚动确保完整显示
                        scroll_to_element_and_wait(driver, item, 2)

                        # 检查是否是"相关情报"面板
                        if clue_title == "相关情报":
                            try:
                                # 在当前面板内查找x-comp-nav-list
                                nav_list = item.find_element(
                                    By.CLASS_NAME, "x-comp-nav-list"
                                )
                                print(f"在'{clue_title}'面板中找到导航列表")

                                # 查找所有标签按钮
                                tab_buttons = nav_list.find_elements(
                                    By.CLASS_NAME, "x-comp-tab-btn"
                                )

                                if tab_buttons:
                                    md_content.append(f"### {clue_title}")
                                    print(f"找到 {len(tab_buttons)} 个相关情报标签")

                                    for j, tab_btn in enumerate(tab_buttons, 1):
                                        try:
                                            # 获取标签文本作为标题
                                            tab_text = (
                                                tab_btn.text.strip()
                                                if tab_btn.text
                                                else f"标签{j}"
                                            )
                                            print(f"处理相关情报标签: {tab_text}")

                                            # 滚动到标签并等待
                                            scroll_to_element_and_wait(
                                                driver, tab_btn, 2
                                            )

                                            # 点击标签
                                            driver.execute_script(
                                                "arguments[0].click();", tab_btn
                                            )
                                            time.sleep(3)  # 等待内容加载

                                            # 查找并截图标签内容区域
                                            try:
                                                # 在当前面板内查找内容区域
                                                content_area = item.find_element(
                                                    By.CSS_SELECTOR,
                                                    ".x-comp-tab-content, .tab-content, .related-intel-content",
                                                )

                                                # 滚动到内容区域并等待
                                                scroll_to_element_and_wait(
                                                    driver, content_area, 2
                                                )

                                                # 处理文件名中的特殊字符
                                                # 第220行 - 处理相关情报标签文件名
                                                safe_tab_text = (
                                                    tab_text.replace(" ", "_")
                                                    .replace("/", "_")
                                                    .replace(":", "_")
                                                    .replace("\\", "_")
                                                    .replace("*", "_")
                                                    .replace("?", "_")
                                                    .replace('"', "_")
                                                    .replace("<", "_")
                                                    .replace(">", "_")
                                                    .replace("|", "_")
                                                )

                                                # 第233行 - 处理相关情报标签fallback文件名
                                                safe_tab_text = (
                                                    tab_text.replace(" ", "_")
                                                    .replace("/", "_")
                                                    .replace(":", "_")
                                                    .replace("\\", "_")
                                                    .replace("*", "_")
                                                    .replace("?", "_")
                                                    .replace('"', "_")
                                                    .replace("<", "_")
                                                    .replace(">", "_")
                                                    .replace("|", "_")
                                                )

                                                # 第530行 - 处理导航列表错误时的文件名
                                                safe_title = (
                                                    clue_title.replace(" ", "_")
                                                    .replace("/", "_")
                                                    .replace(":", "_")
                                                    .replace("\\", "_")
                                                    .replace("*", "_")
                                                    .replace("?", "_")
                                                    .replace('"', "_")
                                                    .replace("<", "_")
                                                    .replace(">", "_")
                                                    .replace("|", "_")
                                                )

                                                # 第539行 - 处理非相关情报面板的文件名
                                                safe_title = (
                                                    clue_title.replace(" ", "_")
                                                    .replace("/", "_")
                                                    .replace(":", "_")
                                                    .replace("\\", "_")
                                                    .replace("*", "_")
                                                    .replace("?", "_")
                                                    .replace('"', "_")
                                                    .replace("<", "_")
                                                    .replace(">", "_")
                                                    .replace("|", "_")
                                                )
                                                related_screenshot_path = os.path.join(
                                                    pic_output_dir_abs,
                                                    f"{domain_name}_related_{j}_{safe_tab_text}.png",
                                                )
                                                content_area.screenshot(
                                                    related_screenshot_path
                                                )
                                                print(
                                                    f"相关情报标签截图已保存: {related_screenshot_path}"
                                                )

                                                md_content.append(f"#### {tab_text}")
                                                md_content.append(
                                                    f"![{tab_text}](ioc_pic/{domain_name}_related_{j}_{safe_tab_text}.png)\n"
                                                )

                                            except Exception as content_e:
                                                print(
                                                    f"截图标签内容时出错: {content_e}"
                                                )
                                                # 如果找不到内容区域，截图整个面板
                                                safe_tab_text = (
                                                    tab_text.replace(" ", "_")
                                                    .replace("/", "_")
                                                    .replace(":", "_")
                                                    .replace("\\", "_")
                                                    .replace("*", "_")
                                                    .replace("?", "_")
                                                    .replace('"', "_")
                                                    .replace("<", "_")
                                                    .replace(">", "_")
                                                    .replace("|", "_")
                                                )
                                                fallback_screenshot_path = os.path.join(
                                                    pic_output_dir_abs,
                                                    f"{domain_name}_related_{j}_{safe_tab_text}.png",
                                                )
                                                item.screenshot(
                                                    fallback_screenshot_path
                                                )

                                                md_content.append(f"#### {tab_text}")
                                                md_content.append(
                                                    f"![{tab_text}](ioc_pic/{domain_name}_related_{j}_{safe_tab_text}.png)\n"
                                                )

                                        except Exception as tab_e:
                                            print(
                                                f"处理第{j}个相关情报标签时出错: {tab_e}"
                                            )
                                            md_content.append(f"#### 相关情报标签 {j}")
                                            md_content.append(
                                                f"无法获取相关情报标签{j}截图\n"
                                            )
                                else:
                                    # 如果没有标签按钮，按原来的方式截图整个面板
                                    safe_title = (
                                        clue_title.replace("/", "_")
                                        .replace(":", "_")
                                        .replace("\\", "_")
                                        .replace("*", "_")
                                        .replace("?", "_")
                                        .replace('"', "_")
                                        .replace("<", "_")
                                        .replace(">", "_")
                                        .replace("|", "_")
                                    )
                                    collapse_screenshot_path = os.path.join(
                                        pic_output_dir_abs,
                                        f"{domain_name}_collapse_{i}_{safe_title}.png",
                                    )
                                    item.screenshot(collapse_screenshot_path)
                                    print(
                                        f"折叠面板项截图已保存: {collapse_screenshot_path}"
                                    )

                                    md_content.append(f"### {clue_title}")
                                    md_content.append(
                                        f"![{clue_title}](ioc_pic/{domain_name}_collapse_{i}_{safe_title}.png)\n"
                                    )

                            except Exception as nav_e:
                                print(
                                    f"在'{clue_title}'面板中查找导航列表时出错: {nav_e}"
                                )
                                # 如果找不到导航列表，按原来的方式处理
                                safe_title = (
                                    clue_title.replace("/", "_")
                                    .replace(":", "_")
                                    .replace("\\", "_")
                                    .replace("*", "_")
                                    .replace("?", "_")
                                    .replace('"', "_")
                                    .replace("<", "_")
                                    .replace(">", "_")
                                    .replace("|", "_")
                                )
                                collapse_screenshot_path = os.path.join(
                                    pic_output_dir_abs,
                                    f"{domain_name}_collapse_{i}_{safe_title}.png",
                                )
                                item.screenshot(collapse_screenshot_path)
                                print(
                                    f"折叠面板项截图已保存: {collapse_screenshot_path}"
                                )

                                md_content.append(f"### {clue_title}")
                                md_content.append(
                                    f"![{clue_title}](ioc_pic/{domain_name}_collapse_{i}_{safe_title}.png)\n"
                                )
                        else:
                            # 如果不是相关情报面板，按原来的方式处理
                            safe_title = (
                                clue_title.replace("/", "_")
                                .replace(":", "_")
                                .replace("\\", "_")
                                .replace("*", "_")
                                .replace("?", "_")
                                .replace('"', "_")
                                .replace("<", "_")
                                .replace(">", "_")
                                .replace("|", "_")
                            )
                            collapse_screenshot_path = os.path.join(
                                pic_output_dir_abs,
                                f"{domain_name}_collapse_{i}_{safe_title}.png",
                            )
                            item.screenshot(collapse_screenshot_path)
                            print(f"折叠面板项截图已保存: {collapse_screenshot_path}")

                            md_content.append(f"### {clue_title}")
                            md_content.append(
                                f"![{clue_title}](ioc_pic/{domain_name}_collapse_{i}_{safe_title}.png)\n"
                            )

                    except Exception as item_e:
                        print(f"处理第{i}个折叠面板项时出错: {item_e}")
                        md_content.append(f"### 分析项 {i}")
                        md_content.append(f"无法获取分析项{i}截图\n")
            else:
                md_content.append(f"## 详细分析")
                md_content.append(f"未找到折叠面板内容\n")

        except Exception as e:
            print(f"截图折叠面板元素时出错: {e}")
            md_content.append(f"## 详细分析")
            md_content.append(f"无法获取详细分析截图\n")

        # 保存完整页面截图
        try:
            # 滚动到页面顶部
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(2)

            full_page_screenshot_path = os.path.join(
                pic_output_dir_abs, f"{domain_name}_full_page.png"
            )
            driver.save_screenshot(full_page_screenshot_path)
            print(f"完整页面截图已保存: {full_page_screenshot_path}")

            md_content.append(f"## 完整页面")
            md_content.append(f"![完整页面](ioc_pic/{domain_name}_full_page.png)\n")

        except Exception as e:
            print(f"保存完整页面截图时出错: {e}")

        # 保存Markdown报告
        md_filename = f"{domain_name}_分析报告.md"
        md_filepath = os.path.join(output_dir_abs, md_filename)

        with open(md_filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(md_content))
        print(f"分析报告已保存到: {md_filepath}")

        return md_filepath

    except Exception as e:
        error_message = f"在查询域名 {domain_name} 时发生错误: {e}"
        print(error_message)
        return error_message

    finally:
        if driver:
            driver.quit()


# --- 主程序入口，用于直接运行测试 ---
if __name__ == "__main__":

    mcp.run(transport="stdio")
    # print("--- 开始测试域名查询（截图版本）---")
    # domain_to_query = "db.testyk.com"
    # domain_result_path = query_threatbook_domain_and_save_with_screenshots(
    #     domain_to_query
    # )

    # if domain_result_path and domain_result_path.endswith(".md"):
    #     print(f"\n域名查询任务完成！分析报告已保存在: {domain_result_path}")
    # else:
    #     print(f"\n域名查询任务失败: {domain_result_path}")
