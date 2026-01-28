"""
数据库连接和会话管理
使用 SQLAlchemy 2.0 语法（FastAPI 推荐）
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from .config import settings

# 创建数据库引擎
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DATABASE_ECHO,
    pool_pre_ping=True,  # 自动检测连接是否有效
    pool_recycle=3600,   # 1小时后回收连接
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建模型基类
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    数据库会话依赖注入函数
    用于 FastAPI 依赖注入

    Yields:
        Session: 数据库会话

    示例:
        @app.get("/users")
        def read_users(db: Session = Depends(get_db)):
            users = db.query(User).all()
            return users
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    初始化数据库表
    创建所有定义的表
    """
    # 导入所有模型，让它们注册到 Base
    from .models import User, Customer, Translate, TranslateLog, Prompt, Comparison, Setting
    Base.metadata.create_all(bind=engine)


def drop_db():
    """
    删除所有数据库表
    警告：仅用于测试环境
    """
    from . import Base
    Base.metadata.drop_all(bind=engine)
