"""
Comparison 数据模型（术语对照表）
使用 SQLAlchemy 2.0 语法
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text

from ..database import Base


class Comparison(Base):
    """
    术语对照表模型
    用于存储专业术语的翻译对照，确保翻译一致性
    """

    __tablename__ = "comparisons"

    id = Column(Integer, primary_key=True, index=True, comment="术语ID")
    source_term = Column(String(500), nullable=False, comment="源术语")
    target_term = Column(String(500), nullable=False, comment="目标术语")

    # 语言信息
    source_lang = Column(String(20), nullable=False, comment="源语言")
    target_lang = Column(String(20), nullable=False, comment="目标语言")

    # 分类和描述
    category = Column(String(100), nullable=True, comment="术语分类（如：计算机、医学等）")
    description = Column(String(500), nullable=True, comment="术语解释")
    context = Column(Text, nullable=True, comment="使用场景说明")

    # 状态信息
    is_active = Column(Boolean, default=True, comment="是否启用")
    priority = Column(Integer, default=0, comment="优先级（数字越大优先级越高）")

    # 创建者信息
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True, comment="创建者ID")

    # 时间戳
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")

    def to_dict(self) -> dict:
        """
        转换为字典（用于 JSON 序列化）

        Returns:
            dict: 术语信息字典
        """
        return {
            "id": self.id,
            "source_term": self.source_term,
            "target_term": self.target_term,
            "source_lang": self.source_lang,
            "target_lang": self.target_lang,
            "category": self.category,
            "description": self.description,
            "context": self.context,
            "is_active": self.is_active,
            "priority": self.priority,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        return f"<Comparison {self.source_term} -> {self.target_term}>"
