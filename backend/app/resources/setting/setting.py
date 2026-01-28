"""
系统配置管理路由
处理系统配置的查询和更新操作
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from ...database import get_db
from ...models.setting import Setting
from ...models.customer import Customer
from ...core.deps import get_current_customer
from ...schemas.common import ResponseModel


router = APIRouter(prefix="/setting", tags=["系统配置"])


@router.get("/list", response_model=None)
async def get_settings(
    category: Optional[str] = Query(None, description="配置分类"),
    public_only: bool = Query(True, description="只返回公开配置"),
    current_user: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """
    获取系统配置列表

    - **category**: 配置分类筛选（可选）
    - **public_only**: 是否只返回公开配置（默认True）
    """
    # 构建查询
    query = db.query(Setting)

    # 公开配置筛选
    if public_only:
        query = query.filter(Setting.is_public == True)

    # 分类筛选
    if category:
        query = query.filter(Setting.category == category)

    settings = query.order_by(Setting.id).all()
    settings_data = [s.to_dict() for s in settings]

    # 按分类组织
    result = {}
    for s in settings_data:
        cat = s['category']
        if cat not in result:
            result[cat] = []
        result[cat].append(s)

    return ResponseModel(
        success=True,
        message="获取成功",
        data=result if category else settings_data
    )


@router.get("/{key}", response_model=None)
async def get_setting(
    key: str,
    current_user: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """
    获取单个配置项

    - **key**: 配置键
    """
    setting = db.query(Setting).filter(Setting.key == key).first()

    if not setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="配置项不存在"
        )

    # 检查是否公开
    if not setting.is_public:
        # TODO: 添加管理员权限检查
        pass

    return ResponseModel(
        success=True,
        message="获取成功",
        data=setting.to_dict()
    )


@router.post("/update", response_model=None)
async def update_settings(
    updates: dict,
    current_user: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """
    批量更新系统配置（管理员功能）

    请求体格式:
    {
        "max_file_size": 104857600,
        "default_model": "gpt-4"
    }
    """
    # TODO: 添加管理员权限检查

    updated = []

    try:
        for key, value in updates.items():
            setting = db.query(Setting).filter(Setting.key == key).first()

            if not setting:
                # 创建新配置
                setting = Setting(
                    key=key,
                    value=str(value),
                    value_type=type(value).__name__
                )
                db.add(setting)
            else:
                # 更新现有配置
                if not setting.is_editable:
                    continue  # 跳过不可编辑的配置

                setting.set_value(value)

            updated.append(setting.to_dict())

        db.commit()

        return ResponseModel(
            success=True,
            message="更新成功",
            data=updated
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新失败: {str(e)}"
        )


@router.get("/translate/info", response_model=None)
async def get_translate_info(
    current_user: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """
    获取翻译服务相关信息

    返回支持的模型、语言、文件格式等
    """
    # 从配置中获取信息
    models_config = db.query(Setting).filter(Setting.key == "supported_models").first()
    formats_config = db.query(Setting).filter(Setting.key == "supported_formats").first()
    languages_config = db.query(Setting).filter(Setting.key == "supported_languages").first()

    info = {
        "models": models_config.get_value() if models_config else ["gpt-3.5-turbo", "gpt-4"],
        "formats": formats_config.get_value() if formats_config else ["docx", "pdf", "xlsx", "pptx", "md", "txt"],
        "languages": languages_config.get_value() if languages_config else {
            "zh": "中文",
            "en": "英文",
            "ja": "日文",
            "ko": "韩文",
            "fr": "法文",
            "de": "德文",
            "es": "西班牙文",
            "ru": "俄文"
        }
    }

    return ResponseModel(
        success=True,
        message="获取成功",
        data=info
    )
