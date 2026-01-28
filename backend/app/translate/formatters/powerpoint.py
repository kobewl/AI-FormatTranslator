"""
PowerPoint 演示文稿格式处理器
支持 .pptx 文件的翻译，保持格式
"""
import uuid
from pathlib import Path
from typing import Callable, Optional
from pptx import Presentation

from . import BaseFormatter
from ...config import settings


class PowerPointFormatter(BaseFormatter):
    """
    PowerPoint 演示文稿处理器

    使用 python-pptx 库处理 PowerPoint 文件
    保持幻灯片布局、格式等
    """

    def translate(
        self,
        source_path: str,
        target_lang: str,
        ai_translator,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> str:
        """
        翻译 PowerPoint 演示文稿

        Args:
            source_path: 源文件路径
            target_lang: 目标语言
            ai_translator: AI 翻译器实例
            progress_callback: 进度回调函数

        Returns:
            str: 翻译结果文件路径
        """
        # 加载演示文稿
        prs = Presentation(source_path)

        # 收集所有需要翻译的文本
        texts_to_translate = []
        for slide in prs.slides:
            for shape in slide.shapes:
                if hasattr(shape, "text") and shape.text.strip():
                    texts_to_translate.append({
                        'shape': shape,
                        'text': shape.text
                    })

        total_count = len(texts_to_translate)

        # 批量翻译
        batch_size = 10
        for i in range(0, total_count, batch_size):
            batch = texts_to_translate[i:i + batch_size]
            texts = [item['text'] for item in batch]

            # 翻译
            translated = ai_translator.translate_batch(texts, target_lang)

            # 更新文本框
            for j, item in enumerate(batch):
                if j < len(translated):
                    # 保持格式，只更新文本
                    text_frame = item['shape'].text_frame
                    text_frame.text = translated[j]

            # 更新进度
            if progress_callback:
                progress_callback(min(i + batch_size, total_count), total_count)

        # 保存结果
        result_path = self._generate_result_path(source_path)
        prs.save(result_path)

        return result_path

    def _generate_result_path(self, source_path: str) -> str:
        """生成结果文件路径"""
        source = Path(source_path)
        filename = f"{source.stem}_translated_{uuid.uuid4().hex[:8]}{source.suffix}"
        return str(settings.TRANSLATE_DIR / filename)
