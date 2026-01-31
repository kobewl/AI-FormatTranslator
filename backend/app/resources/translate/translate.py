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
from ...schemas.translate import TranslateRequest, TranslateResponse, PreviewResponse, ParallelPreviewResponse
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
    translate.domain = request_data.domain
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


@router.post("/retry", response_model=ResponseModel[TranslateResponse])
async def retry_translate(
    task_id: int,
    request_data: TranslateRequest,
    current_user: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """
    重试翻译任务

    基于已完成的翻译任务创建新的翻译任务，使用相同的文件但允许修改翻译参数
    
    - **task_id**: 原翻译任务ID（必须已完成）
    - **source_lang**: 源语言（auto表示自动检测）
    - **target_lang**: 目标语言
    - **model_name**: AI模型名称
    - **thread_count**: 翻译线程数（1-10）
    - **prompt_id**: 提示词ID（可选）
    - **domain**: 翻译领域（general/medical/it/legal/finance等）
    - **options**: 额外配置选项（可选）
    """
    import shutil
    import uuid
    from ...config import settings

    # 查询原翻译记录
    original_translate = db.query(Translate).filter(
        Translate.id == task_id,
        Translate.customer_id == current_user.id
    ).first()

    if not original_translate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="原翻译任务不存在"
        )

    # 检查原任务是否已完成
    if original_translate.status not in ["completed", "failed"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"原任务状态为 {original_translate.status}，只有已完成或失败的任务可以重试"
        )

    # 检查原文件是否存在
    if not original_translate.file_path or not os.path.exists(original_translate.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="原文件不存在，无法重试"
        )

    try:
        # 复制文件到新的路径（避免影响原任务）
        file_ext = original_translate.file_type
        new_filename = f"{uuid.uuid4()}.{file_ext}"
        new_file_path = settings.UPLOAD_DIR / new_filename
        
        shutil.copy2(original_translate.file_path, new_file_path)

        # 创建新的翻译记录
        new_translate = Translate(
            customer_id=current_user.id,
            file_name=original_translate.file_name,
            file_path=str(new_file_path),
            file_size=original_translate.file_size,
            file_type=original_translate.file_type,
            source_lang=request_data.source_lang,
            target_lang=request_data.target_lang,
            model_name=request_data.model_name,
            thread_count=request_data.thread_count,
            prompt_id=request_data.prompt_id,
            display_mode=request_data.display_mode,
            domain=request_data.domain,
            options=request_data.options,
            status="pending",
            progress=0,
            total_segments=0,
            translated_segments=0
        )

        db.add(new_translate)
        db.commit()
        db.refresh(new_translate)

        # 更新用户存储空间
        current_user.update_used_space(original_translate.file_size)
        db.commit()

        return ResponseModel(
            success=True,
            message="重试任务创建成功",
            data=new_translate.to_dict()
        )
    except Exception as e:
        db.rollback()
        # 清理已复制的文件（如果存在）
        if 'new_file_path' in locals() and os.path.exists(new_file_path):
            try:
                os.remove(new_file_path)
            except:
                pass
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建重试任务失败: {str(e)}"
        )


@router.get("/{task_id}/preview", response_model=ResponseModel[PreviewResponse])
async def get_translate_preview(
    task_id: int,
    max_chars: int = Query(5000, ge=100, le=20000, description="最大提取字符数"),
    current_user: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """
    获取翻译任务的源文件预览

    提取源文件内容用于预览，支持 docx/pdf/xlsx/pptx/md/txt 格式

    - **task_id**: 任务ID
    - **max_chars**: 最大提取字符数（默认5000，范围100-20000）
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

    # 检查源文件是否存在
    if not translate.file_path or not os.path.exists(translate.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="源文件不存在"
        )

    try:
        # 根据文件类型选择对应的 Formatter
        file_type = translate.file_type.lower()
        from ...translate.engine import TranslateEngine

        if file_type not in TranslateEngine.FORMATTERS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的文件类型: {file_type}"
            )

        # 获取 Formatter 实例
        formatter_class = TranslateEngine.FORMATTERS[file_type]
        formatter = formatter_class()

        # 提取内容
        preview_data = formatter.extract_content(translate.file_path, max_chars)

        return ResponseModel(
            success=True,
            message="预览内容获取成功",
            data=preview_data
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"预览内容提取失败: {str(e)}"
        )


@router.get("/{task_id}/preview-parallel", response_model=ResponseModel[ParallelPreviewResponse])
async def get_translate_parallel_preview(
    task_id: int,
    max_chars: int = Query(5000, ge=100, le=20000, description="最大提取字符数"),
    current_user: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """
    获取翻译任务的对照预览（原文+译文）

    同时提取源文件和翻译结果文件的内容，用于对照查看

    - **task_id**: 任务ID
    - **max_chars**: 最大提取字符数（默认5000，范围100-20000）
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

    # 检查源文件是否存在
    if not translate.file_path or not os.path.exists(translate.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="源文件不存在"
        )

    # 检查翻译结果文件是否存在
    if not translate.result_file_path or not os.path.exists(translate.result_file_path):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="翻译结果文件不存在，请先完成翻译"
        )

    try:
        # 根据文件类型选择对应的 Formatter
        file_type = translate.file_type.lower()
        from ...translate.engine import TranslateEngine

        if file_type not in TranslateEngine.FORMATTERS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的文件类型: {file_type}"
            )

        # 获取 Formatter 实例
        formatter_class = TranslateEngine.FORMATTERS[file_type]
        formatter = formatter_class()

        # 提取源文件内容
        source_preview = formatter.extract_content(translate.file_path, max_chars)

        # 提取译文文件内容
        # PDF 翻译后转为 Word，所以译文的格式可能不同
        result_type = 'docx' if file_type == 'pdf' else file_type
        if result_type in TranslateEngine.FORMATTERS:
            result_formatter_class = TranslateEngine.FORMATTERS[result_type]
            result_formatter = result_formatter_class()
            translated_preview = result_formatter.extract_content(translate.result_file_path, max_chars)
        else:
            translated_preview = {'content': [], 'total_chars': 0, 'truncated': False}

        return ResponseModel(
            success=True,
            message="对照预览内容获取成功",
            data={
                'source_content': source_preview.get('content', []),
                'translated_content': translated_preview.get('content', []),
                'source_chars': source_preview.get('total_chars', 0),
                'translated_chars': translated_preview.get('total_chars', 0),
                'truncated': source_preview.get('truncated', False) or translated_preview.get('truncated', False),
                'format': file_type
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"对照预览内容提取失败: {str(e)}"
        )
