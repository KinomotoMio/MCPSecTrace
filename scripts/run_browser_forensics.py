#!/usr/bin/env python3
"""
浏览器取证数据提取启动脚本
"""

import sys
from pathlib import Path

# 添加src目录到Python路径
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from mcpsectrace.core.browser_forensics import main

if __name__ == "__main__":
    main()