"""
安全相关功能
处理 JWT token 生成和验证、密码加密等
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
import bcrypt
import hashlib
import base64

from ..config import settings


def _preprocess_password(password: str) -> bytes:
    """
    预处理密码以解决 bcrypt 72 字节限制

    bcrypt 算法限制密码最长 72 字节。
    - 如果密码 <= 72 字节，直接返回原密码的 bytes
    - 如果密码 > 72 字节，使用 SHA-256 哈希

    Args:
        password: 原始明文密码

    Returns:
        bytes: 处理后的密码
    """
    password_bytes = password.encode('utf-8')

    # bcrypt 限制为 72 字节
    if len(password_bytes) <= 72:
        return password_bytes

    # 对于长密码，使用 SHA-256 哈希
    return hashlib.sha256(password_bytes).digest()


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    创建 JWT 访问令牌

    Args:
        data: 要编码到 token 中的数据
        expires_delta: 过期时间增量

    Returns:
        str: JWT token
    """
    to_encode = data.copy()

    # 设置过期时间
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})

    # 编码 JWT
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    解码 JWT 访问令牌

    Args:
        token: JWT token

    Returns:
        解码后的数据，如果验证失败则返回 None
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        return None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码

    支持两种密码格式以保持向后兼容：
    1. 直接 bcrypt 加密（短密码）
    2. SHA-256 预处理 + bcrypt 加密（长密码，超过 72 字节）

    Args:
        plain_password: 明文密码
        hashed_password: 哈希密码

    Returns:
        bool: 密码是否匹配
    """
    try:
        # 先尝试直接验证（短密码或旧方式）
        if bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8')):
            return True

        # 如果失败，尝试 SHA-256 预处理后的验证（长密码的新方式）
        preprocessed = _preprocess_password(plain_password)
        return bcrypt.checkpw(preprocessed, hashed_password.encode('utf-8'))
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """
    获取密码哈希

    对于长密码（> 72 字节），先使用 SHA-256 哈希进行预处理，
    然后再使用 bcrypt 加密。

    Args:
        password: 明文密码

    Returns:
        str: 哈希后的密码
    """
    # 预处理密码（处理长密码情况）
    preprocessed = _preprocess_password(password)

    # 使用 bcrypt 加密，自动添加盐值
    hashed = bcrypt.hashpw(preprocessed, bcrypt.gensalt())

    return hashed.decode('utf-8')
