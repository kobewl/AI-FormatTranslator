"""
格式处理器基类
定义所有格式处理器的通用接口
"""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Callable, Optional


class BaseFormatter(ABC):
    """
    格式处理器基类

    所有具体的格式处理器都应该继承此类并实现 translate 方法
    """

    @abstractmethod
    def translate(
        self,
        source_path: str,
        target_lang: str,
        ai_translator,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> str:
        """
        执行翻译

        Args:
            source_path: 源文件路径
            target_lang: 目标语言
            ai_translator: AI 翻译器实例
            progress_callback: 进度回调函数

        Returns:
            str: 翻译结果文件路径
        """
        pass

    def _save_result(self, content: str, output_path: str):
        """
        保存翻译结果

        Args:
            content: 翻译内容
            output_path: 输出路径
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
