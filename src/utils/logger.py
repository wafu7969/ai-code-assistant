"""
日志配置模块

提供统一的日志记录功能，支持控制台和文件同时输出
"""
import logging
import sys
from pathlib import Path
from datetime import datetime
import os


class DualOutputHandler(logging.Handler):
    """双重输出处理器：同时输出到控制台和文件"""
    
    def __init__(self, console_handler, file_handler):
        super().__init__()
        self.console_handler = console_handler
        self.file_handler = file_handler
    
    def emit(self, record):
        """同时向控制台和文件输出"""
        self.console_handler.emit(record)
        self.file_handler.emit(record)


class ColoredConsoleFormatter(logging.Formatter):
    """带颜色的控制台格式化器"""
    
    # ANSI颜色代码
    COLORS = {
        'DEBUG': '\033[36m',      # 青色
        'INFO': '\033[32m',       # 绿色
        'WARNING': '\033[33m',    # 黄色
        'ERROR': '\033[31m',      # 红色
        'CRITICAL': '\033[35m',   # 紫色
        'RESET': '\033[0m'        # 重置
    }
    
    def format(self, record):
        # 获取颜色
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']
        
        # 设置颜色
        record.levelname = f"{color}{record.levelname}{reset}"
        
        return super().format(record)


class Logger:
    """日志管理器"""
    
    def __init__(self, name: str = "ai_assistant", logs_dir: str = "logs"):
        self.name = name
        self.logs_dir = Path(logs_dir)
        self.logger = None
        self._setup_logger()
    
    def _setup_logger(self):
        """设置日志器"""
        # 创建logs目录
        self.logs_dir.mkdir(exist_ok=True)
        
        # 创建logger
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(logging.INFO)
        
        # 清除已有的handlers
        self.logger.handlers.clear()
        
        # 创建文件handler
        log_filename = datetime.now().strftime(f"{self.name}_%Y%m%d_%H%M%S.log")
        log_filepath = self.logs_dir / log_filename
        
        file_handler = logging.FileHandler(log_filepath, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        
        # 创建控制台handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # 设置格式
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_formatter = ColoredConsoleFormatter(
            '%(levelname)s - %(message)s'
        )
        
        file_handler.setFormatter(file_formatter)
        console_handler.setFormatter(console_formatter)
        
        # 创建双重输出handler
        dual_handler = DualOutputHandler(console_handler, file_handler)
        dual_handler.setFormatter(console_formatter)  # 控制台格式用于显示
        
        self.logger.addHandler(dual_handler)
        
        # 记录日志文件位置
        self.logger.info(f"📝 日志文件: {log_filepath}")
    
    def info(self, message: str):
        """记录信息日志"""
        self.logger.info(message)
    
    def warning(self, message: str):
        """记录警告日志"""
        self.logger.warning(message)
    
    def error(self, message: str):
        """记录错误日志"""
        self.logger.error(message)
    
    def debug(self, message: str):
        """记录调试日志"""
        self.logger.debug(message)
    
    def critical(self, message: str):
        """记录严重错误日志"""
        self.logger.critical(message)


# 全局日志器实例
_global_logger = None


def get_logger(name: str = "ai_assistant", logs_dir: str = "logs") -> Logger:
    """获取全局日志器实例"""
    global _global_logger
    if _global_logger is None:
        _global_logger = Logger(name, logs_dir)
    return _global_logger


def setup_logging(name: str = "ai_assistant", logs_dir: str = "logs"):
    """设置全局日志"""
    global _global_logger
    _global_logger = Logger(name, logs_dir)
    return _global_logger


def log_print(*args, **kwargs):
    """替代print函数，同时记录到日志"""
    # 组装消息
    sep = kwargs.get('sep', ' ')
    message = sep.join(str(arg) for arg in args)
    
    # 记录到日志
    logger = get_logger()
    logger.info(message)


# 在模块加载时设置print函数的替换
def enable_logging():
    """启用日志记录，替换内置print函数"""
    import builtins
    builtins.print = log_print


# 恢复原始print函数
_original_print = print


def disable_logging():
    """禁用日志记录，恢复原始print函数"""
    import builtins
    builtins.print = _original_print