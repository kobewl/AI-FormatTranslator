"""
统一响应格式工具（FastAPI 版）
定义标准化的 API 响应格式
"""
from typing import Any, Optional, Dict, List


def success_response(data: Any = None, message: str = "操作成功", code: int = 200) -> Dict[str, Any]:
    """
    成功响应格式

    Args:
        data: 响应数据
        message: 响应消息
        code: HTTP 状态码（仅用于标识，FastAPI 自动设置状态码）

    Returns:
        Dict: 响应字典
    """
    return {
        "success": True,
        "message": message,
        "data": data
    }


def error_response(message: str, code: int = 400, errors: Any = None) -> Dict[str, Any]:
    """
    错误响应格式

    Args:
        message: 错误消息
        code: HTTP 状态码（仅用于标识）
        errors: 详细错误信息

    Returns:
        Dict: 响应字典
    """
    response = {
        "success": False,
        "message": message
    }
    if errors is not None:
        response["errors"] = errors
    return response


def paginated_response(
    items: List[Any],
    total: int,
    page: int,
    per_page: int,
    message: str = "获取成功"
) -> Dict[str, Any]:
    """
    分页响应格式

    Args:
        items: 数据列表
        total: 总记录数
        page: 当前页码
        per_page: 每页记录数
        message: 响应消息

    Returns:
        Dict: 响应字典
    """
    return {
        "success": True,
        "message": message,
        "data": {
            "items": items,
            "pagination": {
                "total": total,
                "page": page,
                "per_page": per_page,
                "pages": (total + per_page - 1) // per_page  # 向上取整
            }
        }
    }
