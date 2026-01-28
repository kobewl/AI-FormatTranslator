"""
Markdown 文档格式处理器
支持 .md 文件的翻译，保持 Markdown 格式
"""
import uuid
import re
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
        翻译 Markdown 文档

        Args:
            source_path: 源文件路径
            target_lang: 目标语言
            ai_translator: AI 翻译器实例
            progress_callback: 进度回调函数

        Returns:
            str: 翻译结果文件路径
        """
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
