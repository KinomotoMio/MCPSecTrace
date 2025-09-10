# -*- coding: utf-8 -*-
"""
配置系统使用示例

演示如何在MCP服务器中使用新的分层配置系统
"""

from mcpsectrace.config import get_config, get_config_value

def example_browser_forensics_config():
    """浏览器取证配置使用示例"""
    
    # 方式1：获取特定模块的完整配置
    browser_config = get_config("browser")
    max_history = browser_config.get("browser", {}).get("max_history_items", 100)
    
    # 方式2：直接获取配置值（推荐）
    max_history = get_config_value("browser.max_history_items", default=100)
    max_downloads = get_config_value("browser.max_download_items", default=50)
    
    print(f"最大历史记录数: {max_history}")
    print(f"最大下载记录数: {max_downloads}")
    
    # 获取SQL模板
    history_sql = get_config_value("browser.sql_templates.history", config_name="browser")
    print(f"历史记录SQL: {history_sql}")

def example_ioc_config():
    """威胁情报查询配置使用示例"""
    
    # 获取浏览器窗口尺寸
    window_size = get_config_value("ioc.window_size", default=[1920, 1200])
    
    # 获取等待时间配置
    scroll_wait = get_config_value("ioc.scroll_wait_time", default=2)
    
    # 获取Chrome启动选项
    chrome_options = get_config_value("ioc.chrome_options", default=[])
    
    print(f"窗口尺寸: {window_size}")
    print(f"滚动等待时间: {scroll_wait}秒")
    print(f"Chrome选项: {chrome_options}")

def example_automation_config():
    """GUI自动化配置使用示例"""
    
    # 获取重试次数
    retry_times = get_config_value("automation.retry_times", default=3)
    
    # 获取设备性能等级（来自用户配置）
    device_level = get_config_value("device_level", default=2)
    
    # 获取图像文件配置
    huorong_images = get_config_value("automation.image_files.huorong", default={})
    
    print(f"重试次数: {retry_times}")
    print(f"设备性能等级: {device_level}")
    print(f"火绒图像文件: {huorong_images}")

def example_user_override():
    """演示用户配置覆盖默认配置"""
    
    # 用户可以在user_settings.toml中设置device_level = 1覆盖默认值
    device_level = get_config_value("device_level", default=2)
    
    # 根据设备等级调整等待时间
    base_sleep = get_config_value("automation.sleep_short_base", default=1)
    actual_sleep = base_sleep * device_level
    
    print(f"设备等级: {device_level}")
    print(f"实际短等待时间: {actual_sleep}秒")

if __name__ == "__main__":
    print("=== 浏览器取证配置示例 ===")
    example_browser_forensics_config()
    
    print("\n=== 威胁情报配置示例 ===") 
    example_ioc_config()
    
    print("\n=== GUI自动化配置示例 ===")
    example_automation_config()
    
    print("\n=== 用户覆盖配置示例 ===")
    example_user_override()