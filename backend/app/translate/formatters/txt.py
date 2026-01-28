"""
TXT 文本格式处理器
支持 .txt 文件的翻译
"""
import uuid
from pathlib import Path
from typing import Callable, Optional

from . import BaseFormatter
from ...config import settings


class TxtFormatter(BaseFormatter):
    """
    TXT 文本处理器

    最简单的格式处理器
    按段落或行进行翻译
    """

    def translate(
        self,
        source_path: str,
        target_lang: str,
        ai_translator,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> str:
        """
        翻译 TXT 文本文件

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

        # 按段落分割（空行分隔）
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        total_count = len(paragraphs)

        # 批量翻译
        translated_paragraphs = []
        batch_size = 10

        for i in range(0, total_count, batch_size):
            batch = paragraphs[i:i + batch_size]

            # 翻译
            translated = ai_translator.translate_batch(batch, target_lang)
            translated_paragraphs.extend(translated)

            # 更新进度
            if progress_callback:
                progress_callback(min(i + batch_size, total_count), total_count)

        # 重建文本（保持空行分隔）
        result_content = '\n\n'.join(translated_paragraphs)

        # 保存结果
        result_path = self._generate_result_path(source_path)
        with open(result_path, 'w', encoding='utf-8') as f:
            f.write(result_content)

        return result_path

    def _generate_result_path(self, source_path: str) -> str:
        """生成结果文件路径"""
        source = Path(source_path)
        filename = f"{source.stem}_translated_{uuid.uuid4().hex[:8]}{source.suffix}"
        return str(settings.TRANSLATE_DIR / filename)
