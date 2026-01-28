"""
Customer 数据模型（普通用户）
使用 SQLAlchemy 2.0 语法
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, BigInteger, ForeignKey
from sqlalchemy.orm import relationship

from ..database import Base
from ..core.security import verify_password, get_password_hash


class Customer(Base):
    """
    普通用户模型
    用于前端用户注册和使用翻译服务
    """

    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True, comment="用户ID")
    username = Column(String(50), unique=True, nullable=False, index=True, comment="用户名")
    password = Column(String(255), nullable=False, comment="密码")
    email = Column(String(100), unique=True, nullable=True, comment="邮箱")
    phone = Column(String(20), nullable=True, comment="手机号")

    # 存储空间管理（单位：字节）
    max_space = Column(BigInteger, default=1073741824, comment="最大存储空间（默认1GB）")
    used_space = Column(BigInteger, default=0, comment="已使用空间")

    # 用户状态
    status = Column(String(20), default="active", comment="状态（active/suspended）")
    vip_level = Column(String(20), default="free", comment="VIP等级（free/pro/enterprise）")
    vip_expire_at = Column(DateTime, nullable=True, comment="VIP过期时间")

    # 时间戳
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")
    last_login_at = Column(DateTime, nullable=True, comment="最后登录时间")

    # 关系：一个用户可以有多个翻译任务
    translates = relationship("Translate", back_populates="customer")

    def set_password(self, password: str):
        """
        设置密码（自动加密）

        Args:
            password: 明文密码
        """
        self.password = get_password_hash(password)

    def check_password(self, password: str) -> bool:
        """
        验证密码

        Args:
            password: 明文密码

        Returns:
            bool: 密码是否正确
        """
        return verify_password(password, self.password)

    def has_enough_space(self, file_size: int) -> bool:
        """
        检查是否有足够的存储空间

        Args:
            file_size: 文件大小（字节）

        Returns:
            bool: 是否有足够空间
        """
        return (self.used_space + file_size) <= self.max_space

    def update_used_space(self, delta: int):
        """
        更新已使用空间

        Args:
            delta: 空间变化量（正数增加，负数减少）
        """
        self.used_space = max(0, self.used_space + delta)

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
            "phone": self.phone,
            "max_space": self.max_space,
            "used_space": self.used_space,
            "space_percent": round(self.used_space / self.max_space * 100, 2) if self.max_space > 0 else 0,
            "status": self.status,
            "vip_level": self.vip_level,
            "vip_expire_at": self.vip_expire_at.isoformat() if self.vip_expire_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None
        }

    def __repr__(self):
        return f"<Customer {self.username}>"
