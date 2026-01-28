"""
Word 文档格式处理器
支持 .docx 文件的翻译，保持格式
参考开源项目 DocTranslator 的实现
"""
import uuid
import asyncio
from pathlib import Path
from typing import Callable, Optional
from docx import Document
from docx.oxml.ns import qn

from . import BaseFormatter
from ...config import settings


class WordFormatter(BaseFormatter):
    """
    Word 文档处理器

    使用 python-docx 库处理 Word 文档
    保持段落格式、字体样式、表格等
    """

    def translate(
        self,
        source_path: str,
        target_lang: str,
        ai_translator,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> str:
        """
        翻译 Word 文档（同步包装器，调用异步方法）

        Args:
            source_path: 源文件路径
            target_lang: 目标语言
            ai_translator: AI 翻译器实例
            progress_callback: 进度回调函数

        Returns:
            str: 翻译结果文件路径
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
        同步翻译 Word 文档（原有逻辑）

        Args:
            source_path: 源文件路径
            target_lang: 目标语言
            ai_translator: AI 翻译器实例
            progress_callback: 进度回调函数

        Returns:
            str: 翻译结果文件路径
        """
        # 加载文档
        doc = Document(source_path)

        # 第一步：读取所有需要翻译的文本（run 级别）
        texts = []

        # 读取段落中的 runs
        for paragraph in doc.paragraphs:
            self._read_runs(paragraph.runs, texts)

        # 读取超链接中的 runs
        for paragraph in doc.paragraphs:
            for hyperlink in paragraph.hyperlinks:
                self._read_runs(hyperlink.runs, texts)

        # 读取表格中的文本
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for paragraph in cell.paragraphs:
                        self._read_runs(paragraph.runs, texts)

        # 总文本数
        total_count = len(texts)
        if total_count == 0:
            return self._generate_result_path(source_path)

        # 第二步：批量翻译
        batch_size = 10  # 每批翻译的文本数

        for i in range(0, total_count, batch_size):
            batch = texts[i:i + batch_size]
            batch_texts = [item['text'] for item in batch]

            # 调用 AI 翻译
            translated_batch = ai_translator.translate_batch(
                texts=batch_texts,
                target_lang=target_lang
            )

            # 将翻译结果写回 texts 数组
            for j, item in enumerate(batch):
                if j < len(translated_batch):
                    item['translated'] = translated_batch[j]
                else:
                    item['translated'] = item['text']

            # 更新进度
            if progress_callback:
                progress_callback(min(i + batch_size, total_count), total_count)

        # 第三步：将翻译结果写回原文档
        index = 0

        # 写回段落的 runs
        for paragraph in doc.paragraphs:
            index = self._write_runs(paragraph.runs, texts, index)

        # 写回超链接的 runs
        for paragraph in doc.paragraphs:
            for hyperlink in paragraph.hyperlinks:
                index = self._write_runs(hyperlink.runs, texts, index)

        # 写回表格的文本
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for paragraph in cell.paragraphs:
                        index = self._write_runs(paragraph.runs, texts, index)

        # 保存结果（覆盖原文档）
        result_path = self._generate_result_path(source_path)
        doc.save(result_path)

        return result_path

    async def translate_async(
        self,
        source_path: str,
        target_lang: str,
        ai_translator,
        thread_count: int = 5,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> str:
        """
        异步翻译 Word 文档（支持并发）

        Args:
            source_path: 源文件路径
            target_lang: 目标语言
            ai_translator: AI 翻译器实例
            thread_count: 并发线程数
            progress_callback: 进度回调函数

        Returns:
            str: 翻译结果文件路径
        """
        # 加载文档
        doc = Document(source_path)

        # 第一步：读取所有需要翻译的文本（run 级别）
        texts = []

        # 读取段落中的 runs
        for paragraph in doc.paragraphs:
            self._read_runs(paragraph.runs, texts)

        # 读取超链接中的 runs
        for paragraph in doc.paragraphs:
            for hyperlink in paragraph.hyperlinks:
                self._read_runs(hyperlink.runs, texts)

        # 读取表格中的文本
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for paragraph in cell.paragraphs:
                        self._read_runs(paragraph.runs, texts)

        # 总文本数
        total_count = len(texts)
        if total_count == 0:
            return self._generate_result_path(source_path)

        # 第二步：异步批量翻译（并发模式）
        batch_size = 20  # 并发模式下可以增大批次

        # 检查翻译器是否支持并发方法
        if hasattr(ai_translator, 'translate_batch_async_concurrent'):
            # 使用并发翻译
            for i in range(0, total_count, batch_size):
                batch = texts[i:i + batch_size]
                batch_texts = [item['text'] for item in batch]

                # 调用异步并发翻译
                translated_batch = await ai_translator.translate_batch_async_concurrent(
                    texts=batch_texts,
                    target_lang=target_lang,
                    max_concurrency=thread_count,
                    progress_callback=progress_callback
                )

                # 将翻译结果写回 texts 数组
                for j, item in enumerate(batch):
                    if j < len(translated_batch):
                        item['translated'] = translated_batch[j]
                    else:
                        item['translated'] = item['text']
        else:
            # 降级到普通异步翻译
            for i in range(0, total_count, batch_size):
                batch = texts[i:i + batch_size]
                batch_texts = [item['text'] for item in batch]

                # 调用异步翻译
                translated_batch = await ai_translator.translate_batch_async(
                    texts=batch_texts,
                    target_lang=target_lang
                )

                # 将翻译结果写回 texts 数组
                for j, item in enumerate(batch):
                    if j < len(translated_batch):
                        item['translated'] = translated_batch[j]
                    else:
                        item['translated'] = item['text']

                # 更新进度
                if progress_callback:
                    progress_callback(min(i + batch_size, total_count), total_count)

        # 第三步：将翻译结果写回原文档
        index = 0

        # 写回段落的 runs
        for paragraph in doc.paragraphs:
            index = self._write_runs(paragraph.runs, texts, index)

        # 写回超链接的 runs
        for paragraph in doc.paragraphs:
            for hyperlink in paragraph.hyperlinks:
                index = self._write_runs(hyperlink.runs, texts, index)

        # 写回表格的文本
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for paragraph in cell.paragraphs:
                        index = self._write_runs(paragraph.runs, texts, index)

        # 保存结果（覆盖原文档）
        result_path = self._generate_result_path(source_path)
        doc.save(result_path)

        return result_path

    def _read_runs(self, runs, texts):
        """
        读取 runs 中的文本

        Args:
            runs: python-docx 的 runs 对象
            texts: 存储文本的列表
        """
        for run in runs:
            text = run.text
            if text and text.strip():
                texts.append({
                    'text': text,
                    'translated': None,
                    'complete': False
                })

    def _write_runs(self, runs, texts, index):
        """
        将翻译结果写回 runs

        Args:
            runs: python-docx 的 runs 对象
            texts: 存储翻译结果的列表
            index: 当前处理到的文本索引

        Returns:
            int: 更新后的索引
        """
        for run in runs:
            text = run.text
            if text and text.strip():
                if index < len(texts):
                    item = texts[index]
                    print(f"DEBUG _write_runs: index={index}, original={repr(text[:50])}, translated_type={type(item['translated'])}, translated={repr(str(item['translated'])[:50])}")
                    if item['translated']:
                        run.text = item['translated']
                    index += 1
        return index

    def _generate_result_path(self, source_path: str) -> str:
        """
        生成结果文件路径

        Args:
            source_path: 源文件路径

        Returns:
            str: 结果文件路径
        """
        source = Path(source_path)
        # 使用源文件的文件名，但保存到 translate 目录
        filename = f"{source.stem}_translated{source.suffix}"
        return str(settings.TRANSLATE_DIR / filename)
