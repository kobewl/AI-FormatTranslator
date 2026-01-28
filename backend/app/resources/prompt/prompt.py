"""
提示词管理路由
处理提示词的增删改查操作
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from ...database import get_db
from ...models.prompt import Prompt
from ...models.customer import Customer
from ...core.deps import get_current_customer
from ...schemas.common import ResponseModel
from pydantic import BaseModel


router = APIRouter(prefix="/prompt", tags=["提示词管理"])


class PromptCreateRequest(BaseModel):
    """提示词创建请求"""
    name: str
    content: str
    description: Optional[str] = None
    category: str = "general"
    language: str = "en"


class PromptUpdateRequest(BaseModel):
    """提示词更新请求"""
    name: Optional[str] = None
    content: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    language: Optional[str] = None
    is_active: Optional[bool] = None


@router.get("/list", response_model=None)
async def get_prompts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: Optional[str] = Query(None),
    current_user: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """
    获取提示词列表（分页）

    - **page**: 页码
    - **page_size**: 每页数量
    - **category**: 分类筛选（可选）
    """
    # 构建查询（只返回启用的提示词）
    query = db.query(Prompt).filter(Prompt.is_active == True)

    # 分类筛选
    if category:
        query = query.filter(Prompt.category == category)

    # 按使用次数和创建时间排序
    query = query.order_by(desc(Prompt.is_default), desc(Prompt.use_count), desc(Prompt.created_at))

    # 分页
    total = query.count()
    offset = (page - 1) * page_size
    items = query.offset(offset).limit(page_size).all()

    items_data = [item.to_dict() for item in items]
    pages = (total + page_size - 1) // page_size

    return ResponseModel(
        success=True,
        message="获取成功",
        data={
            "items": items_data,
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": pages
        }
    )


@router.get("/{prompt_id}", response_model=None)
async def get_prompt(
    prompt_id: int,
    current_user: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """
    获取提示词详情

    - **prompt_id**: 提示词ID
    """
    prompt = db.query(Prompt).filter(Prompt.id == prompt_id).first()

    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="提示词不存在"
        )

    return ResponseModel(
        success=True,
        message="获取成功",
        data=prompt.to_dict()
    )


@router.post("/create", response_model=None)
async def create_prompt(
    prompt_data: PromptCreateRequest,
    current_user: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """
    创建提示词（管理员功能）

    - **name**: 提示词名称
    - **content**: 提示词内容
    - **description**: 描述（可选）
    - **category**: 分类
    - **language**: 适用语言
    """
    # 检查是否为管理员（这里简化处理，实际应该检查用户角色）
    # TODO: 添加管理员权限检查

    # 检查名称是否已存在
    if db.query(Prompt).filter(Prompt.name == prompt_data.name).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="提示词名称已存在"
        )

    # 创建提示词
    prompt = Prompt(
        name=prompt_data.name,
        content=prompt_data.content,
        description=prompt_data.description,
        category=prompt_data.category,
        language=prompt_data.language,
        created_by=current_user.id
    )

    try:
        db.add(prompt)
        db.commit()
        db.refresh(prompt)

        return ResponseModel(
            success=True,
            message="创建成功",
            data=prompt.to_dict()
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建失败: {str(e)}"
        )


@router.put("/{prompt_id}", response_model=None)
async def update_prompt(
    prompt_id: int,
    prompt_data: PromptUpdateRequest,
    current_user: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """
    更新提示词（管理员功能）

    - **prompt_id**: 提示词ID
    """
    # TODO: 添加管理员权限检查

    prompt = db.query(Prompt).filter(Prompt.id == prompt_id).first()

    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="提示词不存在"
        )

    # 更新字段
    if prompt_data.name is not None:
        prompt.name = prompt_data.name
    if prompt_data.content is not None:
        prompt.content = prompt_data.content
    if prompt_data.description is not None:
        prompt.description = prompt_data.description
    if prompt_data.category is not None:
        prompt.category = prompt_data.category
    if prompt_data.language is not None:
        prompt.language = prompt_data.language
    if prompt_data.is_active is not None:
        prompt.is_active = prompt_data.is_active

    try:
        db.commit()
        db.refresh(prompt)

        return ResponseModel(
            success=True,
            message="更新成功",
            data=prompt.to_dict()
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新失败: {str(e)}"
        )


@router.delete("/{prompt_id}", response_model=None)
async def delete_prompt(
    prompt_id: int,
    current_user: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """
    删除提示词（管理员功能）

    - **prompt_id**: 提示词ID
    """
    # TODO: 添加管理员权限检查

    prompt = db.query(Prompt).filter(Prompt.id == prompt_id).first()

    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="提示词不存在"
        )

    # 不允许删除默认提示词
    if prompt.is_default:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能删除默认提示词"
        )

    try:
        db.delete(prompt)
        db.commit()

        return ResponseModel(
            success=True,
            message="删除成功",
            data={"id": prompt_id}
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除失败: {str(e)}"
        )
