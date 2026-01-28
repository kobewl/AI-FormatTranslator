"""
AI 翻译服务
使用 OpenAI 兼容 API 进行翻译
"""
import asyncio
import time
from typing import List, Optional
from openai import AsyncOpenAI, OpenAI


class AITranslator:
    """
    AI 翻译器

    使用 OpenAI 兼容的 API 进行文本翻译
    支持单文本翻译和批量翻译
    """

    def __init__(
        self,
        api_key: str,
        api_base: str = "https://api.openai.com/v1",
        model: str = "gpt-3.5-turbo",
        timeout: int = 60
    ):
        """
        初始化 AI 翻译器

        Args:
            api_key: API 密钥
            api_base: API 基础 URL
            model: 使用的模型
            timeout: 超时时间（秒）
        """
        self.api_key = api_key
        self.api_base = api_base
        self.model = model
        self.timeout = timeout

        # 创建同步和异步客户端
        self.client = OpenAI(
            api_key=api_key,
            base_url=api_base,
            timeout=timeout
        )
        self.async_client = AsyncOpenAI(
            api_key=api_key,
            base_url=api_base,
            timeout=timeout
        )

    def translate_text(
        self,
        text: str,
        target_lang: str,
        source_lang: str = "auto"
    ) -> str:
        """
        翻译单个文本

        Args:
            text: 要翻译的文本
            target_lang: 目标语言
            source_lang: 源语言（auto 表示自动检测）

        Returns:
            str: 翻译结果
        """
        if not text or not text.strip():
            return text

        # 构建提示词
        prompt = self._build_translation_prompt(text, target_lang, source_lang)

        try:
            # 调用 API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个专业的翻译助手。请准确翻译用户提供的文本，保持原文的意思和语气。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,  # 降低温度以获得更一致的翻译
                max_tokens=4000
            )

            # 提取翻译结果
            content = response.choices[0].message.content
            print(f"DEBUG: API 返回类型={type(content)}, 内容={repr(content)}")

            # 确保返回的是字符串
            if content is None:
                print("WARNING: API 返回了 None，使用原文")
                return text

            # 如果是字符串，直接返回
            if isinstance(content, str):
                return content.strip()

            # 如果是其他类型，尝试转换为字符串
            print(f"WARNING: API 返回了非字符串类型 {type(content)}，尝试转换")
            return str(content)

        except Exception as e:
            print(f"翻译失败: {str(e)}")
            import traceback
            traceback.print_exc()
            # 失败时返回原文
            return text

    def translate_batch(
        self,
        texts: List[str],
        target_lang: str,
        source_lang: str = "auto"
    ) -> List[str]:
        """
        批量翻译文本

        Args:
            texts: 要翻译的文本列表
            target_lang: 目标语言
            source_lang: 源语言

        Returns:
            List[str]: 翻译结果列表
        """
        results = []

        for i, text in enumerate(texts):
            if text and text.strip():
                # 使用重试机制翻译每个文本
                translated = self._translate_with_retry(
                    text, target_lang, source_lang, max_retries=3
                )
                results.append(translated)

                # 已移除延迟以提高翻译速度
            else:
                results.append(text)

        return results

    def _translate_with_retry(
        self,
        text: str,
        target_lang: str,
        source_lang: str,
        max_retries: int = 3
    ) -> str:
        """
        带重试机制的翻译方法

        Args:
            text: 要翻译的文本
            target_lang: 目标语言
            source_lang: 源语言
            max_retries: 最大重试次数

        Returns:
            str: 翻译结果
        """
        last_error = None

        for attempt in range(max_retries):
            try:
                return self.translate_text(text, target_lang, source_lang)

            except Exception as e:
                last_error = e
                error_str = str(e)

                # 检查是否是 429 限流错误
                if '429' in error_str or 'rate_limit' in error_str.lower():
                    if attempt < max_retries - 1:  # 不是最后一次尝试
                        # 计算等待时间：指数退避策略
                        # 第一次重试等待 5 秒，第二次 10 秒，第三次 20 秒
                        wait_time = 5 * (2 ** attempt)
                        print(f"⚠️ 遇到 API 限流，等待 {wait_time} 秒后重试... (尝试 {attempt + 1}/{max_retries})")
                        time.sleep(wait_time)
                        continue

                # 其他错误或最后一次尝试失败，直接返回原文
                print(f"❌ 翻译失败: {str(e)}")
                return text

        # 所有重试都失败，返回原文
        return text

    async def translate_text_async(
        self,
        text: str,
        target_lang: str,
        source_lang: str = "auto"
    ) -> str:
        """
        异步翻译单个文本

        Args:
            text: 要翻译的文本
            target_lang: 目标语言
            source_lang: 源语言

        Returns:
            str: 翻译结果
        """
        if not text or not text.strip():
            return text

        # 构建提示词
        prompt = self._build_translation_prompt(text, target_lang, source_lang)

        try:
            # 调用 API
            response = await self.async_client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个专业的翻译助手。请准确翻译用户提供的文本，保持原文的意思和语气。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=4000
            )

            # 提取翻译结果
            translated_text = response.choices[0].message.content.strip()
            return translated_text

        except Exception as e:
            print(f"翻译失败: {str(e)}")
            return text

    async def translate_batch_async(
        self,
        texts: List[str],
        target_lang: str,
        source_lang: str = "auto"
    ) -> List[str]:
        """
        异步批量翻译文本

        Args:
            texts: 要翻译的文本列表
            target_lang: 目标语言
            source_lang: 源语言

        Returns:
            List[str]: 翻译结果列表
        """
        # 创建并发任务
        tasks = [
            self.translate_text_async(text, target_lang, source_lang)
            for text in texts
        ]

        # 并发执行
        results = await asyncio.gather(*tasks)
        return results

    async def translate_batch_async_concurrent(
        self,
        texts: List[str],
        target_lang: str,
        source_lang: str = "auto",
        max_concurrency: int = 5,
        progress_callback: Optional[callable] = None
    ) -> List[str]:
        """
        并发批量翻译，使用 Semaphore 控制并发数

        Args:
            texts: 要翻译的文本列表
            target_lang: 目标语言
            source_lang: 源语言
            max_concurrency: 最大并发数
            progress_callback: 进度回调函数

        Returns:
            List[str]: 翻译结果列表（保持原始顺序）
        """
        # 创建信号量控制并发数
        semaphore = asyncio.Semaphore(max_concurrency)

        async def translate_with_semaphore(text: str, index: int) -> tuple[int, str]:
            """在信号量控制下进行翻译"""
            async with semaphore:
                result = await self.translate_text_async(text, target_lang, source_lang)
                if progress_callback:
                    progress_callback(index + 1, len(texts))
                return (index, result)

        # 创建所有翻译任务
        tasks = [
            translate_with_semaphore(text, i)
            for i, text in enumerate(texts)
            if text and text.strip()
        ]

        # 并发执行所有任务
        results = await asyncio.gather(*tasks)

        # 按原始顺序返回结果
        sorted_results = list(texts)
        for index, result in results:
            sorted_results[index] = result

        return sorted_results

    def _build_translation_prompt(
        self,
        text: str,
        target_lang: str,
        source_lang: str
    ) -> str:
        """
        构建翻译提示词

        Args:
            text: 要翻译的文本
            target_lang: 目标语言
            source_lang: 源语言

        Returns:
            str: 提示词
        """
        # 语言代码映射
        lang_names = {
            "zh": "中文",
            "en": "英文",
            "ja": "日文",
            "ko": "韩文",
            "fr": "法文",
            "de": "德文",
            "es": "西班牙文",
            "ru": "俄文",
            "ar": "阿拉伯文",
            "pt": "葡萄牙文"
        }

        # 获取语言名称
        target_name = lang_names.get(target_lang, target_lang)

        if source_lang == "auto":
            prompt = f"请将以下文本翻译成{target_name}，只返回翻译结果，不要添加任何解释：\n\n{text}"
        else:
            source_name = lang_names.get(source_lang, source_lang)
            prompt = f"请将以下{source_name}文本翻译成{target_name}，只返回翻译结果，不要添加任何解释：\n\n{text}"

        return prompt

    def __del__(self):
        """清理资源"""
        try:
            self.client.close()
            asyncio.get_event_loop().run_until_complete(self.async_client.close())
        except:
            pass
