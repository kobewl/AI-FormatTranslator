"""
翻译日志模型
用于缓存翻译结果，避免重复翻译相同的文本
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Index

from ..database import Base


class TranslateLog(Base):
    """
    翻译日志模型

    用于缓存已翻译的内容，避免重复调用 API
    通过 MD5 值判断是否为相同内容
    """
    __tablename__ = 'translate_logs'

    id = Column(Integer, primary_key=True, index=True, comment='日志ID')
    md5_key = Column(String(32), nullable=False, index=True, comment='MD5哈希键')
    api_url = Column(String(500), nullable=True, comment='API地址')
    api_key = Column(String(255), nullable=True, comment='API密钥')
    model = Column(String(50), nullable=True, comment='使用的模型')
    backup_model = Column(String(50), nullable=True, comment='备用模型')
    prompt = Column(Text, nullable=True, comment='提示词')
    target_lang = Column(String(20), nullable=False, comment='目标语言')
    source = Column(Text, nullable=False, comment='原文')
    content = Column(Text, nullable=False, comment='译文')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'md5_key': self.md5_key,
            'api_url': self.api_url,
            'model': self.model,
            'target_lang': self.target_lang,
            'source': self.source,
            'content': self.content,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f'<TranslateLog {self.md5_key[:8]}...>'
