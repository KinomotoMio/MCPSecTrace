# -*- coding: utf-8 -*-
"""
MCPSecTrace 配置管理模块

提供分层TOML配置系统，支持用户配置、自定义配置和系统默认配置的自动合并。

基本使用方法:
    from mcpsectrace.config import get_config, get_config_value

    # 获取所有配置
    config = get_config()

    # 获取特定模块配置
    browser_config = get_config("browser")

    # 获取特定配置值
    max_items = get_config_value("browser.max_history_items", default=100)
"""

from .loader import ConfigLoader, get_config_loader, get_config, get_config_value

__all__ = ["ConfigLoader", "get_config_loader", "get_config", "get_config_value"]
