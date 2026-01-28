"""
术语对照表管理路由
处理术语对照表的增删改查操作
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_

from ...database import get_db
from ...models.comparison import Comparison
from ...models.customer import Customer
from ...core.deps import get_current_customer
from ...schemas.common import ResponseModel
from pydantic import BaseModel


router = APIRouter(prefix="/comparison", tags=["术语对照表"])


class ComparisonCreateRequest(BaseModel):
    """术语创建请求"""
    source_term: str
    target_term: str
    source_lang: str
    target_lang: str
    category: Optional[str] = None
    description: Optional[str] = None
    context: Optional[str] = None
    priority: int = 0


class ComparisonUpdateRequest(BaseModel):
    """术语更新请求"""
    source_term: Optional[str] = None
    target_term: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    context: Optional[str] = None
    priority: Optional[int] = None
    is_active: Optional[bool] = None


@router.get("/list", response_model=None)
async def get_comparisons(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    source_lang: Optional[str] = Query(None),
    target_lang: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    current_user: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """
    获取术语对照表列表（分页）

    - **page**: 页码
    - **page_size**: 每页数量
    - **source_lang**: 源语言筛选（可选）
    - **target_lang**: 目标语言筛选（可选）
    - **category**: 分类筛选（可选）
    """
    # 构建查询
    query = db.query(Comparison).filter(Comparison.is_active == True)

    # 语言筛选
    if source_lang:
        query = query.filter(Comparison.source_lang == source_lang)
    if target_lang:
        query = query.filter(Comparison.target_lang == target_lang)

    # 分类筛选
    if category:
        query = query.filter(Comparison.category == category)

    # 按优先级和创建时间排序
    query = query.order_by(desc(Comparison.priority), desc(Comparison.created_at))

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


@router.get("/search", response_model=None)
async def search_comparisons(
    keyword: str = Query(..., min_length=1),
    source_lang: str = Query(...),
    target_lang: str = Query(...),
    current_user: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """
    搜索术语对照

    - **keyword**: 搜索关键词
    - **source_lang**: 源语言
    - **target_lang**: 目标语言
    """
    # 搜索源术语或目标术语包含关键词的记录
    query = db.query(Comparison).filter(
        Comparison.is_active == True,
        Comparison.source_lang == source_lang,
        Comparison.target_lang == target_lang,
        or_(
            Comparison.source_term.like(f"%{keyword}%"),
            Comparison.target_term.like(f"%{keyword}%")
        )
    )

    # 按优先级排序
    query = query.order_by(desc(Comparison.priority))

    items = query.limit(50).all()
    items_data = [item.to_dict() for item in items]

    return ResponseModel(
        success=True,
        message="搜索成功",
        data={
            "items": items_data,
            "total": len(items_data)
        }
    )


@router.get("/{comparison_id}", response_model=None)
async def get_comparison(
    comparison_id: int,
    current_user: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """
    获取术语对照详情

    - **comparison_id**: 术语ID
    """
    comparison = db.query(Comparison).filter(Comparison.id == comparison_id).first()

    if not comparison:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="术语对照不存在"
        )

    return ResponseModel(
        success=True,
        message="获取成功",
        data=comparison.to_dict()
    )


@router.post("/create", response_model=None)
async def create_comparison(
    comparison_data: ComparisonCreateRequest,
    current_user: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """
    创建术语对照（管理员功能）

    - **source_term**: 源术语
    - **target_term**: 目标术语
    - **source_lang**: 源语言
    - **target_lang**: 目标语言
    - **category**: 分类（可选）
    - **description**: 描述（可选）
    - **context**: 使用场景（可选）
    - **priority**: 优先级（可选）
    """
    # TODO: 添加管理员权限检查

    # 创建术语对照
    comparison = Comparison(
        source_term=comparison_data.source_term,
        target_term=comparison_data.target_term,
        source_lang=comparison_data.source_lang,
        target_lang=comparison_data.target_lang,
        category=comparison_data.category,
        description=comparison_data.description,
        context=comparison_data.context,
        priority=comparison_data.priority,
        created_by=current_user.id
    )

    try:
        db.add(comparison)
        db.commit()
        db.refresh(comparison)

        return ResponseModel(
            success=True,
            message="创建成功",
            data=comparison.to_dict()
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建失败: {str(e)}"
        )


@router.put("/{comparison_id}", response_model=None)
async def update_comparison(
    comparison_id: int,
    comparison_data: ComparisonUpdateRequest,
    current_user: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """
    更新术语对照（管理员功能）

    - **comparison_id**: 术语ID
    """
    # TODO: 添加管理员权限检查

    comparison = db.query(Comparison).filter(Comparison.id == comparison_id).first()

    if not comparison:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="术语对照不存在"
        )

    # 更新字段
    if comparison_data.source_term is not None:
        comparison.source_term = comparison_data.source_term
    if comparison_data.target_term is not None:
        comparison.target_term = comparison_data.target_term
    if comparison_data.category is not None:
        comparison.category = comparison_data.category
    if comparison_data.description is not None:
        comparison.description = comparison_data.description
    if comparison_data.context is not None:
        comparison.context = comparison_data.context
    if comparison_data.priority is not None:
        comparison.priority = comparison_data.priority
    if comparison_data.is_active is not None:
        comparison.is_active = comparison_data.is_active

    try:
        db.commit()
        db.refresh(comparison)

        return ResponseModel(
            success=True,
            message="更新成功",
            data=comparison.to_dict()
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新失败: {str(e)}"
        )


@router.delete("/{comparison_id}", response_model=None)
async def delete_comparison(
    comparison_id: int,
    current_user: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """
    删除术语对照（管理员功能）

    - **comparison_id**: 术语ID
    """
    # TODO: 添加管理员权限检查

    comparison = db.query(Comparison).filter(Comparison.id == comparison_id).first()

    if not comparison:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="术语对照不存在"
        )

    try:
        db.delete(comparison)
        db.commit()

        return ResponseModel(
            success=True,
            message="删除成功",
            data={"id": comparison_id}
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除失败: {str(e)}"
        )
