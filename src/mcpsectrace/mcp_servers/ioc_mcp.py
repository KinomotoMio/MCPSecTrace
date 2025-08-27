import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from mcp.server.fastmcp import FastMCP

# ==============================================================================
# ---                           CONFIGURATION                            ---
# ==============================================================================
# 请在此处修改所有路径和设置

# Chrome 和 ChromeDriver 的可执行文件路径
CHROME_EXE_PATH = r"D:\OneDrive\NDSS\Selenium_gpt\chrome-win64\chrome.exe"
CHROMEDRIVER_EXE_PATH = (
    r"D:\OneDrive\NDSS\Selenium_gpt\chromedriver-win64\chromedriver.exe"
)

# 持久化的用户数据目录路径
# 指定一个Chrome用户配置文件夹，脚本将加载并使用其中的Cookies、会话等信息。
# 如果想从一个全新的状态开始，可以指向一个空文件夹。
USER_DATA_DIR = r"C:\Users\Sssu\AppData\Local\Google\Chrome for Testing\User Data"

# 页面加载等待时间（秒）
PAGE_LOAD_WAIT_SECONDS = 10

# 结果输出目录，将结果保存在指定的子文件夹中
OUTPUT_DIR = "src/mcpsectrace/mcp_servers/logs/ioc"

# ==============================================================================

mcp = FastMCP("ioc", log_level="ERROR", port=8888)


@mcp.tool()
def query_threatbook_ip_and_save(ip_address: str) -> str:
    """
    使用 Selenium 打开微步在线（ThreatBook）查询指定 IP，并保存完整的 HTML 页面。
    此版本会使用持久化的用户数据目录来保留会话信息（如 Cookies）。

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

    # 其他浏览器选项
    # chrome_options.add_argument("--headless")  # 如果需要后台运行，请取消此行注释
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--window-size=1920x1080")

    # 配置 ChromeDriver 服务
    service = Service(executable_path=CHROMEDRIVER_EXE_PATH)

    driver = None
    try:
        # 初始化 WebDriver
        driver = webdriver.Chrome(service=service, options=chrome_options)

        url = f"https://x.threatbook.com/v5/ip/{ip_address}"
        print(f"正在访问: {url}")
        driver.get(url)

        # 使用配置区的等待时间
        print(f"页面加载中，请等待 {PAGE_LOAD_WAIT_SECONDS} 秒...")
        time.sleep(PAGE_LOAD_WAIT_SECONDS)

        page_content = driver.page_source
        # 定义输出文件名
        output_filename = f"{ip_address}.html"

        # 获取输出目录的绝对路径
        output_dir_abs = os.path.abspath(OUTPUT_DIR)

        # 确保输出目录存在，如果不存在则递归创建
        os.makedirs(output_dir_abs, exist_ok=True)
        # 使用 os.path.join 来构建跨平台兼容的完整文件路径
        output_filepath = os.path.join(output_dir_abs, output_filename)

        with open(output_filepath, "w", encoding="utf-8") as f:
            f.write(page_content)

        print(f"页面已成功保存到: {output_filepath}")
        return output_filepath

    except Exception as e:
        error_message = f"在查询 IP {ip_address} 时发生错误: {e}"
        print(error_message)
        return error_message

    finally:
        # 确保浏览器被关闭
        if driver:
            driver.quit()


@mcp.tool()
def query_threatbook_domain_and_save(domain_name: str) -> str:
    """
    使用 Selenium 打开微步在线（ThreatBook）查询指定域名，并保存完整的 HTML 页面。
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
    chrome_options.add_argument("--window-size=1920x1080")

    # 配置 ChromeDriver 服务
    service = Service(executable_path=CHROMEDRIVER_EXE_PATH)
    driver = None
    try:
        driver = webdriver.Chrome(service=service, options=chrome_options)

        # 【修改】URL 变更为 domain 查询
        url = f"https://x.threatbook.com/v5/domain/{domain_name}"
        print(f"正在访问: {url}")
        driver.get(url)

        print(f"页面加载中，请等待 {PAGE_LOAD_WAIT_SECONDS} 秒...")
        time.sleep(PAGE_LOAD_WAIT_SECONDS)

        page_content = driver.page_source

        # 【修改】文件名以 domain 命名
        output_filename = f"{domain_name}.html"
        output_dir_abs = os.path.abspath(OUTPUT_DIR)
        os.makedirs(output_dir_abs, exist_ok=True)
        output_filepath = os.path.join(output_dir_abs, output_filename)

        with open(output_filepath, "w", encoding="utf-8") as f:
            f.write(page_content)

        print(f"页面已成功保存到: {output_filepath}")
        return output_filepath

    except Exception as e:
        # 【修改】错误信息变更为 domain
        error_message = f"在查询域名 {domain_name} 时发生错误: {e}"
        print(error_message)
        return error_message

    finally:
        if driver:
            driver.quit()


# --- 主程序入口，用于直接运行测试 ---
if __name__ == "__main__":

    #     print("--- 开始测试 IP 查询 ---")
    #     ip_to_query = "1.1.1.1"
    #     ip_result_path = query_threatbook_ip_and_save(ip_to_query)

    #     if ip_result_path and ip_result_path.endswith(".html"):
    #         print(f"\nIP 查询任务完成！文件已保存在: {ip_result_path}\n")
    #     else:
    #         print(f"\nIP 查询任务失败: {ip_result_path}\n")

    print("--- 开始测试域名查询 ---")
    domain_to_query = "db.testyk.com"
    domain_result_path = query_threatbook_domain_and_save(domain_to_query)

    if domain_result_path and domain_result_path.endswith(".html"):
        print(f"\n域名查询任务完成！文件已保存在: {domain_result_path}")
    else:
        print(f"\n域名查询任务失败: {domain_result_path}")
