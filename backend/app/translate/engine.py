"""
翻译引擎核心
负责协调各种格式处理器和 AI 翻译服务
"""
import asyncio
import os
from pathlib import Path
from typing import Optional
from sqlalchemy.orm import Session
from threading import Lock

from ..models.translate import Translate
from ..database import get_db  # 添加导入
from .formatters.word import WordFormatter
from .formatters.pdf import PDFFormatter
from .formatters.excel import ExcelFormatter
from .formatters.powerpoint import PowerPointFormatter
from .formatters.markdown import MarkdownFormatter
from .formatters.txt import TxtFormatter
from .ai.openai import AITranslator
from ..config import settings


class TranslateEngine:
    """
    翻译引擎核心类

    负责协调翻译任务的完整流程：
    1. 根据文件类型选择对应的格式处理器
    2. 提取文本内容
    3. 调用 AI 翻译服务
    4. 生成翻译后的文件
    5. 更新任务状态和进度
    """

    # 格式处理器映射
    FORMATTERS = {
        "docx": WordFormatter,
        "pdf": PDFFormatter,
        "xlsx": ExcelFormatter,
        "pptx": PowerPointFormatter,
        "md": MarkdownFormatter,
        "txt": TxtFormatter
    }

    # 类级别的锁，用于进度更新的并发控制
    _progress_lock = Lock()

    def __init__(self, task_id: int, db: Session):
        """
        初始化翻译引擎

        Args:
            task_id: 翻译任务ID
            db: 数据库会话
        """
        self.task_id = task_id
        self.db = db
        self.task: Optional[Translate] = None
        self.formatter = None
        self.ai_translator = None

        # 进度更新节流
        self._last_progress_update = 0
        self._last_update_time = 0
        self._progress_update_interval = 0.2  # 每0.2秒最多更新一次数据库
        self._progress_update_threshold = 2  # 或者进度每变化2%更新一次

    def _load_task(self):
        """加载翻译任务"""
        self.task = self.db.query(Translate).filter(Translate.id == self.task_id).first()
        if not self.task:
            raise ValueError(f"翻译任务 {self.task_id} 不存在")

    def _load_task_with_db(self, db: Session):
        """使用指定的数据库 session 加载翻译任务（用于后台线程）"""
        self.task = db.query(Translate).filter(Translate.id == self.task_id).first()
        if not self.task:
            raise ValueError(f"翻译任务 {self.task_id} 不存在")

    def _get_formatter(self):
        """获取对应的格式处理器"""
        formatter_class = self.FORMATTERS.get(self.task.file_type)
        if not formatter_class:
            raise ValueError(f"不支持的文件格式: {self.task.file_type}")

        return formatter_class()

    def _init_ai_translator(self):
        """初始化 AI 翻译器"""
        self.ai_translator = AITranslator(
            api_key=settings.OPENAI_API_KEY,
            api_base=settings.OPENAI_API_BASE,
            model=self.task.model_name,
            timeout=settings.OPENAI_TIMEOUT
        )

        # 传递线程数配置给翻译器
        self.ai_translator.thread_count = self.task.thread_count

    def execute(self):
        """
        执行翻译任务（同步方式）

        完整的翻译流程：
        1. 加载任务
        2. 选择格式处理器
        3. 提取文本
        4. AI 翻译
        5. 生成结果文件
        6. 更新状态

        注意：此方法在后台线程中执行，需要创建新的数据库 session
        """
        # 在后台线程中创建新的数据库 session
        db = next(get_db())

        try:
            # 1. 加载任务（使用新的 session）
            self._load_task_with_db(db)

            # 2. 获取格式处理器
            self.formatter = self._get_formatter()

            # 3. 初始化 AI 翻译器
            self._init_ai_translator()

            # 4. 检查源文件是否存在
            if not os.path.exists(self.task.file_path):
                raise FileNotFoundError(f"源文件不存在: {self.task.file_path}")

            # 5. 执行翻译
            result_path = self.formatter.translate(
                source_path=self.task.file_path,
                target_lang=self.task.target_lang,
                ai_translator=self.ai_translator,
                progress_callback=lambda cur, total: self._update_progress_with_db(db, cur, total)
            )

            # 6. 标记为完成
            self.task.mark_as_completed(result_path)
            db.commit()

            # 同时更新 Redis 状态为 completed
            from ..utils.redis_client import RedisClient
            RedisClient.set_translate_progress(self.task_id, {
                "task_id": self.task_id,
                "status": "completed",
                "progress": 100,
                "total_segments": self.task.total_segments,
                "translated_segments": self.task.total_segments,
                "error_message": self.task.error_message
            })

            print(f"✅ 翻译任务 {self.task_id} 完成")

        except Exception as e:
            # 标记为失败
            if self.task:
                self.task.mark_as_failed(str(e))
                db.commit()

                # 同时更新 Redis 状态为 failed
                from ..utils.redis_client import RedisClient
                RedisClient.set_translate_progress(self.task_id, {
                    "task_id": self.task_id,
                    "status": "failed",
                    "progress": self.task.progress,
                    "total_segments": self.task.total_segments,
                    "translated_segments": self.task.translated_segments,
                    "error_message": str(e)
                })

            print(f"❌ 翻译任务 {self.task_id} 失败: {str(e)}")
            raise
        finally:
            # 关闭数据库 session
            db.close()

            # 关闭 AI 翻译器的异步客户端
            if self.ai_translator:
                try:
                    # 在新的事件循环中关闭异步客户端
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        loop.run_until_complete(self.ai_translator.close_async())
                    finally:
                        loop.close()
                except:
                    pass

    async def execute_async(self):
        """
        执行翻译任务（异步方式）

        在实际应用中，应该使用 Celery 等任务队列
        这里使用 asyncio 简单演示
        """
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.execute)

    def _update_progress(self, current: int, total: int):
        """
        更新翻译进度（主线程版本）

        使用节流机制，避免过于频繁的数据库更新
        使用锁确保并发安全
        同时写入 Redis，确保前端能实时获取到进度

        Args:
            current: 当前进度
            total: 总数
        """
        import time

        if not self.task:
            return

        # 使用锁确保并发安全
        with TranslateEngine._progress_lock:
            # 计算当前进度百分比
            progress_percent = int((current / total * 100)) if total > 0 else 0

            # 检查是否需要更新数据库
            should_update = False
            current_time = time.time()

            # 首次更新
            if self._last_progress_update == 0:
                should_update = True
            # 进度变化超过阈值（2%）
            elif abs(progress_percent - self._last_progress_update) >= self._progress_update_threshold:
                should_update = True
            # 距离上次更新超过时间间隔（0.2秒）
            elif current_time - self._last_update_time >= self._progress_update_interval:
                should_update = True

            if should_update:
                self.task.update_progress(current)
                self.db.commit()
                self._last_progress_update = progress_percent
                self._last_update_time = current_time
                print(f"📊 进度更新: {progress_percent}% ({current}/{total})")

                # 同时写入 Redis（实时进度）
                from ..utils.redis_client import RedisClient
                RedisClient.set_translate_progress(self.task_id, {
                    "task_id": self.task_id,
                    "status": self.task.status,
                    "progress": progress_percent,
                    "total_segments": total,
                    "translated_segments": current,
                    "error_message": self.task.error_message
                })

    def _update_progress_with_db(self, db: Session, current: int, total: int):
        """
        使用指定的数据库 session 更新翻译进度（用于后台线程）

        使用节流机制，避免过于频繁的数据库更新：
        - 每0.2秒最多更新一次
        - 或者进度每变化2%更新一次
        使用锁确保并发安全
        同时写入 Redis，确保前端能实时获取到进度

        Args:
            db: 数据库 session
            current: 当前进度
            total: 总数
        """
        import time

        if not self.task:
            return

        # 使用锁确保并发安全
        with TranslateEngine._progress_lock:
            # 计算当前进度百分比
            progress_percent = int((current / total * 100)) if total > 0 else 0

            # 检查是否需要更新数据库
            should_update = False
            current_time = time.time()

            # 首次更新
            if self._last_progress_update == 0:
                should_update = True
            # 进度变化超过阈值（2%）
            elif abs(progress_percent - self._last_progress_update) >= self._progress_update_threshold:
                should_update = True
            # 距离上次更新超过时间间隔（0.2秒）
            elif current_time - self._last_update_time >= self._progress_update_interval:
                should_update = True

            if should_update:
                self.task.update_progress(current)
                db.commit()
                self._last_progress_update = progress_percent
                self._last_update_time = current_time
                print(f"📊 进度更新: {progress_percent}% ({current}/{total})")

                # 同时写入 Redis（实时进度）
                from ..utils.redis_client import RedisClient
                RedisClient.set_translate_progress(self.task_id, {
                    "task_id": self.task_id,
                    "status": self.task.status,
                    "progress": progress_percent,
                    "total_segments": total,
                    "translated_segments": current,
                    "error_message": self.task.error_message
                })


# 便捷函数
def create_translate_engine(task_id: int, db: Session) -> TranslateEngine:
    """
    创建翻译引擎实例

    Args:
        task_id: 翻译任务ID
        db: 数据库会话

    Returns:
        TranslateEngine: 翻译引擎实例
    """
    return TranslateEngine(task_id, db)
