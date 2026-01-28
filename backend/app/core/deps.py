"""
FastAPI 依赖注入
定义常用的依赖函数，用于路由中
"""
from typing import Optional, Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.user import User
from ..models.customer import Customer
from ..core.security import decode_access_token


# HTTP Bearer 认证方案
security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Customer:
    """
    获取当前登录用户（依赖注入）

    Args:
        credentials: HTTP Bearer 认证凭据
        db: 数据库会话

    Returns:
        当前用户对象

    Raises:
        HTTPException: 认证失败时抛出 401 错误
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # 解码 token
    token = credentials.credentials
    payload = decode_access_token(token)

    if payload is None:
        raise credentials_exception

    # 获取用户 ID（JWT 的 sub 是字符串）
    user_id_str = payload.get("sub")
    if user_id_str is None:
        raise credentials_exception

    # 转换为整数
    try:
        user_id = int(user_id_str)
    except (ValueError, TypeError):
        raise credentials_exception

    # 获取用户类型
    user_type = payload.get("user_type", "customer")

    # 查询用户
    if user_type == "admin":
        user = db.query(User).filter(User.id == user_id).first()
    else:
        user = db.query(Customer).filter(Customer.id == user_id).first()

    if user is None:
        raise credentials_exception

    # 检查用户状态
    if hasattr(user, "status") and user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账户已被禁用"
        )

    if hasattr(user, "is_active") and not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账户未激活"
        )

    return user


def get_current_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    获取当前管理员用户（依赖注入）

    Args:
        current_user: 当前用户

    Returns:
        管理员用户对象

    Raises:
        HTTPException: 如果不是管理员则抛出 403 错误
    """
    if not isinstance(current_user, User):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )

    return current_user


def get_current_customer(
    current_user: Customer = Depends(get_current_user)
) -> Customer:
    """
    获取当前普通用户（依赖注入）

    Args:
        current_user: 当前用户

    Returns:
        普通用户对象

    Raises:
        HTTPException: 如果不是普通用户则抛出 403 错误
    """
    if not isinstance(current_user, Customer):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要普通用户权限"
        )

    return current_user
