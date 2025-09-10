# -*- coding: utf-8 -*-
"""
配置加载器模块

提供分层TOML配置系统，支持：
- 用户核心配置 (user_settings.toml)
- 自定义默认配置 (custom/*.toml)
- 系统默认配置 (defaults/*.toml)

优先级: 用户配置 > 自定义配置 > 系统默认配置
"""
import os
import tomllib
from pathlib import Path
from typing import Dict, Any
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)


class ConfigLoader:
    """配置加载器"""

    def __init__(self, project_root: str = None):
        """
        初始化配置加载器

        Args:
            project_root: 项目根目录，默认自动检测
        """
        if project_root is None:
            # 自动检测项目根目录（查找pyproject.toml）
            current_dir = Path(__file__).parent
            while current_dir != current_dir.parent:
                if (current_dir / "pyproject.toml").exists():
                    project_root = str(current_dir)
                    break
                current_dir = current_dir.parent
            else:
                raise RuntimeError("无法找到项目根目录（缺少pyproject.toml）")

        self.project_root = Path(project_root)
        self.config_dir = self.project_root / "config"
        self._config_cache = {}

    @lru_cache(maxsize=32)
    def load_config(self, config_name: str = None) -> Dict[str, Any]:
        """
        加载分层配置

        Args:
            config_name: 配置名称（对应defaults/下的文件名），None表示加载所有配置

        Returns:
            合并后的配置字典
        """
        if config_name is None:
            # 加载所有配置
            return self._load_all_configs()
        else:
            # 加载指定配置
            return self._load_specific_config(config_name)

    def _load_all_configs(self) -> Dict[str, Any]:
        """加载并合并所有配置"""
        merged_config = {}

        # 1. 加载系统默认配置
        defaults_dir = self.config_dir / "defaults"
        if defaults_dir.exists():
            for toml_file in defaults_dir.glob("*.toml"):
                config_data = self._load_toml_file(toml_file)
                merged_config = self._deep_merge(merged_config, config_data)

        # 2. 加载自定义配置（覆盖对应的默认配置）
        custom_dir = self.config_dir / "custom"
        if custom_dir.exists():
            for toml_file in custom_dir.glob("*.toml"):
                config_data = self._load_toml_file(toml_file)
                merged_config = self._deep_merge(merged_config, config_data)

        # 3. 加载用户核心配置（最高优先级）
        user_config_file = self.config_dir / "user_settings.toml"
        if user_config_file.exists():
            user_config = self._load_toml_file(user_config_file)
            merged_config = self._deep_merge(merged_config, user_config)

        return merged_config

    def _load_specific_config(self, config_name: str) -> Dict[str, Any]:
        """加载指定配置模块"""
        config_data = {}

        # 1. 加载系统默认配置
        default_file = self.config_dir / "defaults" / f"{config_name}.toml"
        if default_file.exists():
            config_data = self._load_toml_file(default_file)

        # 2. 加载自定义配置（覆盖默认）
        custom_file = self.config_dir / "custom" / f"{config_name}.toml"
        if custom_file.exists():
            custom_config = self._load_toml_file(custom_file)
            config_data = self._deep_merge(config_data, custom_config)

        # 3. 从用户核心配置中提取相关部分
        user_config_file = self.config_dir / "user_settings.toml"
        if user_config_file.exists():
            user_config = self._load_toml_file(user_config_file)
            # 根据配置名称提取相关配置
            relevant_user_config = self._extract_relevant_user_config(
                user_config, config_name
            )
            config_data = self._deep_merge(config_data, relevant_user_config)

        return config_data

    def _load_toml_file(self, file_path: Path) -> Dict[str, Any]:
        """加载单个TOML文件"""
        try:
            with open(file_path, "rb") as f:
                return tomllib.load(f)
        except Exception as e:
            logger.warning(f"加载配置文件失败: {file_path}, 错误: {e}")
            return {}

    def _deep_merge(
        self, base: Dict[str, Any], update: Dict[str, Any]
    ) -> Dict[str, Any]:
        """深度合并字典"""
        result = base.copy()

        for key, value in update.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value

        return result

    def _extract_relevant_user_config(
        self, user_config: Dict[str, Any], config_name: str
    ) -> Dict[str, Any]:
        """从用户配置中提取与指定配置模块相关的部分"""
        relevant_config = {}

        # 简单的映射规则，可以根据需要扩展
        config_mappings = {
            "browser": ["browser_settings", "forensics"],
            "ioc": ["threat_intel", "ioc_settings", "chrome"],
            "automation": ["gui", "automation", "device_level"],
            "base": ["system", "paths", "output"],
        }

        if config_name in config_mappings:
            for key in config_mappings[config_name]:
                if key in user_config:
                    relevant_config[key] = user_config[key]

        return relevant_config

    def get_config_value(self, key_path: str, default=None, config_name: str = None):
        """
        获取配置值，支持点号分隔的路径

        Args:
            key_path: 配置路径，如 "browser.max_history_items"
            default: 默认值
            config_name: 配置模块名，None表示从全局配置查找

        Returns:
            配置值
        """
        config = self.load_config(config_name)

        # 按路径查找配置值
        keys = key_path.split(".")
        value = config

        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default

    def reload_config(self):
        """清除缓存，重新加载配置"""
        self._config_cache.clear()
        self.load_config.cache_clear()


# 全局配置加载器实例（延迟初始化）
_config_loader = None


def get_config_loader() -> ConfigLoader:
    """获取全局配置加载器实例"""
    global _config_loader
    if _config_loader is None:
        _config_loader = ConfigLoader()
    return _config_loader


def get_config(config_name: str = None) -> Dict[str, Any]:
    """便捷函数：获取配置"""
    return get_config_loader().load_config(config_name)


def get_config_value(key_path: str, default=None, config_name: str = None):
    """便捷函数：获取配置值"""
    return get_config_loader().get_config_value(key_path, default, config_name)
