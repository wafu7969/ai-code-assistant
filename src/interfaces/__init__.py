"""
接口层

包含用户交互接口：
- 命令行接口(CLI)
- API接口
- 其他交互接口
"""

from .cli import CLI

__all__ = ["CLI"]