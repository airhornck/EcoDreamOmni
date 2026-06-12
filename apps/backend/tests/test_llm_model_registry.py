"""LLM Hub Model Registry tests — PRD V2.7.2 §8."""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from src.services import llm_hub as lhs

pytestmark = pytest.mark.asyncio(loop_scope="function")


@pytest_asyncio.fixture
async def db_session(db, skip_if_no_db):
    await lhs.clear_llm_hub_data(db)
    yield db


# ─── 1. CRUD ───
async def test_register_and_list_models(db_session: AsyncSession):
    m = await lhs.register_model(
        db=db_session, provider="deepseek", model_name="deepseek-chat", api_key="sk-test1"
    )
    assert m["provider"] == "deepseek"
    assert m["model_name"] == "deepseek-chat"

    models = await lhs.list_models(db=db_session)
    assert len(models) == 1
    assert models[0]["api_key_encrypted"] == "••••••••"


async def test_get_and_update_model(db_session: AsyncSession):
    m = await lhs.register_model(
        db=db_session, provider="openai", model_name="gpt-4o", api_key="sk-test2"
    )
    mid = m["id"]

    fetched = await lhs.get_model(db=db_session, model_id=mid)
    assert fetched is not None
    assert fetched["model_name"] == "gpt-4o"

    updated = await lhs.update_model(
        db=db_session, model_id=mid, status="inactive", api_key="sk-new"
    )
    assert updated is not None
    assert updated["status"] == "inactive"
    # api_key should be encrypted
    assert updated["api_key_encrypted"] != "sk-new"


async def test_delete_model(db_session: AsyncSession):
    m = await lhs.register_model(
        db=db_session, provider="aliyun", model_name="qwen-max", api_key="sk-test3"
    )
    mid = m["id"]

    ok = await lhs.delete_model(db=db_session, model_id=mid)
    assert ok is True

    models = await lhs.list_models(db=db_session)
    assert len(models) == 0


# ─── 2. API key encryption ───
async def test_api_key_encryption_roundtrip(db_session: AsyncSession):
    plain = "my-super-secret-key-12345"
    encrypted = lhs.encrypt_api_key(plain)
    assert encrypted != plain
    decrypted = lhs.decrypt_api_key(encrypted)
    assert decrypted == plain


# ─── 3. Connectivity test mock ───
async def test_connectivity_mock(db_session: AsyncSession, monkeypatch):
    m = await lhs.register_model(
        db=db_session,
        provider="deepseek",
        model_name="deepseek-chat",
        api_key="sk-test",
        endpoint_url="https://api.deepseek.com/chat/completions",
    )
    mid = m["id"]

    class FakeResponse:
        status_code = 200
        text = '{"choices":[]}'

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def post(self, *args, **kwargs):
            return FakeResponse()

    monkeypatch.setattr("httpx.AsyncClient", FakeClient)
    result = await lhs.test_connectivity(db=db_session, model_id=mid)
    assert result["reachable"] is True
