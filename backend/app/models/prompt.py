"""
Prompt 数据模型（提示词模板）
使用 SQLAlchemy 2.0 语法
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from ..database import Base


class Prompt(Base):
    """
    提示词模板模型
    用于存储和管理 AI 翻译提示词模板
    """

    __tablename__ = "prompts"

    id = Column(Integer, primary_key=True, index=True, comment="提示词ID")
    name = Column(String(100), nullable=False, comment="提示词名称")
    description = Column(String(500), nullable=True, comment="描述")
    content = Column(Text, nullable=False, comment="提示词内容（支持变量占位符）")

    # 分类信息
    category = Column(String(50), default="general", comment="分类（general/technical/literary等）")
    language = Column(String(20), default="en", comment="适用语言")

    # 状态信息
    is_active = Column(Boolean, default=True, comment="是否启用")
    is_default = Column(Boolean, default=False, comment="是否为默认提示词")
    use_count = Column(Integer, default=0, comment="使用次数")

    # 创建者信息
    created_by = Column(Integer, ForeignKey("customers.id"), nullable=True, comment="创建者ID")

    # 时间戳
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")

    # 关系：一个提示词可以被多个翻译任务使用
    translates = relationship("Translate", back_populates="prompt")

    def increment_usage(self):
        """增加使用次数"""
        self.use_count += 1

    def to_dict(self) -> dict:
        """
        转换为字典（用于 JSON 序列化）

        Returns:
            dict: 提示词信息字典
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "content": self.content,
            "category": self.category,
            "language": self.language,
            "is_active": self.is_active,
            "is_default": self.is_default,
            "use_count": self.use_count,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        return f"<Prompt {self.name}>"
