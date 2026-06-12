"""PlatformSchema Red-Green tests.

Tests for YAML parsing, DB sync, schema validation, and API endpoints.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.services import platform_schema_service as pss
from src.models.platform_schema_orm import PlatformSchemaORM, PlatformContentFormatORM


def test_list_yaml_platform_ids():
    """🔴 RED: 应能列出 YAML 目录中的平台标识."""
    ids = pss.list_yaml_platform_ids()
    assert "xiaohongshu" in ids
    assert "douyin" in ids
    assert "wechat_official" in ids
    assert "bilibili" in ids


def test_load_xiaohongshu_yaml():
    """🔴 RED: 应能正确解析小红书 YAML."""
    schema = pss.load_platform_schema_from_yaml("xiaohongshu")
    assert schema is not None
    assert schema["platform_id"] == "xiaohongshu"
    assert schema["display_name"] == "小红书"
    assert len(schema["content_formats"]) >= 2  # 图文 + 视频 + 仅文字

    # 检查图文格式的 title 字段
    tuwen = next(
        (f for f in schema["content_formats"] if f["format_name"] == "图文"), None
    )
    assert tuwen is not None
    title_field = next((f for f in tuwen["fields"] if f["name"] == "title"), None)
    assert title_field is not None
    assert title_field["max_chars"] == 20
    assert title_field["min_chars"] == 1


def test_load_douyin_yaml():
    """🔴 RED: 应能正确解析抖音 YAML."""
    schema = pss.load_platform_schema_from_yaml("douyin")
    assert schema is not None
    assert schema["platform_id"] == "douyin"
    assert schema["display_name"] == "抖音"


def test_load_wechat_official_yaml():
    """🔴 RED: 应能正确解析公众号 YAML."""
    schema = pss.load_platform_schema_from_yaml("wechat_official")
    assert schema is not None
    assert schema["platform_id"] == "wechat_official"


def test_load_bilibili_yaml():
    """🔴 RED: 应能正确解析 B 站 YAML."""
    schema = pss.load_platform_schema_from_yaml("bilibili")
    assert schema is not None
    assert schema["platform_id"] == "bilibili"


@pytest.mark.asyncio
async def test_sync_platform_schema(db: AsyncSession):
    """🔴 RED: 应能从 YAML 同步到数据库."""
    await pss.clear_platform_schemas(db)

    schema = await pss.sync_platform_schema_from_yaml(db, "xiaohongshu")
    assert schema is not None
    assert schema.platform_id == "xiaohongshu"
    assert schema.display_name == "小红书"
    assert len(schema.content_formats) >= 2


@pytest.mark.asyncio
async def test_list_platform_schemas(db: AsyncSession):
    """🔴 RED: 应能列出所有平台规范."""
    await pss.clear_platform_schemas(db)
    await pss.sync_platform_schema_from_yaml(db, "xiaohongshu")
    await pss.sync_platform_schema_from_yaml(db, "douyin")

    schemas = await pss.list_platform_schemas(db)
    assert len(schemas) == 2
    ids = [s.platform_id for s in schemas]
    assert "xiaohongshu" in ids
    assert "douyin" in ids


@pytest.mark.asyncio
async def test_get_content_format(db: AsyncSession):
    """🔴 RED: 应能获取指定内容格式."""
    await pss.clear_platform_schemas(db)
    await pss.sync_platform_schema_from_yaml(db, "xiaohongshu")

    fmt = await pss.get_content_format(db, "xiaohongshu", "图文")
    assert fmt is not None
    assert fmt.format_name == "图文"
    assert len(fmt.fields) > 0


def test_validate_content_pass():
    """🔴 RED: 合法内容应通过校验."""
    fields = [
        {"name": "title", "label": "标题", "type": "string", "required": True, "max_chars": 20},
        {"name": "body", "label": "正文", "type": "string", "required": True, "max_chars": 1000},
        {"name": "tags", "label": "标签", "type": "list", "required": False, "max_count": 10},
    ]
    content = {"title": "猫咪日常", "body": "今天带猫去公园", "tags": ["猫咪", "日常"]}

    passed, errors = pss.validate_content_against_schema(content, fields, strict=True)
    assert passed is True
    assert len(errors) == 0


def test_validate_content_title_too_long():
    """🔴 RED: 超长标题应被拦截."""
    fields = [
        {"name": "title", "label": "标题", "type": "string", "required": True, "max_chars": 20},
    ]
    content = {"title": "这是一段非常长的标题超过了二十个字符的限制"}

    passed, errors = pss.validate_content_against_schema(content, fields, strict=True)
    assert passed is False
    assert len(errors) == 1
    assert errors[0].field == "title"
    assert "最多 20 个字符" in errors[0].message


def test_validate_content_missing_required():
    """🔴 RED: 缺失必填项应被拦截."""
    fields = [
        {"name": "title", "label": "标题", "type": "string", "required": True},
    ]
    content = {}

    passed, errors = pss.validate_content_against_schema(content, fields, strict=True)
    assert passed is False
    assert len(errors) == 1
    assert errors[0].field == "title"


def test_validate_content_tags_overflow():
    """🔴 RED: 标签数量超限应被拦截."""
    fields = [
        {"name": "tags", "label": "标签", "type": "list", "required": False, "max_count": 5},
    ]
    content = {"tags": ["a", "b", "c", "d", "e", "f", "g"]}

    passed, errors = pss.validate_content_against_schema(content, fields, strict=True)
    assert passed is False
    assert len(errors) == 1
    assert "最多 5 项" in errors[0].message


def test_validate_content_warn_only():
    """🔴 RED: 非严格模式应仅警告不阻断."""
    fields = [
        {"name": "title", "label": "标题", "type": "string", "required": True, "max_chars": 20},
    ]
    content = {"title": "这是一段非常长的标题超过了二十个字符的限制"}

    passed, errors = pss.validate_content_against_schema(content, fields, strict=False)
    assert passed is True  # 非严格模式不阻断
    assert len(errors) == 1
    assert errors[0].severity == "warn"


def test_validate_content_pic_num_min():
    """🔴 RED: 图片数量不足应被拦截."""
    fields = [
        {"name": "images", "label": "图片", "type": "list", "required": True, "min": 1},
    ]
    content = {"images": []}

    passed, errors = pss.validate_content_against_schema(content, fields, strict=True)
    assert passed is False
    assert "至少需要 1 项" in errors[0].message


def test_validate_content_image_format():
    """🔴 RED: 不支持的图片格式应被拦截."""
    fields = [
        {"name": "cover", "label": "封面", "type": "string", "required": True, "supported": ["png", "jpg", "jpeg", "webp"]},
    ]
    content = {"cover": "image.gif"}

    passed, errors = pss.validate_content_against_schema(content, fields, strict=True)
    assert passed is False
    assert "不支持格式 'gif'" in errors[0].message


# ─── API Integration Tests ───

def get_auth_token(client, role: str = "operator"):
    import uuid
    from src.models.user import clear_users
    from src.services.platform_schema_service import clear_platform_schemas
    from src.services.auth_service import register_user
    from tests.conftest import sync_clear_platform_rules

    clear_users()
    sync_clear_platform_rules()

    email = f"ps_{uuid.uuid4().hex[:8]}@ecodream.com"
    response = client.post("/auth/register", json={
        "email": email,
        "password": "SecurePass123!",
        "username": f"psuser_{uuid.uuid4().hex[:8]}",
        "role": role,
    })
    assert response.status_code == 201, f"Register failed: {response.text}"
    return response.json()["access_token"]


def test_api_sync_from_yaml(client):
    """🔴 RED: API 应能从 YAML 同步."""
    token = get_auth_token(client)
    response = client.post(
        "/platform-schemas/sync-from-yaml",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 4  # 至少 4 个平台
    ids = [r["platform_id"] for r in data]
    assert "xiaohongshu" in ids
    assert "douyin" in ids


def test_api_list_platform_schemas(client):
    """🔴 RED: API 应能列出所有平台规范."""
    token = get_auth_token(client)
    # 先同步
    client.post(
        "/platform-schemas/sync-from-yaml",
        headers={"Authorization": f"Bearer {token}"},
    )

    response = client.get(
        "/platform-schemas",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "schemas" in data
    assert len(data["schemas"]) >= 4


def test_api_get_platform_schema(client):
    """🔴 RED: API 应能获取指定平台规范."""
    token = get_auth_token(client)
    client.post(
        "/platform-schemas/sync-from-yaml",
        headers={"Authorization": f"Bearer {token}"},
    )

    response = client.get(
        "/platform-schemas/xiaohongshu",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["platform_id"] == "xiaohongshu"
    assert data["display_name"] == "小红书"
    assert len(data["content_formats"]) >= 2


def test_api_validate_content(client):
    """🔴 RED: API 应能校验内容格式."""
    token = get_auth_token(client)
    client.post(
        "/platform-schemas/sync-from-yaml",
        headers={"Authorization": f"Bearer {token}"},
    )

    # 合法内容（使用 YAML 中定义的字段名：title, content, tags）
    response = client.post(
        "/platform-schemas/validate",
        json={
            "platform_id": "xiaohongshu",
            "format_name": "图文",
            "content": {"title": "猫咪日常", "content": "今天带猫去公园", "tags": ["猫咪"]},
            "strict": True,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["passed"] is True, f"Expected passed=True, got errors: {data.get('errors')}"

    # 超长标题
    response = client.post(
        "/platform-schemas/validate",
        json={
            "platform_id": "xiaohongshu",
            "format_name": "图文",
            "content": {"title": "这是一段非常长的标题超过了二十个字符的限制很多很多字", "content": "正文"},
            "strict": True,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["passed"] is False
    assert len(data["errors"]) >= 1
