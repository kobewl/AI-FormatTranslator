"""
Markdown 文档格式处理器
支持 .md 文件的翻译，保持 Markdown 格式
"""
import uuid
import re
import asyncio
from pathlib import Path
from typing import Callable, Optional

from . import BaseFormatter
from ...config import settings


class MarkdownFormatter(BaseFormatter):
    """
    Markdown 文档处理器

    保持 Markdown 格式（标题、列表、代码块等）
    只翻译文本内容，不翻译标记符号
    """

    def translate(
        self,
        source_path: str,
        target_lang: str,
        ai_translator,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> str:
        """
        翻译 Markdown 文档（同步包装器，调用异步方法）

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
            # 读取文件
            with open(source_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 解析 Markdown 为段落
            paragraphs = self._parse_markdown(content)

            # 翻译
            translated_paragraphs = []
            total = len(paragraphs)

            for i, para in enumerate(paragraphs):
                if para['text'].strip():
                    # 翻译文本
                    translated = ai_translator.translate_text(para['text'], target_lang)
                    translated_paragraphs.append({
                        'prefix': para['prefix'],
                        'text': translated,
                        'suffix': para['suffix']
                    })
                else:
                    # 空行，保持原样
                    translated_paragraphs.append(para)

                if progress_callback:
                    progress_callback(i + 1, total)

            # 重建 Markdown
            result_content = self._rebuild_markdown(translated_paragraphs)

            # 保存结果
            result_path = self._generate_result_path(source_path)
            with open(result_path, 'w', encoding='utf-8') as f:
                f.write(result_content)

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
        异步翻译 Markdown 文档（支持并发）

        Args:
            source_path: 源文件路径
            target_lang: 目标语言
            ai_translator: AI 翻译器实例
            thread_count: 并发线程数
            progress_callback: 进度回调函数

        Returns:
            str: 翻译结果文件路径
        """
        # 读取文件
        with open(source_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 解析 Markdown 为段落
        paragraphs = self._parse_markdown(content)

        # 收集需要翻译的段落
        texts_to_translate = [para['text'] for para in paragraphs if para['text'].strip()]

        # 检查是否支持并发翻译
        if hasattr(ai_translator, 'translate_batch_async_concurrent'):
            # 使用并发翻译
            translated_texts = await ai_translator.translate_batch_async_concurrent(
                texts=texts_to_translate,
                target_lang=target_lang,
                max_concurrency=thread_count,
                progress_callback=progress_callback
            )
        else:
            # 降级到普通异步翻译
            translated_texts = []
            for text in texts_to_translate:
                translated = await ai_translator.translate_text_async(text, target_lang)
                translated_texts.append(translated)

        # 重建翻译结果
        translated_paragraphs = []
        text_index = 0
        for para in paragraphs:
            if para['text'].strip():
                translated_paragraphs.append({
                    'prefix': para['prefix'],
                    'text': translated_texts[text_index],
                    'suffix': para['suffix']
                })
                text_index += 1
            else:
                # 空行，保持原样
                translated_paragraphs.append(para)

        # 重建 Markdown
        result_content = self._rebuild_markdown(translated_paragraphs)

        # 保存结果
        result_path = self._generate_result_path(source_path)
        with open(result_path, 'w', encoding='utf-8') as f:
            f.write(result_content)

        return result_path

    def _parse_markdown(self, content: str) -> list:
        """
        解析 Markdown 为段落

        Args:
            content: Markdown 内容

        Returns:
            list: 段落列表
        """
        paragraphs = []

        # 按行分割
        lines = content.split('\n')

        current_para = {
            'prefix': '',
            'text': '',
            'suffix': ''
        }

        for line in lines:
            # 检测标题
            if line.startswith('#'):
                if current_para['text']:
                    paragraphs.append(current_para)
                # 提取标题标记
                match = re.match(r'^(#+\s*)(.*)$', line)
                if match:
                    current_para = {
                        'prefix': match.group(1),
                        'text': match.group(2),
                        'suffix': ''
                    }
                else:
                    current_para = {'prefix': '', 'text': line, 'suffix': ''}
            # 检测代码块
            elif line.startswith('```'):
                if current_para['text']:
                    paragraphs.append(current_para)
                paragraphs.append({'prefix': '', 'text': line, 'suffix': '', 'is_code': True})
                current_para = {'prefix': '', 'text': '', 'suffix': ''}
            # 检测列表
            elif line.startswith(('-', '*', '+')) or re.match(r'^\d+\.', line):
                if current_para['text']:
                    paragraphs.append(current_para)
                match = re.match(r'^(\s*[-*+\d+.]\s+)(.*)$', line)
                if match:
                    current_para = {
                        'prefix': match.group(1),
                        'text': match.group(2),
                        'suffix': ''
                    }
                else:
                    current_para = {'prefix': '', 'text': line, 'suffix': ''}
            # 普通段落
            else:
                if line.strip():
                    if current_para['text']:
                        current_para['text'] += '\n' + line
                    else:
                        current_para['text'] = line
                else:
                    if current_para['text']:
                        paragraphs.append(current_para)
                    paragraphs.append({'prefix': '', 'text': '', 'suffix': ''})
                    current_para = {'prefix': '', 'text': '', 'suffix': ''}

        if current_para['text']:
            paragraphs.append(current_para)

        return paragraphs

    def _rebuild_markdown(self, paragraphs: list) -> str:
        """
        从段落重建 Markdown

        Args:
            paragraphs: 段落列表

        Returns:
            str: Markdown 内容
        """
        lines = []
        for para in paragraphs:
            if para.get('is_code'):
                lines.append(para['text'])
            else:
                line = para['prefix'] + para['text'] + para['suffix']
                lines.append(line)
        return '\n'.join(lines)

    def _generate_result_path(self, source_path: str) -> str:
        """生成结果文件路径"""
        source = Path(source_path)
        filename = f"{source.stem}_translated_{uuid.uuid4().hex[:8]}{source.suffix}"
        return str(settings.TRANSLATE_DIR / filename)

    def extract_content(self, file_path: str, max_chars: int = 5000) -> dict:
        """
        提取 Markdown 文件内容用于预览

        Args:
            file_path: 文件路径
            max_chars: 最大提取字符数

        Returns:
            dict: 包含 content 列表、total_chars、truncated、format
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 解析 Markdown
            paragraphs = self._parse_markdown(content)

            # 构建内容列表
            content_list = []
            total_chars = 0
            truncated = False

            for idx, para in enumerate(paragraphs):
                text = para['text'].strip()
                if not text:
                    continue

                # 判断类型
                if para.get('is_code'):
                    item_type = 'code'
                elif para['prefix'].startswith('#'):
                    item_type = 'heading'
                elif para['prefix'].strip() and para['prefix'].strip()[0] in '-*+':
                    item_type = 'list'
                elif re.match(r'^\d+\.', para['prefix'].strip()):
                    item_type = 'list'
                else:
                    item_type = 'paragraph'

                if total_chars + len(text) > max_chars:
                    remaining = max_chars - total_chars
                    if remaining > 0:
                        content_list.append({
                            'type': item_type,
                            'text': text[:remaining],
                            'index': idx,
                            'prefix': para['prefix']
                        })
                    truncated = True
                    break

                content_list.append({
                    'type': item_type,
                    'text': text,
                    'index': idx,
                    'prefix': para['prefix']
                })
                total_chars += len(text)

            return {
                'content': content_list,
                'total_chars': total_chars,
                'truncated': truncated,
                'format': 'markdown',
                'total_paragraphs': len([p for p in paragraphs if p['text'].strip()])
            }
        except Exception as e:
            return {
                'content': [],
                'total_chars': 0,
                'truncated': False,
                'format': 'markdown',
                'error': str(e)
            }
