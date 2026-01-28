"""
用户相关的 Pydantic 模式
定义请求和响应的数据结构
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr, ConfigDict


class LoginRequest(BaseModel):
    """登录请求"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    password: str = Field(..., min_length=6, description="密码")
    user_type: Optional[str] = Field("customer", description="用户类型（customer/admin）")

    class Config:
        json_schema_extra = {
            "example": {
                "username": "testuser",
                "password": "password123",
                "user_type": "customer"
            }
        }


class RegisterRequest(BaseModel):
    """注册请求"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    password: str = Field(..., min_length=6, max_length=100, description="密码")
    email: Optional[EmailStr] = Field(None, description="邮箱")
    phone: Optional[str] = Field(None, description="手机号")

    class Config:
        json_schema_extra = {
            "example": {
                "username": "newuser",
                "password": "password123",
                "email": "user@example.com",
                "phone": "13800138000"
            }
        }


class TokenResponse(BaseModel):
    """Token 响应"""
    token: str = Field(..., description="JWT 访问令牌")
    token_type: str = Field("Bearer", description="令牌类型")
    user_type: str = Field(..., description="用户类型")
    user: dict = Field(..., description="用户信息")

    class Config:
        json_schema_extra = {
            "example": {
                "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "Bearer",
                "user_type": "customer",
                "user": {
                    "id": 1,
                    "username": "testuser",
                    "email": "user@example.com"
                }
            }
        }


class CustomerResponse(BaseModel):
    """用户信息响应"""
    id: int
    username: str
    email: Optional[str] = None
    phone: Optional[str] = None
    max_space: int
    used_space: int
    space_percent: float
    status: str
    vip_level: str
    vip_expire_at: Optional[datetime] = None
    created_at: datetime
    last_login_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class UserResponse(BaseModel):
    """管理员信息响应"""
    id: int
    username: str
    email: Optional[str] = None
    role: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
