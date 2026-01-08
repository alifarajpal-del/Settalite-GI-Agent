"""
نظام تسجيل متقدم للعمليات
"""
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

def setup_logger(
    log_dir: str = "outputs",
    name: str = "heritage_sentinel",
    level: str = "INFO"
) -> logging.Logger:
    """
    إعداد نظام التسجيل
    
    Args:
        log_dir: مجلد السجلات
        name: اسم السجل
        level: مستوى التسجيل
    
    Returns:
        كائن Logger
    """
    # إنشاء مجلد السجلات
    log_path = Path(log_dir) / "logs"
    log_path.mkdir(parents=True, exist_ok=True)
    
    # إنشاء اسم ملف السجل
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_path / f"{name}_{timestamp}.log"
    
    # إعداد Logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # إزالة المعالجات القديمة
    logger.handlers.clear()
    
    # معالج الملف
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s | %(name)s | %(levelname)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    
    # معالج الطرفية
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, level.upper()))
    console_formatter = logging.Formatter(
        '%(levelname)s: %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    
    # إضافة المعالجات
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    logger.info(f"تم تهيئة نظام التسجيل: {log_file}")
    
    return logger

class LoggerContext:
    """
    سياق تسجيل مع معلومات إضافية
    """
    def __init__(self, logger: logging.Logger, operation: str):
        self.logger = logger
        self.operation = operation
        self.start_time = None
    
    def __enter__(self):
        self.start_time = datetime.now()
        self.logger.info(f"بدء عملية: {self.operation}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = (datetime.now() - self.start_time).total_seconds()
        
        if exc_type is None:
            self.logger.info(f"اكتملت عملية: {self.operation} ({duration:.2f}s)")
        else:
            self.logger.error(f"فشلت عملية: {self.operation} ({duration:.2f}s) - {exc_val}")
        
        return False

def log_function(logger: logging.Logger):
    """
    ديكوريتور لتسجيل استدعاءات الدوال
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger.debug(f"استدعاء دالة: {func.__name__}")
            try:
                result = func(*args, **kwargs)
                logger.debug(f"نجحت دالة: {func.__name__}")
                return result
            except Exception as e:
                logger.error(f"فشلت دالة: {func.__name__} - {e}")
                raise
        return wrapper
    return decorator
