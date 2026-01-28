"""
DocTranslator 配置文件
使用 Pydantic Settings 管理配置（FastAPI 推荐方式）
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import Optional, Union, List
from pathlib import Path


class Settings(BaseSettings):
    """应用配置类"""

    # 应用基础配置
    APP_NAME: str = "DocTranslator API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    API_PREFIX: str = "/api"

    # 安全配置
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    JWT_SECRET_KEY: str = "jwt-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7天

    # 数据库配置
    DATABASE_URL: str = "mysql+pymysql://root:password@localhost:3306/doc_translator?charset=utf8mb4"
    DATABASE_ECHO: bool = False

    # CORS 配置
    CORS_ORIGINS: list = ["*"]  # 生产环境应该指定具体域名
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list = ["*"]
    CORS_ALLOW_HEADERS: list = ["*"]

    # 文件上传配置（单位：MB，从 .env 读取）
    MAX_FILE_SIZE: int = 30  # 最大文件大小（MB）
    MAX_USER_STORAGE: int = 100  # 用户最大存储空间（MB）

    # 文件上传相关（自动计算为字节）
    @property
    def MAX_UPLOAD_SIZE(self) -> int:
        """最大上传大小（字节）"""
        return self.MAX_FILE_SIZE * 1024 * 1024

    @property
    def MAX_USER_STORAGE_BYTES(self) -> int:
        """用户最大存储空间（字节）"""
        return self.MAX_USER_STORAGE * 1024 * 1024

    ALLOWED_EXTENSIONS: set = {"docx", "pdf", "xlsx", "pptx", "md", "txt"}

    # 存储路径配置
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    STORAGE_DIR: Path = BASE_DIR / "storage"
    UPLOAD_DIR: Path = STORAGE_DIR / "uploads"
    TRANSLATE_DIR: Path = STORAGE_DIR / "translate"

    # 日志配置
    LOG_LEVEL: str = "INFO"  # 日志级别：DEBUG, INFO, WARNING, ERROR, CRITICAL
    LOG_DIR: Path = BASE_DIR / "logs"  # 日志文件目录
    LOG_MAX_BYTES: int = 10 * 1024 * 1024  # 单个日志文件最大大小（10MB）
    LOG_BACKUP_COUNT: int = 10  # 保留的日志备份文件数量

    # AI 翻译配置
    OPENAI_API_KEY: str = ""
    OPENAI_API_BASE: str = "https://api.openai.com/v1"
    OPENAI_MODEL: str = "gpt-3.5-turbo"
    OPENAI_TIMEOUT: int = 60

    # 邮箱配置
    MAIL_SERVER: str = "smtp.qq.com"
    MAIL_PORT: int = 587
    MAIL_USE_TLS: bool = True
    MAIL_USERNAME: str = ""
    MAIL_PASSWORD: str = ""
    MAIL_DEFAULT_SENDER: str = ""
    ALLOWED_EMAIL_DOMAINS: Union[str, List[str]] = "qq.com,163.com,126.com"

    # Redis 配置（可选）
    REDIS_URL: Optional[str] = None

    # 分页配置
    DEFAULT_PAGE: int = 1
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    @field_validator('ALLOWED_EMAIL_DOMAINS', mode='before')
    @classmethod
    def parse_email_domains(cls, v):
        """解析邮箱域名配置（支持逗号分隔的字符串）"""
        if isinstance(v, str):
            return [domain.strip() for domain in v.split(',')]
        return v

    @field_validator('CORS_ORIGINS', mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        """解析 CORS 来源配置（支持 JSON 字符串或逗号分隔）"""
        if isinstance(v, str):
            # 尝试解析 JSON 格式
            if v.startswith('[') and v.endswith(']'):
                import json
                try:
                    return json.loads(v)
                except:
                    pass
            # 否则按逗号分隔
            return [origin.strip() for origin in v.split(',')]
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra='ignore'  # 忽略 .env 中额外定义的字段
    )


# 创建配置实例
settings = Settings()

# 确保存储目录存在
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
settings.TRANSLATE_DIR.mkdir(parents=True, exist_ok=True)

# 确保日志目录存在
settings.LOG_DIR.mkdir(parents=True, exist_ok=True)
