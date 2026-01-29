"""
Redis 工具类
用于存储实时进度数据，避免数据库事务隔离问题
"""
import redis
import json
from typing import Optional, Dict, Any
from ..config import settings


class RedisClient:
    """Redis 客户端单例"""

    _instance: Optional[redis.Redis] = None

    @classmethod
    def get_client(cls) -> redis.Redis:
        """获取 Redis 客户端实例"""
        if cls._instance is None:
            # 从配置文件读取 Redis 连接参数
            cls._instance = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            # 测试连接
            try:
                cls._instance.ping()
                print(f"✅ Redis 连接成功 (host={settings.REDIS_HOST}, port={settings.REDIS_PORT})")
            except Exception as e:
                print(f"⚠️ Redis 连接失败: {e}")
                print("💡 提示：请启动 Redis 服务：")
                print("   方法1: brew services start redis")
                print("   方法2: redis-server")
                cls._instance = None

        return cls._instance

    @classmethod
    def set_translate_progress(cls, task_id: int, progress_data: Dict[str, Any]) -> bool:
        """
        设置翻译进度

        Args:
            task_id: 任务ID
            progress_data: 进度数据

        Returns:
            bool: 是否设置成功
        """
        client = cls.get_client()
        if client is None:
            return False

        try:
            key = f"translate_progress:{task_id}"
            # 设置过期时间为1小时
            client.setex(key, 3600, json.dumps(progress_data))
            return True
        except Exception as e:
            print(f"❌ Redis 设置进度失败: {e}")
            return False

    @classmethod
    def get_translate_progress(cls, task_id: int) -> Optional[Dict[str, Any]]:
        """
        获取翻译进度

        Args:
            task_id: 任务ID

        Returns:
            Optional[Dict]: 进度数据
        """
        client = cls.get_client()
        if client is None:
            return None

        try:
            key = f"translate_progress:{task_id}"
            data = client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            print(f"❌ Redis 获取进度失败: {e}")
            return None

    @classmethod
    def delete_translate_progress(cls, task_id: int) -> bool:
        """
        删除翻译进度

        Args:
            task_id: 任务ID

        Returns:
            bool: 是否删除成功
        """
        client = cls.get_client()
        if client is None:
            return False

        try:
            key = f"translate_progress:{task_id}"
            client.delete(key)
            return True
        except Exception as e:
            print(f"❌ Redis 删除进度失败: {e}")
            return False
