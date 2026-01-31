"""
Translate 数据模型（翻译任务）
使用 SQLAlchemy 2.0 语法
"""
from datetime import datetime
import uuid
from sqlalchemy import Column, Integer, String, DateTime, BigInteger, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship

from ..database import Base


class Translate(Base):
    """
    翻译任务模型
    记录文档翻译的完整生命周期
    """

    __tablename__ = "translates"

    id = Column(Integer, primary_key=True, index=True, comment="任务ID")
    uuid = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()), comment="唯一标识符")

    # 外键关联
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True, comment="用户ID")
    prompt_id = Column(Integer, ForeignKey("prompts.id"), nullable=True, comment="提示词ID")

    # 文件信息
    file_name = Column(String(255), nullable=False, comment="原始文件名")
    file_path = Column(String(500), nullable=False, comment="原始文件路径")
    file_size = Column(BigInteger, nullable=False, default=0, comment="文件大小（字节）")
    file_type = Column(String(20), nullable=False, comment="文件类型（docx/pdf/xlsx/pptx/md/txt）")

    # 翻译配置
    source_lang = Column(String(20), default="auto", comment="源语言（auto表示自动检测）")
    target_lang = Column(String(20), nullable=True, comment="目标语言（上传时为空，开始翻译时设置）")
    model_name = Column(String(50), default="gpt-3.5-turbo", comment="使用的AI模型")
    thread_count = Column(Integer, default=5, comment="翻译线程数")
    display_mode = Column(Integer, default=1, comment="译文显示模式：1=替换模式,2=对照模式,3=表格对照,4=双语对照...")
    domain = Column(String(50), default="general", comment="翻译领域（general/medical/it/legal等）")

    # 翻译结果
    result_file_path = Column(String(500), nullable=True, comment="翻译结果文件路径")
    total_segments = Column(Integer, default=0, comment="总文本段数")
    translated_segments = Column(Integer, default=0, comment="已翻译段数")

    # 任务状态
    status = Column(String(20), default="pending", comment="状态（pending/processing/completed/failed）")
    progress = Column(Integer, default=0, comment="进度百分比（0-100）")
    error_message = Column(Text, nullable=True, comment="错误信息")

    # 时间记录
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    started_at = Column(DateTime, nullable=True, comment="开始时间")
    completed_at = Column(DateTime, nullable=True, comment="完成时间")

    # 额外配置（JSON格式存储）
    options = Column(JSON, nullable=True, comment="额外配置选项")

    # 关系
    customer = relationship("Customer", back_populates="translates")
    prompt = relationship("Prompt", back_populates="translates")

    def update_progress(self, translated_count: int):
        """
        更新翻译进度

        Args:
            translated_count: 已翻译的段数
        """
        self.translated_segments = translated_count
        if self.total_segments > 0:
            self.progress = int((translated_count / self.total_segments) * 100)
        else:
            self.progress = 0

    def mark_as_started(self):
        """标记任务为开始处理"""
        self.status = "processing"
        self.started_at = datetime.now()
        self.progress = 0

    def mark_as_completed(self, result_path: str):
        """
        标记任务为完成

        Args:
            result_path: 结果文件路径
        """
        self.status = "completed"
        self.progress = 100
        self.completed_at = datetime.now()
        self.result_file_path = result_path

    def mark_as_failed(self, error_msg: str):
        """
        标记任务为失败

        Args:
            error_msg: 错误信息
        """
        self.status = "failed"
        self.error_message = error_msg
        self.completed_at = datetime.now()

    def to_dict(self) -> dict:
        """
        转换为字典（用于 JSON 序列化）

        Returns:
            dict: 任务信息字典
        """
        return {
            "id": self.id,
            "uuid": self.uuid,
            "customer_id": self.customer_id,
            "prompt_id": self.prompt_id,
            "file_name": self.file_name,
            "file_size": self.file_size,
            "file_type": self.file_type,
            "source_lang": self.source_lang,
            "target_lang": self.target_lang,
            "model_name": self.model_name,
            "thread_count": self.thread_count,
            "display_mode": self.display_mode,
            "domain": self.domain,
            "result_file_path": self.result_file_path,
            "total_segments": self.total_segments,
            "translated_segments": self.translated_segments,
            "status": self.status,
            "progress": self.progress,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "options": self.options
        }

    def __repr__(self):
        return f"<Translate {self.file_name} - {self.status}>"
