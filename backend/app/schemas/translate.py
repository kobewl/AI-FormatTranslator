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
    domain: str = Field("general", description="翻译领域（general/medical/it/legal/finance等）")
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
    domain: str = "general"
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


class PreviewContentItem(BaseModel):
    """预览内容项"""
    type: str = Field(..., description="内容类型：paragraph/table/cell/text/heading/list/code")
    text: str = Field(..., description="文本内容")
    index: int | str = Field(..., description="索引或位置标识")
    location: Optional[str] = Field(None, description="位置描述（如表格位置）")
    prefix: Optional[str] = Field(None, description="前缀标记（如 Markdown 标题标记）")


class PreviewResponse(BaseModel):
    """文件预览响应"""
    content: list[PreviewContentItem] = Field(..., description="内容列表")
    total_chars: int = Field(..., description="总字符数")
    truncated: bool = Field(..., description="是否被截断")
    format: str = Field(..., description="文件格式")
    total_paragraphs: Optional[int] = Field(None, description="总段落数（Word/TXT）")
    total_tables: Optional[int] = Field(None, description="总表格数（Word）")
    total_sheets: Optional[int] = Field(None, description="总工作表数（Excel）")
    total_cells: Optional[int] = Field(None, description="总单元格数（Excel）")
    total_slides: Optional[int] = Field(None, description="总幻灯片数（PPT）")
    total_texts: Optional[int] = Field(None, description="总文本数（PPT）")
    error: Optional[str] = Field(None, description="错误信息（如果有）")

    class Config:
        json_schema_extra = {
            "example": {
                "content": [
                    {"type": "paragraph", "text": "这是一段示例文本", "index": 0}
                ],
                "total_chars": 1000,
                "truncated": False,
                "format": "docx"
            }
        }


class ParallelPreviewResponse(BaseModel):
    """对照预览响应（原文+译文）"""
    source_content: list[PreviewContentItem] = Field(..., description="原文内容列表")
    translated_content: list[PreviewContentItem] = Field(..., description="译文内容列表")
    source_chars: int = Field(..., description="原文总字符数")
    translated_chars: int = Field(..., description="译文总字符数")
    truncated: bool = Field(..., description="是否被截断")
    format: str = Field(..., description="文件格式")
    error: Optional[str] = Field(None, description="错误信息（如果有）")
