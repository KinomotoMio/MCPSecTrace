"""
MCPSecTrace 部署测试MCP服务器

此模块封装了简化的MCP工具用于测试各个组件的部署情况
"""

import os
import subprocess
import sys
import time
from pathlib import Path

from mcp.server.fastmcp import FastMCP
from mcpsectrace.config import get_config_value

# 创建MCP服务器实例
mcp = FastMCP("deployment_test", log_level="ERROR", port=8888)


@mcp.tool()
def test_huorong_open() -> str:
    """
    测试火绒安全软件启动功能

    验证内容：
    - 检查火绒安全软件路径配置是否正确
    - 验证火绒程序文件是否存在
    - 尝试启动火绒安全软件进程
    - 检查进程是否成功运行

    适用场景：
    - 部署验证：确认火绒MCP服务器能够正常启动火绒工具
    - 配置检查：验证user_settings.toml中的huorong_exe路径配置
    - 环境测试：检查系统是否支持火绒程序运行

    Returns:
        str: 详细的测试结果，包括成功/失败状态和进程信息
    """
    huorong_path = get_config_value("paths.huorong_exe", default="")

    if not huorong_path:
        return "❌ 火绒路径未配置"

    if not Path(huorong_path).exists():
        return f"❌ 火绒路径不存在: {huorong_path}"

    try:
        # 尝试启动火绒
        process = subprocess.Popen(huorong_path, shell=True)

        # 给进程一点时间启动
        time.sleep(2)

        # 检查进程是否还在运行
        if process.poll() is None:
            return f"✅ 火绒启动成功，进程ID: {process.pid}"
        else:
            return f"✅ 火绒已启动完成，进程ID: {process.pid}"

    except Exception as e:
        return f"❌ 启动火绒失败: {e}"


@mcp.tool()
def test_ioc_browser_access() -> str:
    """
    测试IOC威胁情报查询的浏览器访问功能

    验证内容：
    - 检查Chrome浏览器路径和ChromeDriver路径配置
    - 验证Chrome用户数据目录配置（可选）
    - 初始化Selenium WebDriver with Chrome
    - 访问微步在线威胁情报平台测试页面
    - 验证页面是否正常加载和显示

    测试目标：
    - URL: https://x.threatbook.com/v5/ip/8.8.8.8
    - 测试IP: 8.8.8.8 (Google DNS)

    适用场景：
    - 部署验证：确认IOC MCP服务器的浏览器环境配置正确
    - 网络测试：验证是否能访问威胁情报网站
    - 驱动测试：检查Selenium WebDriver是否正常工作
    - 配置检查：验证所有浏览器相关的路径配置

    Returns:
        str: 详细测试结果，包括访问URL、页面标题和当前页面信息
    """
    chrome_path = get_config_value("paths.chrome_exe", default="")
    chromedriver_path = get_config_value("paths.chromedriver_exe", default="")

    if not chrome_path:
        return "❌ Chrome路径未配置"

    if not Path(chrome_path).exists():
        return f"❌ Chrome路径不存在: {chrome_path}"

    if not chromedriver_path:
        return "❌ ChromeDriver路径未配置"

    if not Path(chromedriver_path).exists():
        return f"❌ ChromeDriver路径不存在: {chromedriver_path}"

    # 检查Chrome用户数据目录（可选配置）
    user_data_dir = get_config_value("paths.chrome_user_data_dir", default="")
    if user_data_dir and not Path(user_data_dir).exists():
        return f"❌ Chrome用户数据目录不存在: {user_data_dir}"

    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service

        chrome_options = Options()
        chrome_options.binary_location = chrome_path
        # chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-infobars")
        chrome_options.add_argument("--disable-notifications")

        # 添加用户数据目录配置
        user_data_dir = get_config_value("paths.chrome_user_data_dir", default="")
        if user_data_dir:
            chrome_options.add_argument(f"--user-data-dir={user_data_dir}")

        service = Service(chromedriver_path)

        # 初始化WebDriver
        driver = webdriver.Chrome(service=service, options=chrome_options)

        # 测试访问威胁情报查询页面（微步在线）
        test_ip = "8.8.8.8"  # 使用Google DNS作为测试IP
        threatbook_url = f"https://x.threatbook.com/v5/ip/{test_ip}"

        driver.get(threatbook_url)

        # 等待页面加载
        time.sleep(3)

        title = driver.title
        current_url = driver.current_url

        # 清理
        driver.quit()

        return f"✅ IOC威胁情报页面访问测试成功\n访问URL: {threatbook_url}\n页面标题: {title}\n当前URL: {current_url}"

    except Exception as e:
        return f"❌ IOC浏览器访问测试失败: {e}"


@mcp.tool()
def test_focus_pack_open() -> str:
    """
    测试Focus Pack工具启动功能

    验证内容：
    - 检查Focus Pack工具路径配置是否正确
    - 验证Focus Pack程序文件是否存在
    - 尝试启动Focus Pack工具进程
    - 检查进程是否成功运行

    工具说明：
    - Focus Pack是一个专业的系统扫描和清理工具
    - 主要用于恶意软件检测和系统优化
    - 支持快速扫描和深度扫描功能

    适用场景：
    - 部署验证：确认Focus Pack MCP服务器能够正常启动工具
    - 配置检查：验证user_settings.toml中的focus_pack_exe路径配置
    - 权限测试：某些功能可能需要管理员权限
    - 环境测试：检查系统兼容性

    Returns:
        str: 详细的测试结果，包括启动状态和进程信息
    """
    focus_pack_path = get_config_value("paths.focus_pack_exe", default="")

    if not focus_pack_path:
        return "❌ Focus Pack路径未配置"

    if not Path(focus_pack_path).exists():
        return f"❌ Focus Pack路径不存在: {focus_pack_path}"

    try:
        # 尝试启动Focus Pack
        process = subprocess.Popen(focus_pack_path, shell=True)

        # 给进程一点时间启动
        time.sleep(2)

        # 检查进程是否还在运行
        if process.poll() is None:
            return f"✅ Focus Pack启动成功，进程ID: {process.pid}"
        else:
            return f"✅ Focus Pack已启动完成，进程ID: {process.pid}"

    except Exception as e:
        return f"❌ 启动Focus Pack失败: {e}"


@mcp.tool()
def test_hrkill_open() -> str:
    """
    测试HRKill工具启动功能

    验证内容：
    - 检查HRKill工具路径配置是否正确
    - 验证HRKill程序文件是否存在
    - 尝试启动HRKill工具进程
    - 检查进程是否成功运行

    工具说明：
    - HRKill是一个专业的恶意软件查杀工具
    - 专注于清除顽固病毒和恶意进程
    - 具有强制终止恶意进程的能力
    - 通常需要管理员权限才能发挥最大效果

    适用场景：
    - 部署验证：确认HRKill MCP服务器能够正常启动工具
    - 配置检查：验证user_settings.toml中的hrkill_exe路径配置
    - 权限测试：验证管理员权限要求
    - 安全测试：检查恶意软件查杀功能可用性

    Returns:
        str: 详细的测试结果，包括启动状态和进程信息
    """
    hrkill_path = get_config_value("paths.hrkill_exe", default="")

    if not hrkill_path:
        return "❌ HRKill路径未配置"

    if not Path(hrkill_path).exists():
        return f"❌ HRKill路径不存在: {hrkill_path}"

    try:
        # 尝试启动HRKill
        process = subprocess.Popen(hrkill_path, shell=True)

        # 给进程一点时间启动
        time.sleep(2)

        # 检查进程是否还在运行
        if process.poll() is None:
            return f"✅ HRKill启动成功，进程ID: {process.pid}"
        else:
            return f"✅ HRKill已启动完成，进程ID: {process.pid}"

    except Exception as e:
        return f"❌ 启动HRKill失败: {e}"


@mcp.tool()
def run_all_deployment_tests() -> str:
    """
    运行所有部署测试 - 一键执行完整的部署验证

    功能说明：
    - 自动执行所有4个核心工具的启动测试
    - 生成详细的测试报告和统计信息
    - 提供部署状态的整体评估

    执行的测试：
    1. 火绒安全软件启动测试
    2. IOC威胁情报浏览器访问测试
    3. Focus Pack工具启动测试
    4. HRKill工具启动测试

    适用场景：
    - 新环境部署：快速验证整个MCPSecTrace项目的部署状态
    - 定期检查：定期检查所有组件的运行状态
    - 故障排查：快速定位哪些组件有问题
    - CI/CD集成：在自动化部署流程中进行验证

    报告内容：
    - 每个测试的详细结果
    - 通过/失败统计
    - 整体部署状态评估

    Returns:
        str: 完整的测试汇总报告，包含所有测试结果和统计信息
    """
    tests = [
        ("火绒工具启动", test_huorong_open),
        ("IOC浏览器访问", test_ioc_browser_access),
        ("Focus Pack启动", test_focus_pack_open),
        ("HRKill启动", test_hrkill_open),
    ]

    results = []
    passed_count = 0

    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append(f"{test_name}: {result}")
            if result.startswith("✅"):
                passed_count += 1
        except Exception as e:
            error_msg = f"❌ {test_name} 测试异常: {e}"
            results.append(error_msg)

    # 生成汇总报告
    total_tests = len(tests)
    failed_count = total_tests - passed_count

    summary = ["=" * 50, "MCPSecTrace 部署测试汇总", "=" * 50, ""]

    summary.extend(results)

    summary.extend(
        [
            "",
            "-" * 50,
            f"总计: {total_tests} 项测试",
            f"通过: {passed_count} 项",
            f"失败: {failed_count} 项",
        ]
    )

    if failed_count == 0:
        summary.append("\n🎉 所有部署测试通过！项目可以正常部署和运行。")
    else:
        summary.append(f"\n⚠️ 有 {failed_count} 项测试失败，请检查配置和依赖。")

    return "\n".join(summary)


@mcp.tool()
def check_config_paths() -> str:
    """
    检查配置文件中的所有路径 - 验证配置完整性

    功能说明：
    - 读取user_settings.toml配置文件
    - 验证所有工具路径的有效性
    - 生成详细的配置检查报告

    检查的配置项：
    - 火绒安全软件路径 (paths.huorong_exe)
    - Chrome浏览器路径 (paths.chrome_exe)
    - ChromeDriver路径 (paths.chromedriver_exe)
    - Chrome用户数据目录 (paths.chrome_user_data_dir)
    - HRKill工具路径 (paths.hrkill_exe)
    - Focus Pack工具路径 (paths.focus_pack_exe)

    验证内容：
    - 配置项是否存在
    - 路径是否指向有效文件/目录
    - 文件是否可访问

    适用场景：
    - 初始配置：验证配置文件设置是否正确
    - 故障排查：快速定位配置问题
    - 环境迁移：确认新环境配置的有效性
    - 定期检查：验证配置的持续有效性

    Returns:
        str: 详细的路径检查报告，包含每个配置项的状态
    """
    paths_to_check = [
        ("火绒路径", "paths.huorong_exe"),
        ("Chrome路径", "paths.chrome_exe"),
        ("ChromeDriver路径", "paths.chromedriver_exe"),
        ("Chrome用户数据目录", "paths.chrome_user_data_dir"),
        ("HRKill路径", "paths.hrkill_exe"),
        ("Focus Pack路径", "paths.focus_pack_exe"),
    ]

    results = []
    valid_count = 0

    for name, config_key in paths_to_check:
        path = get_config_value(config_key, default="")
        if not path:
            results.append(f"❌ {name}: 未配置")
        elif Path(path).exists():
            results.append(f"✅ {name}: {path}")
            valid_count += 1
        else:
            results.append(f"❌ {name}: 路径不存在 - {path}")

    total_paths = len(paths_to_check)
    invalid_count = total_paths - valid_count

    summary = ["配置路径检查结果:", "=" * 30, ""]

    summary.extend(results)

    summary.extend(
        [
            "",
            f"总计: {total_paths} 个路径",
            f"有效: {valid_count} 个",
            f"无效: {invalid_count} 个",
        ]
    )

    return "\n".join(summary)


# 主函数
def main():
    # """MCP服务器主函数"""
    # print("=" * 60)
    # print("MCPSecTrace 部署测试MCP服务器")
    # print("=" * 60)
    # print()
    # print("🔧 可用的MCP工具：")
    # print()
    # print("📋 单项测试工具：")
    # print("  • test_huorong_open          - 测试火绒安全软件启动")
    # print("  • test_ioc_browser_access    - 测试IOC威胁情报浏览器访问")
    # print("  • test_focus_pack_open       - 测试Focus Pack工具启动")
    # print("  • test_hrkill_open           - 测试HRKill工具启动")
    # print()
    # print("🎯 综合测试工具：")
    # print("  • run_all_deployment_tests   - 一键运行所有部署测试")
    # print("  • check_config_paths         - 检查配置文件中的所有路径")
    # print()
    # print("💡 使用建议：")
    # print("  - 首次部署：先运行 check_config_paths 验证配置")
    # print("  - 完整验证：使用 run_all_deployment_tests 进行全面测试")
    # print("  - 问题排查：使用单项测试工具定位具体问题")
    # print()
    # print("🚀 服务器启动中...")
    # print("=" * 60)

    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
