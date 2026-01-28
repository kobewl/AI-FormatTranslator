"""
认证路由
处理用户登录、注册等认证相关操作
使用 FastAPI 路由装饰器
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ...database import get_db
from ...core.deps import get_current_customer
from ...models.customer import Customer
from ...models.user import User
from ...schemas.user import LoginRequest, RegisterRequest, TokenResponse, CustomerResponse
from ...core.security import create_access_token
from ...schemas.common import ResponseModel


router = APIRouter(prefix="/auth", tags=["认证"])


@router.post(
    "/login",
    response_model=ResponseModel[TokenResponse],
    summary="用户登录",
    description="用户使用用户名和密码登录系统"
)
async def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    用户登录接口

    - **username**: 用户名
    - **password**: 密码
    - **user_type**: 用户类型（customer/admin，默认customer）
    """
    # 根据用户类型选择模型
    if login_data.user_type == "admin":
        user = db.query(User).filter(User.username == login_data.username).first()
    else:
        user = db.query(Customer).filter(Customer.username == login_data.username).first()

    # 验证用户存在和密码正确
    if not user or not user.check_password(login_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )

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

    # 生成 JWT token
    token_data = {
        "sub": str(user.id),  # JWT 规范要求 sub 必须是字符串
        "user_type": login_data.user_type,
        "username": user.username
    }
    access_token = create_access_token(token_data)

    # 更新最后登录时间
    if hasattr(user, "last_login_at"):
        user.last_login_at = datetime.now()
        db.commit()

    return ResponseModel(
        success=True,
        message="登录成功",
        data=TokenResponse(
            token=access_token,
            token_type="Bearer",
            user_type=login_data.user_type,
            user=user.to_dict()
        )
    )


@router.post(
    "/register",
    response_model=ResponseModel[CustomerResponse],
    status_code=status.HTTP_201_CREATED,
    summary="用户注册",
    description="新用户注册账号"
)
async def register(
    register_data: RegisterRequest,
    db: Session = Depends(get_db)
):
    """
    用户注册接口

    - **username**: 用户名（至少3个字符）
    - **password**: 密码（至少6个字符）
    - **email**: 邮箱（可选）
    - **phone**: 手机号（可选）
    """
    # 检查用户名是否已存在
    if db.query(Customer).filter(Customer.username == register_data.username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )

    # 检查邮箱是否已存在
    if register_data.email:
        if db.query(Customer).filter(Customer.email == register_data.email).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已被注册"
            )

    # 创建新用户
    customer = Customer(
        username=register_data.username,
        email=register_data.email,
        phone=register_data.phone
    )
    customer.set_password(register_data.password)

    try:
        db.add(customer)
        db.commit()
        db.refresh(customer)

        return ResponseModel(
            success=True,
            message="注册成功",
            data=customer.to_dict()
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"注册失败: {str(e)}"
        )


@router.get(
    "/me",
    response_model=None,
    summary="获取当前用户信息",
    description="获取当前登录用户的详细信息"
)
async def get_current_user_info(
    current_user: Customer = Depends(get_current_customer)
):
    """
    获取当前用户信息接口

    需要在请求头中携带有效的 JWT token
    """
    return ResponseModel(
        success=True,
        message="获取成功",
        data=current_user.to_dict()
    )
