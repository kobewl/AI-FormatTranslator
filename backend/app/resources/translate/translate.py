"""
翻译任务路由
处理翻译任务的启动、查询、列表、下载等操作
"""
import os
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc

from ...database import get_db
from ...models.customer import Customer
from ...models.translate import Translate
from ...schemas.translate import TranslateRequest, TranslateResponse
from ...schemas.common import ResponseModel, PaginationParams, PaginatedResponse
from ...core.deps import get_current_customer
from ...translate.engine import TranslateEngine


router = APIRouter(tags=["翻译任务"])


@router.post("/start", response_model=ResponseModel[TranslateResponse])
async def start_translate(
    request_data: TranslateRequest,
    current_user: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """
    启动翻译任务

    - **file_id**: 文件ID（上传时返回的ID）
    - **source_lang**: 源语言（auto表示自动检测）
    - **target_lang**: 目标语言
    - **model_name**: AI模型名称
    - **thread_count**: 翻译线程数（1-10）
    - **prompt_id**: 提示词ID（可选）
    - **options**: 额外配置选项（可选）
    """

    # 查询翻译记录
    translate = db.query(Translate).filter(
        Translate.id == request_data.file_id,
        Translate.customer_id == current_user.id
    ).first()

    if not translate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="翻译任务不存在"
        )

    # 检查状态
    if translate.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"任务状态为 {translate.status}，无法启动翻译"
        )

    # 更新翻译配置
    translate.source_lang = request_data.source_lang
    translate.target_lang = request_data.target_lang
    translate.model_name = request_data.model_name
    translate.thread_count = request_data.thread_count
    translate.prompt_id = request_data.prompt_id
    translate.display_mode = request_data.display_mode
    translate.options = request_data.options

    try:
        # 标记为开始处理
        translate.mark_as_started()
        db.commit()

        # 同时更新 Redis 状态
        from ...utils.redis_client import RedisClient
        RedisClient.set_translate_progress(translate.id, {
            "task_id": translate.id,
            "status": "processing",
            "progress": 0,
            "total_segments": 0,
            "translated_segments": 0,
            "error_message": None
        })

        # 创建翻译引擎并执行（异步）
        engine = TranslateEngine(translate.id, db)
        # 在实际应用中，这里应该使用 Celery 或后台任务
        # 暂时使用同步方式演示
        import asyncio
        asyncio.create_task(engine.execute_async())

        return ResponseModel(
            success=True,
            message="翻译任务已启动",
            data=translate.to_dict()
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"启动翻译失败: {str(e)}"
        )


@router.get("/list", response_model=ResponseModel[PaginatedResponse])
async def get_translate_list(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    status_filter: Optional[str] = Query(None, description="状态筛选"),
    current_user: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """
    获取翻译任务列表（分页）

    - **page**: 页码（从1开始）
    - **page_size**: 每页数量
    - **status_filter**: 状态筛选（可选）
    """

    # 构建查询
    query = db.query(Translate).filter(Translate.customer_id == current_user.id)

    # 状态筛选
    if status_filter:
        query = query.filter(Translate.status == status_filter)

    # 按创建时间倒序
    query = query.order_by(desc(Translate.created_at))

    # 计算总数
    total = query.count()

    # 分页
    offset = (page - 1) * page_size
    items = query.offset(offset).limit(page_size).all()

    # 转换为字典
    items_data = [item.to_dict() for item in items]
    pages = (total + page_size - 1) // page_size

    return ResponseModel(
        success=True,
        message="获取成功",
        data=PaginatedResponse(
            items=items_data,
            total=total,
            page=page,
            page_size=page_size,
            pages=pages
        )
    )


@router.get("/{task_id}", response_model=ResponseModel[TranslateResponse])
async def get_translate_detail(
    task_id: int,
    current_user: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """
    获取翻译任务详情

    - **task_id**: 任务ID
    """

    translate = db.query(Translate).filter(
        Translate.id == task_id,
        Translate.customer_id == current_user.id
    ).first()

    if not translate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="翻译任务不存在"
        )

    return ResponseModel(
        success=True,
        message="获取成功",
        data=translate.to_dict()
    )


@router.get("/{task_id}/progress", response_model=None)
async def get_translate_progress(
    task_id: int,
    current_user: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """
    查询翻译进度

    - **task_id**: 任务ID
    """

    # 首先尝试从 Redis 获取进度（实时数据）
    from ...utils.redis_client import RedisClient

    progress_data = RedisClient.get_translate_progress(task_id)

    if progress_data:
        # 从 Redis 获取到了数据
        return ResponseModel(
            success=True,
            message="获取成功",
            data=progress_data
        )

    # Redis 中没有数据，从数据库查询（备用方案）
    translate = db.query(Translate).filter(
        Translate.id == task_id,
        Translate.customer_id == current_user.id
    ).first()

    if not translate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="翻译任务不存在"
        )

    progress_data = {
        "task_id": translate.id,
        "status": translate.status,
        "progress": translate.progress,
        "total_segments": translate.total_segments,
        "translated_segments": translate.translated_segments,
        "error_message": translate.error_message
    }

    return ResponseModel(
        success=True,
        message="获取成功",
        data=progress_data
    )


@router.get("/{task_id}/download")
async def download_translate_result(
    task_id: int,
    current_user: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """
    下载翻译结果

    - **task_id**: 任务ID
    """

    translate = db.query(Translate).filter(
        Translate.id == task_id,
        Translate.customer_id == current_user.id
    ).first()

    if not translate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="翻译任务不存在"
        )

    if translate.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"任务未完成（当前状态: {translate.status}）"
        )

    if not translate.result_file_path or not os.path.exists(translate.result_file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="翻译结果文件不存在"
        )

    # 生成下载文件名（使用实际结果文件的扩展名）
    original_name, _ = os.path.splitext(translate.file_name)
    result_ext = os.path.splitext(translate.result_file_path)[1]

    # 使用目标语言代码生成文件名：原文件名_语言代码.扩展名
    target_lang = translate.target_lang if translate.target_lang else "en"
    download_filename = f"{original_name}_{target_lang}{result_ext}"

    # 读取文件内容
    with open(translate.result_file_path, 'rb') as f:
        content = f.read()

    # URL 编码文件名
    from urllib.parse import quote
    filename_encoded = quote(download_filename.encode('utf-8'))

    # 使用 Response 而不是 FileResponse，手动设置所有头
    from fastapi.responses import Response

    return Response(
        content=content,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{filename_encoded}"
        }
    )


@router.delete("/{task_id}", response_model=None)
async def delete_translate_task(
    task_id: int,
    current_user: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """
    删除翻译任务

    - **task_id**: 任务ID
    """

    translate = db.query(Translate).filter(
        Translate.id == task_id,
        Translate.customer_id == current_user.id
    ).first()

    if not translate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="翻译任务不存在"
        )

    # 删除物理文件
    if translate.file_path and os.path.exists(translate.file_path):
        try:
            os.remove(translate.file_path)
            current_user.update_used_space(-translate.file_size)
        except:
            pass

    # 删除结果文件
    if translate.result_file_path and os.path.exists(translate.result_file_path):
        try:
            os.remove(translate.result_file_path)
        except:
            pass

    # 删除数据库记录
    try:
        db.delete(translate)
        db.commit()

        return ResponseModel(
            success=True,
            message="任务删除成功",
            data={"id": task_id}
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除失败: {str(e)}"
        )


@router.delete("/all", response_model=None)
async def delete_all_translates(
    current_user: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """
    删除所有翻译任务

    清空用户的所有翻译任务和文件
    """
    # 查询所有任务
    translates = db.query(Translate).filter(
        Translate.customer_id == current_user.id
    ).all()

    deleted_count = 0
    total_freed_space = 0

    for translate in translates:
        # 删除物理文件
        if translate.file_path and os.path.exists(translate.file_path):
            try:
                os.remove(translate.file_path)
                total_freed_space += translate.file_size
            except:
                pass

        # 删除结果文件
        if translate.result_file_path and os.path.exists(translate.result_file_path):
            try:
                os.remove(translate.result_file_path)
            except:
                pass

        # 删除数据库记录
        db.delete(translate)
        deleted_count += 1

    # 更新用户存储空间
    current_user.update_used_space(-total_freed_space)

    try:
        db.commit()

        return ResponseModel(
            success=True,
            message=f"已删除 {deleted_count} 个翻译任务",
            data={
                "deleted_count": deleted_count,
                "freed_space": total_freed_space
            }
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除失败: {str(e)}"
        )


@router.get("/statistics", response_model=None)
async def get_translate_statistics(
    current_user: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """
    获取翻译统计信息

    返回用户的翻译统计数据
    """
    # 查询统计
    total = db.query(Translate).filter(
        Translate.customer_id == current_user.id
    ).count()

    completed = db.query(Translate).filter(
        Translate.customer_id == current_user.id,
        Translate.status == 'completed'
    ).count()

    failed = db.query(Translate).filter(
        Translate.customer_id == current_user.id,
        Translate.status == 'failed'
    ).count()

    processing = db.query(Translate).filter(
        Translate.customer_id == current_user.id,
        Translate.status == 'processing'
    ).count()

    pending = db.query(Translate).filter(
        Translate.customer_id == current_user.id,
        Translate.status == 'pending'
    ).count()

    # 计算总文件大小
    total_size = db.query(Translate).filter(
        Translate.customer_id == current_user.id
    ).with_entities(
        Translate.file_size
    ).all()
    total_file_size = sum(size for (size,) in total_size)

    return ResponseModel(
        success=True,
        message="获取成功",
        data={
            "total": total,
            "completed": completed,
            "failed": failed,
            "processing": processing,
            "pending": pending,
            "success_rate": round(completed / total * 100, 2) if total > 0 else 0,
            "total_file_size": total_file_size
        }
    )


@router.get("/finish/count", response_model=None)
async def get_finish_count(
    current_user: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """
    获取已完成翻译数量

    简化版的统计接口，只返回已完成数量
    """
    count = db.query(Translate).filter(
        Translate.customer_id == current_user.id,
        Translate.status == 'completed'
    ).count()

    return ResponseModel(
        success=True,
        message="获取成功",
        data={"count": count}
    )
