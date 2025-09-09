import os
from functools import lru_cache

try:
    import tomllib  # Python 3.11+
except Exception as _e:  # pragma: no cover
    tomllib = None  # type: ignore


@lru_cache(maxsize=1)
def get_settings() -> dict:
    """
    加载 config/settings.toml 并缓存结果。
    优先使用标准库 tomllib；若不可用，请安装 tomlkit 或 tomli 并在此处替换。
    """
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    config_path = os.path.join(project_root, "config", "settings.toml")
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"未找到配置文件: {config_path}")

    if tomllib is None:
        raise RuntimeError("当前 Python 缺少 tomllib，请使用 Python 3.11+ 或安装 tomli")

    with open(config_path, "rb") as f:
        data = tomllib.load(f)
    return data
