"""
增强的 AI 翻译服务
支持缓存、备份模型、重试机制
"""
import hashlib
import asyncio
import re
import time
from typing import List, Optional, Dict, Any
from datetime import datetime
from openai import AsyncOpenAI, OpenAI
from sqlalchemy.orm import Session

from ...models.translate_log import TranslateLog


class EnhancedAITranslator:
    """
    增强的 AI 翻译器

    新增功能：
    - 翻译结果缓存（避免重复翻译）
    - 备份模型支持（主模型失败时自动切换）
    - 自动重试机制（最多3次）
    - DeepSeek 思考过程过滤
    - 速率限制处理
    """

    def __init__(
        self,
        api_key: str,
        api_base: str = "https://api.openai.com/v1",
        model: str = "gpt-3.5-turbo",
        backup_model: Optional[str] = None,
        timeout: int = 60,
        db: Optional[Session] = None
    ):
        """
        初始化增强的 AI 翻译器

        Args:
            api_key: API 密钥
            api_base: API 基础 URL
            model: 主模型
            backup_model: 备份模型
            timeout: 超时时间（秒）
            db: 数据库会话（用于缓存）
        """
        self.api_key = api_key
        self.api_base = api_base
        self.model = model
        self.backup_model = backup_model
        self.timeout = timeout
        self.db = db

        # 当前使用的模型（可能是备份模型）
        self.current_model = model

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

    def _generate_md5_key(self, text: str, target_lang: str) -> str:
        """
        生成 MD5 哈希键用于缓存

        Args:
            text: 原文
            target_lang: 目标语言

        Returns:
            str: MD5 哈希值
        """
        content = f"{self.api_key}{self.api_base}{text}{self.model}{self.backup_model}{target_lang}"
        return hashlib.md5(content.encode('utf-8')).hexdigest()

    def _check_cache(self, text: str, target_lang: str) -> Optional[str]:
        """
        检查缓存中是否有翻译结果

        Args:
            text: 原文
            target_lang: 目标语言

        Returns:
            缓存的翻译结果，如果没有返回 None
        """
        if not self.db:
            return None

        try:
            md5_key = self._generate_md5_key(text, target_lang)
            log = self.db.query(TranslateLog).filter_by(md5_key=md5_key).first()

            if log:
                print(f"✅ 命中缓存: {text[:30]}...")
                return log.content

            return None
        except Exception as e:
            print(f"❌ 缓存查询失败: {str(e)}")
            return None

    def _save_cache(self, text: str, target_lang: str, content: str):
        """
        保存翻译结果到缓存

        Args:
            text: 原文
            target_lang: 目标语言
            content: 译文
        """
        if not self.db:
            return

        try:
            md5_key = self._generate_md5_key(text, target_lang)
            log = TranslateLog(
                md5_key=md5_key,
                api_url=self.api_base,
                api_key=self.api_key,
                model=self.model,
                backup_model=self.backup_model,
                target_lang=target_lang,
                source=text,
                content=content
            )
            self.db.add(log)
            self.db.commit()
        except Exception as e:
            print(f"❌ 缓存保存失败: {str(e)}")

    def _filter_deepseek_thought(self, text: str) -> str:
        """
        过滤 DeepSeek 思考过程标签

        Args:
            text: 翻译结果

        Returns:
            过滤后的文本
        """
        # 移除 <think>...</think> 标签及其内容
        pattern = r'<think>.*?</think>'
        return re.sub(pattern, '', text, flags=re.DOTALL).strip()

    def _build_translation_prompt(self, text: str, target_lang: str) -> str:
        """
        构建翻译提示词

        Args:
            text: 要翻译的文本
            target_lang: 目标语言

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
            "ru": "俄文"
        }

        target_name = lang_names.get(target_lang, target_lang)

        return f"请将以下文本翻译成{target_name}，只返回翻译结果，不要添加任何解释：\n\n{text}"

    def _call_openai_api(self, text: str, target_lang: str, use_backup: bool = False) -> str:
        """
        调用 OpenAI API 进行翻译

        Args:
            text: 要翻译的文本
            target_lang: 目标语言
            use_backup: 是否使用备份模型

        Returns:
            str: 翻译结果
        """
        model = self.backup_model if use_backup else self.current_model
        prompt = self._build_translation_prompt(text, target_lang)

        try:
            response = self.client.chat.completions.create(
                model=model,
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

            content = response.choices[0].message.content.strip()

            # 过滤 DeepSeek 思考过程
            content = self._filter_deepseek_thought(content)

            print(f"✅ 翻译成功（{model}）: {text[:30]}...")

            return content

        except Exception as e:
            print(f"❌ API 调用失败（{model}）: {str(e)}")
            raise

    def translate_text(self, text: str, target_lang: str) -> str:
        """
        翻译单个文本（带缓存、重试、备份模型）

        Args:
            text: 要翻译的文本
            target_lang: 目标语言

        Returns:
            str: 翻译结果
        """
        if not text or not text.strip():
            return text

        # 1. 检查缓存
        cached = self._check_cache(text, target_lang)
        if cached:
            return cached

        # 2. 尝试翻译（带重试和备份模型）
        max_retries = 3
        last_error = None

        for attempt in range(max_retries):
            try:
                # 先尝试主模型
                content = self._call_openai_api(text, target_lang, use_backup=False)

                # 保存到缓存
                self._save_cache(text, target_lang, content)

                return content

            except Exception as e:
                last_error = str(e)
                error_type = type(e).__name__

                print(f"⚠️  第 {attempt + 1} 次尝试失败 ({error_type}): {last_error}")

                # 如果是速率限制或认证错误，尝试备份模型
                if error_type in ['RateLimitError', 'AuthenticationError', 'PermissionDeniedError']:
                    if self.backup_model and self.current_model != self.backup_model:
                        print(f"🔄 切换到备份模型: {self.backup_model}")
                        self.current_model = self.backup_model

                        # 等待1秒后重试
                        time.sleep(1)

                        # 使用备份模型重试
                        content = self._call_openai_api(text, target_lang, use_backup=True)

                        # 保存到缓存
                        self._save_cache(text, target_lang, content)

                        # 恢复主模型
                        self.current_model = self.model

                        return content

                # 最后一次尝试失败
                if attempt == max_retries - 1:
                    print(f"❌ 翻译最终失败，返回原文: {text[:30]}...")
                    return text

                # 等待5秒后重试
                time.sleep(5)

        return text

    def translate_batch(self, texts: List[str], target_lang: str) -> List[str]:
        """
        批量翻译文本

        Args:
            texts: 要翻译的文本列表
            target_lang: 目标语言

        Returns:
            List[str]: 翻译结果列表
        """
        results = []

        for text in texts:
            if text and text.strip():
                translated = self.translate_text(text, target_lang)
                results.append(translated)
            else:
                results.append(text)

        return results

    async def _call_openai_api_async(self, text: str, target_lang: str, use_backup: bool = False) -> str:
        """
        异步调用 OpenAI API 进行翻译

        Args:
            text: 要翻译的文本
            target_lang: 目标语言
            use_backup: 是否使用备份模型

        Returns:
            str: 翻译结果
        """
        model = self.backup_model if use_backup else self.current_model
        prompt = self._build_translation_prompt(text, target_lang)

        try:
            response = await self.async_client.chat.completions.create(
                model=model,
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

            content = response.choices[0].message.content.strip()

            # 过滤 DeepSeek 思考过程
            content = self._filter_deepseek_thought(content)

            print(f"✅ 翻译成功（{model}）: {text[:30]}...")

            return content

        except Exception as e:
            print(f"❌ API 调用失败（{model}）: {str(e)}")
            raise

    async def translate_text_async(self, text: str, target_lang: str) -> str:
        """
        异步翻译单个文本（带缓存、重试、备份模型）

        Args:
            text: 要翻译的文本
            target_lang: 目标语言

        Returns:
            str: 翻译结果
        """
        if not text or not text.strip():
            return text

        # 1. 检查缓存
        cached = self._check_cache(text, target_lang)
        if cached:
            return cached

        # 2. 尝试翻译（带重试和备份模型）
        max_retries = 3
        last_error = None

        for attempt in range(max_retries):
            try:
                # 先尝试主模型
                content = await self._call_openai_api_async(text, target_lang, use_backup=False)

                # 保存到缓存
                self._save_cache(text, target_lang, content)

                return content

            except Exception as e:
                last_error = str(e)
                error_type = type(e).__name__

                print(f"⚠️  第 {attempt + 1} 次尝试失败 ({error_type}): {last_error}")

                # 如果是速率限制或认证错误，尝试备份模型
                if error_type in ['RateLimitError', 'AuthenticationError', 'PermissionDeniedError']:
                    if self.backup_model and self.current_model != self.backup_model:
                        print(f"🔄 切换到备份模型: {self.backup_model}")
                        self.current_model = self.backup_model

                        # 等待1秒后重试
                        await asyncio.sleep(1)

                        # 使用备份模型重试
                        content = await self._call_openai_api_async(text, target_lang, use_backup=True)

                        # 保存到缓存
                        self._save_cache(text, target_lang, content)

                        # 恢复主模型
                        self.current_model = self.model

                        return content

                # 最后一次尝试失败
                if attempt == max_retries - 1:
                    print(f"❌ 翻译最终失败，返回原文: {text[:30]}...")
                    return text

                # 等待5秒后重试
                await asyncio.sleep(5)

        return text

    async def translate_batch_async_concurrent(
        self,
        texts: List[str],
        target_lang: str,
        max_concurrency: int = 5,
        progress_callback: Optional[callable] = None
    ) -> List[str]:
        """
        并发批量翻译，使用 Semaphore 控制并发数

        Args:
            texts: 要翻译的文本列表
            target_lang: 目标语言
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
                result = await self.translate_text_async(text, target_lang)
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
