"""
通用 Pydantic 模式
定义标准化的 API 响应格式
"""
from typing import Generic, TypeVar, Optional, Any
from pydantic import BaseModel, Field

# 泛型类型变量
T = TypeVar("T")


class ResponseModel(BaseModel, Generic[T]):
    """
    统一响应格式
    """
    success: bool = Field(..., description="请求是否成功")
    message: str = Field(..., description="响应消息")
    data: Optional[T] = Field(None, description="响应数据")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "操作成功",
                "data": None
            }
        }


class PaginationParams(BaseModel):
    """
    分页参数
    """
    page: int = Field(1, ge=1, description="页码（从1开始）")
    page_size: int = Field(20, ge=1, le=100, description="每页记录数")

    class Config:
        json_schema_extra = {
            "example": {
                "page": 1,
                "page_size": 20
            }
        }


class PaginatedResponse(BaseModel, Generic[T]):
    """
    分页响应格式
    """
    items: list[T] = Field(..., description="数据列表")
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页记录数")
    pages: int = Field(..., description="总页数")

    class Config:
        json_schema_extra = {
            "example": {
                "items": [],
                "total": 100,
                "page": 1,
                "page_size": 20,
                "pages": 5
            }
        }
