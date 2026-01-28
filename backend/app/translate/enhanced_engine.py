"""
增强的翻译引擎核心
支持缓存、备份模型、重试机制
"""
import asyncio
import os
from pathlib import Path
from typing import Optional
from sqlalchemy.orm import Session

from ..models.translate import Translate
from .formatters.word import WordFormatter
from .formatters.pdf import PDFFormatter
from .formatters.excel import ExcelFormatter
from .formatters.powerpoint import PowerPointFormatter
from .formatters.markdown import MarkdownFormatter
from .formatters.txt import TxtFormatter
from .ai.enhanced_openai import EnhancedAITranslator
from ...config import settings


class EnhancedTranslateEngine:
    """
    增强的翻译引擎核心类

    新增功能：
    - 翻译结果缓存
    - 备份模型支持
    - 失败自动重试
    - 更详细的错误处理
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

    def _load_task(self):
        """加载翻译任务"""
        self.task = self.db.query(Translate).filter(Translate.id == self.task_id).first()
        if not self.task:
            raise ValueError(f"翻译任务 {self.task_id} 不存在")

    def _get_formatter(self):
        """获取对应的格式处理器"""
        formatter_class = self.FORMATTERS.get(self.task.file_type)
        if not formatter_class:
            raise ValueError(f"不支持的文件格式: {self.task.file_type}")

        return formatter_class()

    def _init_ai_translator(self):
        """初始化增强的 AI 翻译器"""
        # 从任务配置或系统配置获取参数
        model_name = self.task.model_name or settings.OPENAI_MODEL

        # 检查是否有备份模型配置
        backup_model = None
        if self.task.options and isinstance(self.task.options, dict):
            backup_model = self.task.options.get('backup_model')

        self.ai_translator = EnhancedAITranslator(
            api_key=settings.OPENAI_API_KEY,
            api_base=settings.OPENAI_API_BASE,
            model=model_name,
            backup_model=backup_model,
            timeout=settings.OPENAI_TIMEOUT,
            db=self.db  # 传入数据库会话以支持缓存
        )

    def execute(self):
        """
        执行翻译任务（同步方式）

        完整的翻译流程：
        1. 加载任务
        2. 选择格式处理器
        3. 初始化 AI 翻译器
        4. 提取文本
        5. AI 翻译（带缓存和重试）
        6. 生成结果文件
        7. 更新状态
        """
        try:
            # 1. 加载任务
            self._load_task()
            print(f"📝 开始翻译任务 {self.task_id}: {self.task.file_name}")

            # 2. 获取格式处理器
            self.formatter = self._get_formatter()
            print(f"📄 文件类型: {self.task.file_type}")

            # 3. 初始化 AI 翻译器
            self._init_ai_translator()
            print(f"🤖 使用模型: {self.ai_translator.model}")
            if self.ai_translator.backup_model:
                print(f"🔄 备份模型: {self.ai_translator.backup_model}")

            # 4. 检查源文件是否存在
            if not os.path.exists(self.task.file_path):
                raise FileNotFoundError(f"源文件不存在: {self.task.file_path}")

            # 5. 执行翻译
            print("🚀 开始执行翻译...")
            result_path = self.formatter.translate(
                source_path=self.task.file_path,
                target_lang=self.task.target_lang,
                ai_translator=self.ai_translator,
                progress_callback=self._update_progress
            )

            # 6. 标记为完成
            self.task.mark_as_completed(result_path)
            self.db.commit()

            print(f"✅ 翻译任务 {self.task_id} 完成!")

        except Exception as e:
            # 标记为失败
            if self.task:
                error_msg = str(e)
                self.task.mark_as_failed(error_msg)
                self.db.commit()
                print(f"❌ 翻译任务 {self.task_id} 失败: {error_msg}")
            raise

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
        更新翻译进度

        Args:
            current: 当前进度
            total: 总数
        """
        if self.task:
            self.task.update_progress(current)
            self.db.commit()
            print(f"📊 进度: {current}/{total} ({self.task.progress}%)")


# 便捷函数
def create_enhanced_translate_engine(task_id: int, db: Session) -> EnhancedTranslateEngine:
    """
    创建增强翻译引擎实例

    Args:
        task_id: 翻译任务ID
        db: 数据库会话

    Returns:
        EnhancedTranslateEngine: 增强翻译引擎实例
    """
    return EnhancedTranslateEngine(task_id, db)
