"""
翻译相关的 Pydantic 模式
定义翻译请求和响应的数据结构
"""
from typing import Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field


class TranslateRequest(BaseModel):
    """启动翻译请求"""
    file_id: int = Field(..., description="文件ID")
    source_lang: str = Field("auto", description="源语言（auto表示自动检测）")
    target_lang: str = Field(..., description="目标语言")
    model_name: str = Field("gpt-3.5-turbo", description="AI模型名称")
    thread_count: int = Field(5, ge=1, le=10, description="翻译线程数")
    prompt_id: Optional[int] = Field(None, description="提示词ID")
    display_mode: int = Field(1, description="译文显示模式：1=替换模式, 2=对照模式, 3=表格对照...")
    options: Optional[dict] = Field(None, description="额外配置选项")

    class Config:
        json_schema_extra = {
            "example": {
                "file_id": 1,
                "source_lang": "auto",
                "target_lang": "zh",
                "model_name": "gpt-3.5-turbo",
                "thread_count": 5,
                "display_mode": "replace"
            }
        }


class TranslateResponse(BaseModel):
    """翻译任务响应"""
    id: int
    uuid: str
    customer_id: Optional[int] = None
    prompt_id: Optional[int] = None
    file_name: str
    file_size: int
    file_type: str
    source_lang: str
    target_lang: str
    model_name: str
    thread_count: int
    display_mode: int = 1
    result_file_path: Optional[str] = None
    total_segments: int
    translated_segments: int
    status: str
    progress: int
    error_message: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    options: Optional[dict] = None

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "uuid": "550e8400-e29b-41d4-a716-446655440000",
                "file_name": "document.docx",
                "status": "processing",
                "progress": 45
            }
        }


class FileUploadResponse(BaseModel):
    """文件上传响应"""
    id: int
    file_name: str
    file_path: str
    file_size: int
    file_type: str

    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "file_name": "document.docx",
                "file_path": "/uploads/uuid.docx",
                "file_size": 1024000,
                "file_type": "docx"
            }
        }
