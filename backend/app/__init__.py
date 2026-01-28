"""
DocTranslator FastAPI 主应用
使用 FastAPI 框架构建的文档翻译 API
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from .config import settings
from .database import init_db
from .utils.logger import setup_logger
from .resources.auth import router as auth_router
from .resources.translate import router as translate_router
from .resources.prompt import router as prompt_router
from .resources.comparison import router as comparison_router
from .resources.setting import router as setting_router
from .resources.account import router as account_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理

    Args:
        app: FastAPI 应用实例

    Yields:
        None
    """
    # 初始化日志系统
    app_logger = setup_logger(
        name="doc_translator",
        level=settings.LOG_LEVEL,
        log_dir=settings.LOG_DIR
    )

    # 启动时执行
    app_logger.info("=" * 50)
    app_logger.info("🚀 正在启动 DocTranslator API...")
    app_logger.info(f"📦 环境: {'开发' if settings.DEBUG else '生产'}")
    app_logger.info(f"📊 日志级别: {settings.LOG_LEVEL}")
    app_logger.info(f"🗄️  数据库: {settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else 'N/A'}")

    # 初始化数据库表
    if settings.DEBUG:
        init_db()
        app_logger.info("✅ 数据库表已创建")

    app_logger.info("✅ DocTranslator API 启动完成")
    app_logger.info("=" * 50)

    yield

    # 关闭时执行
    app_logger.info("👋 正在关闭 DocTranslator API...")


# 创建 FastAPI 应用实例
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="基于 AI 的智能文档翻译系统",
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,  # Swagger UI
    redoc_url="/redoc" if settings.DEBUG else None,  # ReDoc
)


# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)


# 注册路由
app.include_router(auth_router, prefix=settings.API_PREFIX)
app.include_router(translate_router, prefix=settings.API_PREFIX)
app.include_router(prompt_router, prefix=settings.API_PREFIX)
app.include_router(comparison_router, prefix=settings.API_PREFIX)
app.include_router(setting_router, prefix=settings.API_PREFIX)
app.include_router(account_router, prefix=settings.API_PREFIX)


# 根路径
@app.get("/", tags=["根路径"])
async def root():
    """API 根路径"""
    return {
        "success": True,
        "message": "欢迎使用 DocTranslator API",
        "version": settings.APP_VERSION,
        "docs": "/docs" if settings.DEBUG else "disabled"
    }


# 健康检查
@app.get("/health", tags=["健康检查"])
async def health_check():
    """健康检查端点"""
    return {
        "success": True,
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION
    }


# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全局异常处理器"""
    import traceback
    print(f"❌ 未处理的异常: {exc}")
    print(traceback.format_exc())

    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "服务器内部错误",
            "detail": str(exc) if settings.DEBUG else None
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="debug" if settings.DEBUG else "info"
    )
