"""
翻译路由模块
"""
from fastapi import APIRouter

from .files import router as files_router
from .translate import router as translate_router

# 创建统一的翻译路由
router = APIRouter(prefix="/translate", tags=["翻译"])

# 合并子路由
router.include_router(files_router)
router.include_router(translate_router)
