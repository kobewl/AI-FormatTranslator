"""
PDF 文档格式处理器
使用 PDF → Word → 翻译 的方案，保持格式
"""
import uuid
import asyncio
import os
import shutil
from pathlib import Path
from typing import Callable, Optional

from . import BaseFormatter
from .word import WordFormatter
from ...config import settings

# 尝试导入 pdf2docx
try:
    from pdf2docx import Converter
    PDF2DOCX_AVAILABLE = True
except ImportError:
    PDF2DOCX_AVAILABLE = False


class PDFFormatter(BaseFormatter):
    """
    PDF 文档处理器

    使用 pdf2docx 将 PDF 转换为 Word，然后翻译 Word 文档
    返回翻译后的 Word 文件（.docx 格式）

    这个方案的优点：
    - Word 格式会自动调整文本布局，不会错位
    - 表格结构保持良好
    - 用户可以手动调整格式
    """

    def _pdf_to_word(self, pdf_path: str, word_path: str) -> str:
        """
        将 PDF 转换为 Word

        Args:
            pdf_path: PDF 文件路径
            word_path: 输出的 Word 文件路径

        Returns:
            str: Word 文件路径
        """
        if not PDF2DOCX_AVAILABLE:
            raise ImportError("PDF 转 Word 需要安装 pdf2docx")

        # 创建转换器
        cv = Converter(pdf_path)
        try:
            # 转换 PDF 到 Word
            cv.convert(word_path)
        finally:
            cv.close()

        return word_path

    def translate(
        self,
        source_path: str,
        target_lang: str,
        ai_translator,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> str:
        """
        翻译 PDF 文档（同步包装器，调用异步方法）

        Args:
            source_path: 源 PDF 文件路径
            target_lang: 目标语言
            ai_translator: AI 翻译器实例
            progress_callback: 进度回调函数

        Returns:
            str: 翻译结果 Word 文件路径
        """
        # 检查翻译器是否支持并发方法
        if hasattr(ai_translator, 'translate_batch_async_concurrent'):
            # 获取线程数配置
            thread_count = getattr(ai_translator, 'thread_count', 5)

            # 创建新的事件循环并运行异步方法（不关闭循环，避免 AsyncOpenAI 客户端引用错误）
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(
                    self.translate_async(source_path, target_lang, ai_translator, thread_count, progress_callback)
                )
            finally:
                # 不关闭循环，让 asyncio 自动管理
                asyncio.set_event_loop(None)
        else:
            # 使用原有同步逻辑
            return self._translate_sync(source_path, target_lang, ai_translator, progress_callback)

    def _translate_sync(
        self,
        source_path: str,
        target_lang: str,
        ai_translator,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> str:
        """
        同步翻译 PDF 文档

        Args:
            source_path: 源 PDF 文件路径
            target_lang: 目标语言
            ai_translator: AI 翻译器实例
            progress_callback: 进度回调函数

        Returns:
            str: 翻译结果 Word 文件路径
        """
        print(f"🚀 启动 PDF 翻译（通过 Word 格式）")

        # 创建临时工作目录
        work_dir = settings.TRANSLATE_DIR / f"pdf2word_{uuid.uuid4().hex[:8]}"
        work_dir.mkdir(parents=True, exist_ok=True)

        try:
            # 第一步：PDF → Word
            print(f"\n📖 步骤 1/2: PDF 转 Word...")
            pdf_source = Path(source_path)
            word_temp_path = work_dir / f"{pdf_source.stem}.docx"

            self._pdf_to_word(source_path, str(word_temp_path))

            # 第二步：翻译 Word 文档
            print(f"\n🌐 步骤 2/2: 翻译 Word 文档...")

            # 使用 WordFormatter 翻译
            word_formatter = WordFormatter()
            translated_word_path = word_formatter._translate_sync(
                str(word_temp_path),
                target_lang,
                ai_translator,
                progress_callback
            )

            # WordFormatter 已经将文件保存到最终位置了
            # 直接返回该路径
            result_path = translated_word_path

            print(f"✅ 翻译完成！")
            print(f"📁 结果文件: {result_path}")

            # 清理临时目录
            shutil.rmtree(work_dir)

            return result_path

        except Exception as e:
            print(f"❌ PDF 翻译失败: {str(e)}")
            import traceback
            traceback.print_exc()

            # 清理临时目录
            if work_dir.exists():
                shutil.rmtree(work_dir)

            raise

    async def translate_async(
        self,
        source_path: str,
        target_lang: str,
        ai_translator,
        thread_count: int = 5,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> str:
        """
        异步翻译 PDF 文档

        Args:
            source_path: 源 PDF 文件路径
            target_lang: 目标语言
            ai_translator: AI 翻译器实例
            thread_count: 并发线程数
            progress_callback: 进度回调函数

        Returns:
            str: 翻译结果 Word 文件路径
        """
        print(f"🚀 启动 PDF 翻译（异步，通过 Word 格式）")

        # 创建临时工作目录
        work_dir = settings.TRANSLATE_DIR / f"pdf2word_{uuid.uuid4().hex[:8]}"
        work_dir.mkdir(parents=True, exist_ok=True)

        try:
            # 第一步：PDF → Word（同步操作，在线程池中运行）
            print(f"\n📖 步骤 1/2: PDF 转 Word...")
            pdf_source = Path(source_path)
            word_temp_path = work_dir / f"{pdf_source.stem}.docx"

            # 在线程池中运行 PDF → Word 转换
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self._pdf_to_word(source_path, str(word_temp_path))
            )

            # 第二步：翻译 Word 文档（异步）
            print(f"\n🌐 步骤 2/2: 翻译 Word 文档...")

            # 使用 WordFormatter 翻译
            word_formatter = WordFormatter()
            translated_word_path = await word_formatter.translate_async(
                str(word_temp_path),
                target_lang,
                ai_translator,
                thread_count,
                progress_callback
            )

            # WordFormatter 已经将文件保存到最终位置了
            # 直接返回该路径
            result_path = translated_word_path

            print(f"✅ 翻译完成！")
            print(f"📁 结果文件: {result_path}")

            # 清理临时目录
            shutil.rmtree(work_dir)

            return result_path

        except Exception as e:
            print(f"❌ PDF 翻译失败: {str(e)}")
            import traceback
            traceback.print_exc()

            # 清理临时目录
            if work_dir.exists():
                shutil.rmtree(work_dir)

            raise

    def extract_content(self, file_path: str, max_chars: int = 5000) -> dict:
        """
        提取 PDF 文件内容用于预览

        PDF 文件需要先转换为 Word，然后提取内容

        Args:
            file_path: 文件路径
            max_chars: 最大提取字符数

        Returns:
            dict: 包含 content 列表、total_chars、truncated、format
        """
        if not PDF2DOCX_AVAILABLE:
            return {
                'content': [],
                'total_chars': 0,
                'truncated': False,
                'format': 'pdf',
                'error': 'PDF 预览需要安装 pdf2docx 库'
            }

        # 创建临时工作目录
        work_dir = settings.TRANSLATE_DIR / f"pdf_preview_{uuid.uuid4().hex[:8]}"
        work_dir.mkdir(parents=True, exist_ok=True)

        try:
            # PDF → Word
            pdf_source = Path(file_path)
            word_temp_path = work_dir / f"{pdf_source.stem}.docx"

            self._pdf_to_word(file_path, str(word_temp_path))

            # 使用 WordFormatter 提取内容
            word_formatter = WordFormatter()
            result = word_formatter.extract_content(str(word_temp_path), max_chars)
            result['format'] = 'pdf'

            # 清理临时目录
            shutil.rmtree(work_dir)

            return result

        except Exception as e:
            # 清理临时目录
            if work_dir.exists():
                shutil.rmtree(work_dir)

            return {
                'content': [],
                'total_chars': 0,
                'truncated': False,
                'format': 'pdf',
                'error': str(e)
            }
