"""
DocTranslator 数据模型模块
导出所有数据模型（SQLAlchemy 2.0）
"""
from .user import User
from .customer import Customer
from .translate import Translate
from .translate_log import TranslateLog
from .prompt import Prompt
from .comparison import Comparison
from .setting import Setting

__all__ = [
    "User",
    "Customer",
    "Translate",
    "TranslateLog",
    "Prompt",
    "Comparison",
    "Setting"
]
