"""
用户账户功能路由
处理修改密码、存储空间查询等用户账户相关操作
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ...database import get_db
from ...models.customer import Customer
from ...core.deps import get_current_customer
from ...core.security import get_password_hash
from ...schemas.common import ResponseModel
from pydantic import BaseModel


router = APIRouter(prefix="/account", tags=["用户账户"])


class ChangePasswordRequest(BaseModel):
    """修改密码请求"""
    old_password: str
    new_password: str


@router.post("/change-password", response_model=None)
async def change_password(
    request_data: ChangePasswordRequest,
    current_user: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """
    修改密码

    - **old_password**: 原密码
    - **new_password**: 新密码（至少6个字符）
    """
    # 验证原密码
    if not current_user.check_password(request_data.old_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="原密码错误"
        )

    # 验证新密码长度
    if len(request_data.new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="新密码至少需要6个字符"
        )

    # 更新密码
    current_user.set_password(request_data.new_password)

    try:
        db.commit()

        return ResponseModel(
            success=True,
            message="密码修改成功，请重新登录",
            data={}
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"密码修改失败: {str(e)}"
        )


@router.get("/storage", response_model=None)
async def get_storage_info(
    current_user: Customer = Depends(get_current_customer)
):
    """
    获取存储空间信息

    返回用户的存储空间使用情况
    """
    def format_size(bytes_size: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_size < 1024.0:
                return f"{bytes_size:.2f} {unit}"
            bytes_size /= 1024.0
        return f"{bytes_size:.2f} TB"

    return ResponseModel(
        success=True,
        message="获取成功",
        data={
            "max_space": current_user.max_space,
            "used_space": current_user.used_space,
            "available_space": current_user.max_space - current_user.used_space,
            "space_percent": round(current_user.used_space / current_user.max_space * 100, 2),
            "max_space_formatted": format_size(current_user.max_space),
            "used_space_formatted": format_size(current_user.used_space),
            "available_space_formatted": format_size(current_user.max_space - current_user.used_space),
            "vip_level": current_user.vip_level
        }
    )


@router.get("/info", response_model=None)
async def get_account_info(
    current_user: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """
    获取账户详细信息

    包括用户信息和翻译统计
    """
    # 查询用户的翻译统计
    from ...models.translate import Translate
    total_translates = db.query(Translate).filter(
        Translate.customer_id == current_user.id
    ).count()

    completed_translates = db.query(Translate).filter(
        Translate.customer_id == current_user.id,
        Translate.status == 'completed'
    ).count()

    return ResponseModel(
        success=True,
        message="获取成功",
        data={
            "user": current_user.to_dict(),
            "statistics": {
                "total_translates": total_translates,
                "completed_translates": completed_translates,
                "success_rate": round(completed_translates / total_translates * 100, 2) if total_translates > 0 else 0
            }
        }
    )
