"""
Setting 数据模型（系统配置）
使用 SQLAlchemy 2.0 语法
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text

from ..database import Base


class Setting(Base):
    """
    系统配置模型
    用于存储全局系统配置参数
    """

    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, index=True, comment="配置ID")
    key = Column(String(100), unique=True, nullable=False, index=True, comment="配置键")
    value = Column(Text, nullable=True, comment="配置值")
    value_type = Column(String(20), default="string", comment="值类型（string/int/float/bool/json）")
    category = Column(String(50), default="general", comment="配置分类")
    description = Column(String(500), nullable=True, comment="配置描述")

    # 状态
    is_public = Column(Boolean, default=False, comment="是否公开（前端可读取）")
    is_editable = Column(Boolean, default=True, comment="是否可编辑")

    # 时间戳
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")

    def get_value(self):
        """
        获取转换后的值

        Returns:
            根据值类型转换后的值
        """
        if self.value is None:
            return None

        if self.value_type == "int":
            return int(self.value)
        elif self.value_type == "float":
            return float(self.value)
        elif self.value_type == "bool":
            return self.value.lower() in ("true", "1", "yes", "on")
        elif self.value_type == "json":
            import json
            return json.loads(self.value)
        else:
            return self.value

    def set_value(self, value):
        """
        设置值

        Args:
            value: 要设置的值
        """
        import json
        if self.value_type == "json":
            self.value = json.dumps(value, ensure_ascii=False)
        else:
            self.value = str(value)

    def to_dict(self) -> dict:
        """
        转换为字典（用于 JSON 序列化）

        Returns:
            dict: 配置信息字典
        """
        return {
            "id": self.id,
            "key": self.key,
            "value": self.get_value(),
            "value_type": self.value_type,
            "category": self.category,
            "description": self.description,
            "is_public": self.is_public,
            "is_editable": self.is_editable,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        return f"<Setting {self.key}={self.value}>"
