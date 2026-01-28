"""
PDF 文档格式处理器
支持 .pdf 文件的翻译，保持原始格式
"""
import uuid
import asyncio
from pathlib import Path
from typing import Callable, Optional, List, Dict, Tuple
from copy import deepcopy

from . import BaseFormatter
from ...config import settings

# 尝试导入 PyMuPDF
try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False


class PDFFormatter(BaseFormatter):
    """
    PDF 文档处理器

    使用 PyMuPDF (fitz) 在原始 PDF 上替换文本，尽量保持原有格式
    """

    def _extract_text_blocks(self, page) -> List[Dict]:
        """
        提取页面中的文本块及其位置信息

        Args:
            page: PyMuPDF 页面对象

        Returns:
            List[Dict]: 文本块列表，包含文本内容和位置信息
        """
        blocks = page.get_text("dict")["blocks"]
        text_blocks = []

        for block in blocks:
            if "lines" in block:  # 文本块
                for line in block["lines"]:
                    for span in line["spans"]:
                        text = span["text"]
                        if text.strip():  # 只处理非空文本
                            text_blocks.append({
                                "text": text,
                                "bbox": span["bbox"],  # (x0, y0, x1, y1)
                                "font": span["font"],
                                "size": span["size"],
                                "flags": span["flags"],
                                "color": span["color"]
                            })

        return text_blocks

    def _replace_text_on_page(self, page, text_blocks: List[Dict], translations: List[str]):
        """
        在页面上替换文本

        Args:
            page: PyMuPDF 页面对象
            text_blocks: 原始文本块列表
            translations: 翻译后的文本列表
        """
        print(f"🔄 开始替换页面上的 {len(text_blocks)} 个文本块")

        # 先使用红色遮罩标记要删除的文本区域
        for block in text_blocks:
            rect = fitz.Rect(block["bbox"])
            # 添加红色遮罩注释来标记要删除的区域
            page.add_redact_annot(rect, fill=(1, 1, 1))  # 白色填充

        # 应用红色遮罩，这会真正删除被遮罩区域的内容
        page.apply_redactions()
        print(f"✅ 已清除原始文本")

        # 插入翻译后的文本
        success_count = 0
        for i, (block, translated_text) in enumerate(zip(text_blocks, translations)):
            bbox = block["bbox"]
            x0, y0, x1, y1 = bbox

            # 计算文本框的宽度和高度
            rect = fitz.Rect(x0, y0, x1, y1 + (y1 - y0) * 0.5)  # 增加高度以容纳可能的较长文本

            try:
                # 使用 insert_textbox 插入文本（支持自动换行和缩放）
                page.insert_textbox(
                    rect,
                    translated_text,
                    fontsize=block["size"] * 0.9,  # 稍微缩小字体以避免溢出
                    fontname="china-s",  # 使用支持中文的字体
                    color=block["color"]
                )
                success_count += 1
            except Exception as e:
                # 如果 insert_textbox 失败，使用简单的 insert_text
                try:
                    page.insert_text(
                        fitz.Point(x0, y1),
                        translated_text,
                        fontsize=block["size"] * 0.8,
                        fontname="china-s",
                        color=block["color"]
                    )
                    success_count += 1
                except:
                    # 如果仍然失败，跳过此文本块
                    print(f"⚠️ 文本插入失败: {repr(translated_text[:30])}")

        print(f"✅ 成功插入 {success_count}/{len(text_blocks)} 个翻译文本")

    def translate(
        self,
        source_path: str,
        target_lang: str,
        ai_translator,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> str:
        """
        翻译 PDF 文档（同步包装器，调用异步方法）
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
            try:
                import fitz  # PyMuPDF
            except ImportError:
                raise ImportError(
                    "PDF 处理需要安装 PyMuPDF: pip install PyMuPDF"
                )

            # 打开原始 PDF
            doc = fitz.open(source_path)

            # 收集所有需要翻译的文本块
            all_text_blocks = []
            page_text_blocks = []

            for page_num, page in enumerate(doc):
                text_blocks = self._extract_text_blocks(page)
                page_text_blocks.append(text_blocks)
                all_text_blocks.extend([block["text"] for block in text_blocks])

            total_count = len(all_text_blocks)

            print(f"📄 PDF 翻译：共提取 {total_count} 个文本块")
            if total_count > 0:
                print(f"📝 第一个文本块: {repr(all_text_blocks[0][:50])}")

            # 翻译所有文本
            translated_texts = []
            batch_size = 20

            for i in range(0, total_count, batch_size):
                batch = all_text_blocks[i:i + batch_size]
                translated_batch = ai_translator.translate_batch(batch, target_lang)
                translated_texts.extend(translated_batch)

                if progress_callback:
                    progress_callback(min(i + batch_size, total_count), total_count)

            if total_count > 0:
                print(f"✅ 翻译完成，第一个翻译结果: {repr(translated_texts[0][:50])}")

            # 在原始 PDF 上替换文本
            text_index = 0
            for page_num, page in enumerate(doc):
                text_blocks = page_text_blocks[page_num]
                page_translations = []

                for block in text_blocks:
                    if text_index < len(translated_texts):
                        page_translations.append(translated_texts[text_index])
                        text_index += 1

                self._replace_text_on_page(page, text_blocks, page_translations)

            # 保存结果
            result_path = self._generate_result_path(source_path, ext='.pdf')
            doc.save(result_path)
            doc.close()

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
        异步翻译 PDF 文档（支持并发）

        Args:
            source_path: 源文件路径
            target_lang: 目标语言
            ai_translator: AI 翻译器实例
            thread_count: 并发线程数
            progress_callback: 进度回调函数

        Returns:
            str: 翻译结果文件路径
        """
        try:
            import fitz  # PyMuPDF
        except ImportError:
            raise ImportError(
                "PDF 处理需要安装 PyMuPDF: pip install PyMuPDF"
            )

        # 打开原始 PDF
        doc = fitz.open(source_path)

        # 收集所有需要翻译的文本块
        all_text_blocks = []
        page_text_blocks = []

        for page_num, page in enumerate(doc):
            text_blocks = self._extract_text_blocks(page)
            page_text_blocks.append(text_blocks)
            all_text_blocks.extend([block["text"] for block in text_blocks])

        total_count = len(all_text_blocks)

        print(f"📄 PDF 翻译（异步）：共提取 {total_count} 个文本块")
        if total_count > 0:
            print(f"📝 第一个文本块: {repr(all_text_blocks[0][:50])}")

        # 检查是否支持并发翻译
        if hasattr(ai_translator, 'translate_batch_async_concurrent'):
            # 使用并发翻译
            translated_texts = await ai_translator.translate_batch_async_concurrent(
                texts=all_text_blocks,
                target_lang=target_lang,
                max_concurrency=thread_count,
                progress_callback=progress_callback
            )
        else:
            # 降级到普通异步翻译
            translated_texts = []
            for i, text in enumerate(all_text_blocks):
                translated = await ai_translator.translate_text_async(text, target_lang)
                translated_texts.append(translated)

                if progress_callback:
                    progress_callback(i + 1, total_count)

        if total_count > 0:
            print(f"✅ 翻译完成，第一个翻译结果: {repr(translated_texts[0][:50])}")

        # 在原始 PDF 上替换文本
        text_index = 0
        for page_num, page in enumerate(doc):
            text_blocks = page_text_blocks[page_num]
            page_translations = []

            for block in text_blocks:
                if text_index < len(translated_texts):
                    page_translations.append(translated_texts[text_index])
                    text_index += 1

            self._replace_text_on_page(page, text_blocks, page_translations)

        # 保存结果
        result_path = self._generate_result_path(source_path, ext='.pdf')
        doc.save(result_path)
        doc.close()

        return result_path

    def _generate_result_path(self, source_path: str, ext: str = None) -> str:
        """生成结果文件路径"""
        source = Path(source_path)
        if ext is None:
            ext = source.suffix
        filename = f"{source.stem}_translated_{uuid.uuid4().hex[:8]}{ext}"
        return str(settings.TRANSLATE_DIR / filename)
