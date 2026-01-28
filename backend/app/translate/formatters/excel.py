"""
Excel 表格格式处理器
支持 .xlsx 文件的翻译，保持表格结构
"""
import uuid
from pathlib import Path
from typing import Callable, Optional
from openpyxl import load_workbook, Workbook
from openpyxl.utils import get_column_letter

from . import BaseFormatter
from ...config import settings


class ExcelFormatter(BaseFormatter):
    """
    Excel 表格处理器

    使用 openpyxl 库处理 Excel 文件
    保持表格结构、公式等
    """

    def translate(
        self,
        source_path: str,
        target_lang: str,
        ai_translator,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> str:
        """
        翻译 Excel 表格

        Args:
            source_path: 源文件路径
            target_lang: 目标语言
            ai_translator: AI 翻译器实例
            progress_callback: 进度回调函数

        Returns:
            str: 翻译结果文件路径
        """
        # 加载工作簿
        wb = load_workbook(source_path)

        # 收集所有需要翻译的文本单元格
        cells_to_translate = []
        for sheet in wb.worksheets:
            for row in sheet.iter_rows():
                for cell in row:
                    # 只翻译字符串类型的单元格
                    if cell.value and isinstance(cell.value, str) and cell.value.strip():
                        # 跳过公式
                        if not cell.value.startswith('='):
                            cells_to_translate.append({
                                'sheet': sheet,
                                'cell': cell,
                                'text': cell.value
                            })

        total_count = len(cells_to_translate)

        # 批量翻译
        batch_size = 20
        for i in range(0, total_count, batch_size):
            batch = cells_to_translate[i:i + batch_size]
            texts = [item['text'] for item in batch]

            # 翻译
            translated = ai_translator.translate_batch(texts, target_lang)

            # 更新单元格
            for j, item in enumerate(batch):
                if j < len(translated):
                    item['cell'].value = translated[j]

            # 更新进度
            if progress_callback:
                progress_callback(min(i + batch_size, total_count), total_count)

        # 保存结果
        result_path = self._generate_result_path(source_path)
        wb.save(result_path)
        wb.close()

        return result_path

    def _generate_result_path(self, source_path: str) -> str:
        """生成结果文件路径"""
        source = Path(source_path)
        filename = f"{source.stem}_translated_{uuid.uuid4().hex[:8]}{source.suffix}"
        return str(settings.TRANSLATE_DIR / filename)
