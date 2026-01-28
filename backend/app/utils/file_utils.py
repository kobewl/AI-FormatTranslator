"""
文件处理工具函数（FastAPI 版）
处理文件上传、验证、删除等操作
"""
import os
import uuid
import re
from pathlib import Path
from typing import Tuple, Optional
from fastapi import UploadFile


def secure_filename(filename: str) -> str:
    """
    安全处理文件名（移除危险字符）

    Args:
        filename: 原始文件名

    Returns:
        str: 安全的文件名
    """
    # 移除路径部分
    filename = os.path.basename(filename)

    # 移除危险字符
    filename = re.sub(r'[^\w\s.-]', '', filename)

    # 移除开点和结尾的点/空格
    filename = filename.strip('. ')

    # 如果文件名为空，使用默认名称
    if not filename:
        filename = "unnamed"

    return filename


def allowed_file(filename: str, allowed_extensions: set) -> bool:
    """
    检查文件扩展名是否允许

    Args:
        filename: 文件名
        allowed_extensions: 允许的扩展名集合

    Returns:
        bool: 是否允许
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions


def generate_unique_filename(original_filename: str) -> str:
    """
    生成唯一的文件名

    Args:
        original_filename: 原始文件名

    Returns:
        str: 唯一文件名（UUID + 原扩展名）
    """
    ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''
    unique_id = str(uuid.uuid4())
    return f"{unique_id}.{ext}" if ext else unique_id


async def save_uploaded_file(file: UploadFile, upload_folder: str) -> Tuple[bool, str, Optional[str]]:
    """
    保存上传的文件（异步）

    Args:
        file: FastAPI UploadFile 对象
        upload_folder: 上传目录

    Returns:
        tuple: (是否成功, 文件路径, 错误消息)
    """
    try:
        # 安全处理文件名
        filename = secure_filename(file.filename)
        if not filename:
            return False, "", "文件名无效"

        # 生成唯一文件名
        unique_filename = generate_unique_filename(filename)

        # 确保目录存在
        os.makedirs(upload_folder, exist_ok=True)

        # 保存文件
        file_path = os.path.join(upload_folder, unique_filename)

        # 异步读取并写入文件
        with open(file_path, 'wb') as f:
            content = await file.read()
            f.write(content)

        return True, file_path, None

    except Exception as e:
        return False, "", f"文件保存失败: {str(e)}"


def delete_file(file_path: str) -> bool:
    """
    删除文件

    Args:
        file_path: 文件路径

    Returns:
        bool: 是否删除成功
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False
    except Exception:
        return False


def get_file_size(file_path: str) -> int:
    """
    获取文件大小

    Args:
        file_path: 文件路径

    Returns:
        int: 文件大小（字节）
    """
    try:
        return os.path.getsize(file_path)
    except Exception:
        return 0


def format_file_size(size_bytes: int) -> str:
    """
    格式化文件大小显示

    Args:
        size_bytes: 文件大小（字节）

    Returns:
        str: 格式化后的文件大小字符串
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"


def get_file_extension(filename: str) -> str:
    """
    获取文件扩展名

    Args:
        filename: 文件名

    Returns:
        str: 文件扩展名（小写，不含点）
    """
    return filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
