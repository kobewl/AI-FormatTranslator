"""
User 数据模型（管理员）
使用 SQLAlchemy 2.0 语法
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime

from ..database import Base
from ..core.security import verify_password, get_password_hash


class User(Base):
    """
    管理员用户模型
    用于系统管理员登录和管理
    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, comment="用户ID")
    username = Column(String(50), unique=True, nullable=False, index=True, comment="用户名")
    password_hash = Column(String(255), nullable=False, comment="密码哈希")
    email = Column(String(100), unique=True, nullable=True, comment="邮箱")
    role = Column(String(20), default="admin", comment="角色（admin/user）")
    is_active = Column(Boolean, default=True, comment="是否激活")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")

    def set_password(self, password: str):
        """
        设置密码（自动加密）

        Args:
            password: 明文密码
        """
        self.password_hash = get_password_hash(password)

    def check_password(self, password: str) -> bool:
        """
        验证密码

        Args:
            password: 明文密码

        Returns:
            bool: 密码是否正确
        """
        return verify_password(password, self.password_hash)

    def to_dict(self) -> dict:
        """
        转换为字典（用于 JSON 序列化）

        Returns:
            dict: 用户信息字典（不包含密码）
        """
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        return f"<User {self.username}>"
