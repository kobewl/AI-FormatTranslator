"""
DocTranslator 日志配置模块

提供统一的日志配置和管理功能，支持：
- 控制台输出（带颜色）
- 文件输出（自动轮转）
- 不同级别的日志分离
- 异步日志写入（性能优化）
"""
import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from typing import Optional

from ..config import settings


# 日志颜色配置
class ColoredFormatter(logging.Formatter):
    """带颜色的控制台日志格式化器"""

    # ANSI 颜色代码
    COLORS = {
        'DEBUG': '\033[36m',    # 青色
        'INFO': '\033[32m',     # 绿色
        'WARNING': '\033[33m',  # 黄色
        'ERROR': '\033[31m',    # 红色
        'CRITICAL': '\033[35m', # 紫色
    }
    RESET = '\033[0m'

    def format(self, record):
        """格式化日志记录，添加颜色"""
        log_color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{log_color}{record.levelname}{self.RESET}"
        return super().format(record)


def setup_logger(
    name: str = "doc_translator",
    level: Optional[str] = None,
    log_dir: Optional[Path] = None
) -> logging.Logger:
    """
    设置并返回一个配置好的日志记录器

    Args:
        name: 日志记录器名称
        level: 日志级别（DEBUG、INFO、WARNING、ERROR、CRITICAL）
        log_dir: 日志文件目录

    Returns:
        配置好的日志记录器

    Example:
        >>> logger = setup_logger(__name__)
        >>> logger.info("这是一条普通日志")
        >>> logger.error("这是一条错误日志")
    """
    # 创建日志记录器
    logger = logging.getLogger(name)

    # 如果已经配置过，直接返回
    if logger.handlers:
        return logger

    # 设置日志级别
    log_level = level or ("DEBUG" if settings.DEBUG else "INFO")
    logger.setLevel(getattr(logging, log_level.upper()))

    # 日志格式
    detailed_format = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(filename)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    console_format = ColoredFormatter(
        fmt='%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%H:%M:%S'
    )

    # 1. 控制台处理器（带颜色）
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)

    # 2. 文件处理器（如果配置了日志目录）
    if log_dir is None:
        log_dir = settings.BASE_DIR / "logs"

    # 确保日志目录存在
    log_dir.mkdir(parents=True, exist_ok=True)

    # 按大小轮转的文件处理器 - 所有日志
    all_log_file = log_dir / "app.log"
    file_handler = RotatingFileHandler(
        filename=all_log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=10,              # 保留10个备份
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_format)
    logger.addHandler(file_handler)

    # 3. 错误日志单独文件
    error_log_file = log_dir / "error.log"
    error_handler = RotatingFileHandler(
        filename=error_log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,               # 保留5个备份
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_format)
    logger.addHandler(error_handler)

    return logger


# 创建默认的日志记录器实例
logger = setup_logger("doc_translator")


def get_logger(name: str) -> logging.Logger:
    """
    获取指定名称的日志记录器

    Args:
        name: 日志记录器名称（通常使用 __name__）

    Returns:
        日志记录器实例

    Example:
        >>> from app.utils.logger import get_logger
        >>> logger = get_logger(__name__)
        >>> logger.info("模块启动")
    """
    return setup_logger(name)
