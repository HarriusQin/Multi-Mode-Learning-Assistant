import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional


class LogManager:
    """日志管理器，单例模式"""

    _instance: Optional['LogManager'] = None
    _loggers: dict[str, logging.Logger] = {}

    def __init__(
        self,
        log_dir: str = "logs",
        level: int = logging.INFO,
        max_bytes: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5,
        console_level: int = logging.WARNING,
    ):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.level = level
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        self.console_level = console_level

    @classmethod
    def get_instance(cls, **kwargs) -> 'LogManager':
        if cls._instance is None:
            if kwargs:
                cls._instance = cls(**kwargs)
            else:
                cls._instance = cls()
        return cls._instance

    @classmethod
    def reset(cls):
        """重置单例，用于测试"""
        cls._instance = None
        cls._loggers = {}

    def get_logger(self, name: str) -> logging.Logger:
        if name in self._loggers:
            return self._loggers[name]

        logger = logging.getLogger(name)
        logger.setLevel(self.level)
        logger.handlers.clear()

        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)8s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        # 文件 handler - 轮转
        fh = RotatingFileHandler(
            self.log_dir / f"{name}.log",
            maxBytes=self.max_bytes,
            backupCount=self.backup_count,
            encoding="utf-8"
        )
        fh.setLevel(self.level)
        fh.setFormatter(formatter)

        # 控制台 handler
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(self.console_level)
        ch.setFormatter(formatter)

        logger.addHandler(fh)
        logger.addHandler(ch)

        self._loggers[name] = logger
        return logger


def init_logging(
    log_dir: str = "logs",
    level: int = logging.INFO,
    console_level: int = logging.WARNING,
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 5,
):
    """初始化日志系统"""
    LogManager.reset()
    LogManager.get_instance(
        log_dir=log_dir,
        level=level,
        console_level=console_level,
        max_bytes=max_bytes,
        backup_count=backup_count,
    )


def get_logger(name: str) -> logging.Logger:
    """获取 logger 实例"""
    return LogManager.get_instance().get_logger(name)
