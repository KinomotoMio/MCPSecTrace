"""
统一的日志配置工具
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

def setup_logger(
    name: str,
    log_file: Optional[str] = None,
    level: int = logging.INFO,
    format_string: Optional[str] = None
) -> logging.Logger:
    """
    设置统一的日志记录器
    
    Args:
        name: 日志记录器名称
        log_file: 日志文件路径（可选）
        level: 日志级别
        format_string: 自定义格式字符串
    
    Returns:
        配置好的日志记录器
    """
    
    if format_string is None:
        format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    formatter = logging.Formatter(format_string)
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 避免重复添加处理器
    if logger.handlers:
        return logger
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 文件处理器（如果指定了日志文件）
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_path, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def get_timestamped_filename(prefix: str, extension: str = "log") -> str:
    """
    生成带时间戳的文件名
    
    Args:
        prefix: 文件名前缀
        extension: 文件扩展名
    
    Returns:
        带时间戳的文件名
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{timestamp}.{extension}"

def setup_mcp_logger(mcp_name: str, logs_dir: str = "data/logs") -> logging.Logger:
    """
    为MCP服务器设置专用日志记录器
    
    Args:
        mcp_name: MCP服务器名称
        logs_dir: 日志目录
    
    Returns:
        配置好的MCP日志记录器
    """
    log_filename = get_timestamped_filename(f"{mcp_name}_mcp")
    log_path = Path(logs_dir) / mcp_name / log_filename
    
    return setup_logger(
        name=f"mcp.{mcp_name}",
        log_file=str(log_path),
        format_string='%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s'
    )