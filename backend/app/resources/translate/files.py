"""
文件上传路由
处理文件上传、删除等操作
"""
import os
import uuid
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session

from ...database import get_db
from ...models.customer import Customer
from ...models.translate import Translate
from ...schemas.translate import FileUploadResponse
from ...schemas.common import ResponseModel
from ...config import settings
from ...core.deps import get_current_customer


router = APIRouter(tags=["文件管理"])


def get_file_extension(filename: str) -> str:
    """获取文件扩展名"""
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


@router.post("/upload", response_model=ResponseModel[FileUploadResponse])
async def upload_file(
    file: UploadFile = File(...),
    current_user: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """
    上传翻译文件

    - **file**: 要翻译的文件（支持 docx, pdf, xlsx, pptx, md, txt）
    """

    # 验证文件扩展名
    file_ext = get_file_extension(file.filename)
    if file_ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的文件格式。支持的格式: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )

    # 读取文件内容
    file_content = await file.read()
    file_size = len(file_content)

    # 检查文件大小
    if file_size > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"文件大小超过限制（最大 {settings.MAX_FILE_SIZE}MB）"
        )

    # 检查用户存储空间
    if not current_user.has_enough_space(file_size):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="存储空间不足"
        )

    # 生成唯一文件名
    unique_filename = f"{uuid.uuid4()}.{file_ext}"
    file_path = settings.UPLOAD_DIR / unique_filename

    # 保存文件
    try:
        with open(file_path, "wb") as f:
            f.write(file_content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文件保存失败: {str(e)}"
        )

    # 创建翻译记录（状态为 pending）
    translate = Translate(
        customer_id=current_user.id,
        file_name=file.filename,
        file_path=str(file_path),
        file_size=file_size,
        file_type=file_ext,
        status="pending"
    )

    try:
        db.add(translate)
        db.commit()
        db.refresh(translate)

        # 更新用户已使用空间
        current_user.update_used_space(file_size)
        db.commit()

        return ResponseModel(
            success=True,
            message="文件上传成功",
            data=FileUploadResponse(
                id=translate.id,
                file_name=translate.file_name,
                file_path=translate.file_path,
                file_size=translate.file_size,
                file_type=translate.file_type
            )
        )
    except Exception as e:
        # 回滚：删除文件
        if file_path.exists():
            os.remove(file_path)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建翻译记录失败: {str(e)}"
        )


@router.delete("/file/{file_id}", response_model=None)
async def delete_file(
    file_id: int,
    current_user: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """
    删除上传的文件

    - **file_id**: 文件ID
    """
    # 查询翻译记录
    translate = db.query(Translate).filter(
        Translate.id == file_id,
        Translate.customer_id == current_user.id
    ).first()

    if not translate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文件不存在"
        )

    # 只能删除 pending 或 failed 状态的任务
    if translate.status not in ["pending", "failed"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无法删除状态为 {translate.status} 的任务"
        )

    # 删除物理文件
    file_path = translate.file_path
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            # 更新用户存储空间
            current_user.update_used_space(-translate.file_size)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"删除文件失败: {str(e)}"
            )

    # 删除数据库记录
    try:
        db.delete(translate)
        db.commit()

        return ResponseModel(
            success=True,
            message="文件删除成功",
            data={"id": file_id}
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除记录失败: {str(e)}"
        )
