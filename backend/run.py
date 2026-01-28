"""
DocTranslator API 启动入口
使用 Uvicorn ASGI 服务器运行 FastAPI 应用
"""
import uvicorn
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).resolve().parent))

if __name__ == "__main__":
    uvicorn.run(
        "app:app",  # 应用路径
        host="0.0.0.0",  # 监听所有网络接口
        port=8000,  # 端口
        reload=True,  # 开发模式自动重载
        log_level="info",  # 日志级别
        access_log=True,  # 访问日志
    )
