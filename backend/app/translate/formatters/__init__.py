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

    @abstractmethod
    async def translate_async(
        self,
        source_path: str,
        target_lang: str,
        ai_translator,
        thread_count: int = 5,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> str:
        """
        异步执行翻译（支持并发）

        Args:
            source_path: 源文件路径
            target_lang: 目标语言
            ai_translator: AI 翻译器实例
            thread_count: 并发线程数
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

    @abstractmethod
    def extract_content(self, file_path: str, max_chars: int = 5000) -> dict:
        """
        提取文件内容用于预览

        Args:
            file_path: 文件路径
            max_chars: 最大提取字符数（防止文件过大）

        Returns:
            dict: 包含以下字段：
                - content: 文本内容列表，每项包含 {type, text, index} 
                - total_chars: 总字符数
                - truncated: 是否被截断
                - format: 文件格式
        """
        pass
