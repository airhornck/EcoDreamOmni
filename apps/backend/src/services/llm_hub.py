"""LLM Hub Service — PRD V2.7.2 §8 精简版.

厂家选择 + 模型名 + APIKey + 应用范围（全局/节点覆盖）
"""

import base64
import os
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

import httpx
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from src.models.llm_hub_orm import LLMModelORM, LLMScopeConfigORM, LLMUsageLogORM, LLMPricingORM

# ── AES-256-GCM encryption for API keys ──
from src.core.config import settings

# Derive master key from settings (falls back to JWT_SECRET for test environments)
MASTER_KEY = settings.LLM_API_KEY_MASTER_KEY or settings.JWT_SECRET or "ecodream-test-master-key-32bytes!"
_key_bytes = MASTER_KEY.encode("utf-8")
if len(_key_bytes) < 32:
    _key_bytes = _key_bytes.ljust(32, b"\0")
else:
    _key_bytes = _key_bytes[:32]


def encrypt_api_key(plain_text: str) -> str:
    aesgcm = AESGCM(_key_bytes)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, plain_text.encode("utf-8"), None)
    return base64.b64encode(nonce + ciphertext).decode("utf-8")


def decrypt_api_key(encrypted: str) -> str:
    data = base64.b64decode(encrypted.encode("utf-8"))
    nonce, ciphertext = data[:12], data[12:]
    aesgcm = AESGCM(_key_bytes)
    plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    return plaintext.decode("utf-8")


# ── Provider region classification ──
domestic_providers = {"deepseek", "aliyun", "baidu", "zhipu", "kimi", "xunfei"}
overseas_providers = {"openai", "anthropic", "google"}


def get_provider_region(provider: str) -> str:
    return "domestic" if provider in domestic_providers else "overseas"


# ── Pricing seed data ──
pricing_data = [
    {"model_name": "deepseek-chat", "provider": "deepseek", "input_price_per_1k": 0.001, "output_price_per_1k": 0.002, "currency": "CNY"},
    {"model_name": "deepseek-v4-pro", "provider": "deepseek", "input_price_per_1k": 0.001, "output_price_per_1k": 0.002, "currency": "CNY"},
    {"model_name": "deepseek-reasoner", "provider": "deepseek", "input_price_per_1k": 0.004, "output_price_per_1k": 0.016, "currency": "CNY"},
    {"model_name": "gpt-4o", "provider": "openai", "input_price_per_1k": 0.035, "output_price_per_1k": 0.105, "currency": "USD"},
    {"model_name": "gpt-4o-mini", "provider": "openai", "input_price_per_1k": 0.00015, "output_price_per_1k": 0.0006, "currency": "USD"},
    {"model_name": "claude-3-5-sonnet", "provider": "anthropic", "input_price_per_1k": 0.003, "output_price_per_1k": 0.015, "currency": "USD"},
    {"model_name": "qwen-max", "provider": "aliyun", "input_price_per_1k": 0.02, "output_price_per_1k": 0.06, "currency": "CNY"},
    {"model_name": "glm-4", "provider": "zhipu", "input_price_per_1k": 0.005, "output_price_per_1k": 0.005, "currency": "CNY"},
    {"model_name": "kimi-v1", "provider": "kimi", "input_price_per_1k": 0.006, "output_price_per_1k": 0.012, "currency": "CNY"},
]


async def init_pricing_data(db: Any) -> None:
    for item in pricing_data:
        stmt = pg_insert(LLMPricingORM).values(**item).on_conflict_do_nothing(
            index_elements=["model_name"]
        )
        await db.execute(stmt)
    await db.flush()
    await db.commit()


# ── Helpers ──
def _model_to_dict(orm: LLMModelORM, *, mask_key: bool = False) -> Dict[str, Any]:
    return {
        "id": str(orm.id),
        "provider": orm.provider,
        "model_name": orm.model_name,
        "api_key_encrypted": "••••••••" if mask_key else orm.api_key_encrypted,
        "endpoint_base_url": orm.endpoint_base_url,
        "status": orm.status,
        "data_training_opt_out": orm.data_training_opt_out,
        "modality_support": orm.modality_support or {},
        "created_at": orm.created_at.isoformat() if orm.created_at else None,
        "updated_at": orm.updated_at.isoformat() if orm.updated_at else None,
    }


def _scope_to_dict(orm: LLMScopeConfigORM) -> Dict[str, Any]:
    return {
        "id": str(orm.id),
        "scope_type": orm.scope_type,
        "node_id": orm.node_id,
        "model_id": str(orm.model_id),
        "temperature": orm.temperature,
        "timeout_seconds": orm.timeout_seconds,
        "created_at": orm.created_at.isoformat() if orm.created_at else None,
        "updated_at": orm.updated_at.isoformat() if orm.updated_at else None,
    }


def _usage_to_dict(orm: LLMUsageLogORM) -> Dict[str, Any]:
    return {
        "id": str(orm.id),
        "model_id": str(orm.model_id) if orm.model_id else None,
        "node_id": orm.node_id,
        "provider_region": orm.provider_region,
        "input_tokens": orm.input_tokens,
        "output_tokens": orm.output_tokens,
        "latency_ms": orm.latency_ms,
        "status": orm.status,
        "error_message": orm.error_message,
        "created_at": orm.created_at.isoformat() if orm.created_at else None,
    }


def _default_endpoint(provider: str) -> str:
    defaults = {
        "deepseek": "https://api.deepseek.com/chat/completions",
        "aliyun": "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation",
        "baidu": "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/completions",
        "zhipu": "https://open.bigmodel.cn/api/paas/v4/chat/completions",
        "kimi": "https://api.moonshot.cn/v1/chat/completions",
        "xunfei": "https://spark-api-open.xf-yun.com/v1/chat/completions",
        "openai": "https://api.openai.com/v1/chat/completions",
        "anthropic": "https://api.anthropic.com/v1/messages",
        "google": "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent",
    }
    return defaults.get(provider, "")


# ── Model Registry ──
async def register_model(
    db: Any,
    provider: str,
    model_name: str,
    api_key: str,
    endpoint_url: Optional[str] = None,
    status: str = "active",
    modality_support: Optional[Dict[str, bool]] = None,
) -> Dict[str, Any]:
    encrypted = encrypt_api_key(api_key)
    orm = LLMModelORM(
        provider=provider,
        model_name=model_name,
        api_key_encrypted=encrypted,
        endpoint_base_url=endpoint_url,
        status=status,
        modality_support=modality_support or {},
    )
    db.add(orm)
    await db.flush()
    await db.commit()
    await db.refresh(orm)
    return _model_to_dict(orm, mask_key=False)


async def list_models(
    db: Any,
    provider: Optional[str] = None,
    status: Optional[str] = None,
) -> List[Dict[str, Any]]:
    query = select(LLMModelORM).order_by(LLMModelORM.created_at.desc())
    if provider:
        query = query.where(LLMModelORM.provider == provider)
    if status:
        query = query.where(LLMModelORM.status == status)
    result = await db.execute(query)
    return [_model_to_dict(m, mask_key=True) for m in result.scalars().all()]


async def get_model(db: Any, model_id: str) -> Optional[Dict[str, Any]]:
    result = await db.execute(select(LLMModelORM).where(LLMModelORM.id == model_id))
    orm = result.scalar_one_or_none()
    return _model_to_dict(orm, mask_key=False) if orm else None


async def update_model(
    db: Any, model_id: str, **fields: Any
) -> Optional[Dict[str, Any]]:
    result = await db.execute(select(LLMModelORM).where(LLMModelORM.id == model_id))
    orm = result.scalar_one_or_none()
    if not orm:
        return None
    allowed = {
        "provider",
        "model_name",
        "endpoint_base_url",
        "status",
        "data_training_opt_out",
        "modality_support",
    }
    for key, value in fields.items():
        if key == "api_key" and value is not None:
            value = encrypt_api_key(value)
            key = "api_key_encrypted"
        if key in allowed or key == "api_key_encrypted":
            setattr(orm, key, value)
    orm.updated_at = datetime.now(timezone.utc)
    await db.flush()
    await db.commit()
    await db.refresh(orm)
    return _model_to_dict(orm, mask_key=False)


async def delete_model(db: Any, model_id: str) -> bool:
    result = await db.execute(select(LLMModelORM).where(LLMModelORM.id == model_id))
    orm = result.scalar_one_or_none()
    if not orm:
        return False
    await db.delete(orm)
    await db.flush()
    await db.commit()
    return True


async def test_connectivity(db: Any, model_id: str) -> Dict[str, Any]:
    result = await db.execute(select(LLMModelORM).where(LLMModelORM.id == model_id))
    orm = result.scalar_one_or_none()
    if not orm:
        return {"reachable": False, "error": "Model not found"}
    try:
        api_key = decrypt_api_key(orm.api_key_encrypted)
    except Exception as e:
        return {"reachable": False, "error": f"Decryption failed: {e}"}

    url = orm.endpoint_base_url or _default_endpoint(orm.provider)
    if not url:
        return {"reachable": False, "error": "No endpoint configured"}

    payload = {
        "model": orm.model_name,
        "messages": [{"role": "user", "content": "hi"}],
        "max_tokens": 1,
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(url, headers=headers, json=payload)
        if resp.status_code < 500:
            return {
                "reachable": True,
                "status_code": resp.status_code,
                "detail": resp.text[:200],
            }
        return {
            "reachable": False,
            "status_code": resp.status_code,
            "detail": resp.text[:200],
        }
    except Exception as e:
        return {"reachable": False, "error": str(e)}


# ── Scope Config ──
async def set_global_default(
    db: Any, model_id: str, temperature: float = 0.5, timeout: int = 60
) -> Dict[str, Any]:
    result = await db.execute(
        select(LLMScopeConfigORM).where(LLMScopeConfigORM.scope_type == "global")
    )
    existing = result.scalar_one_or_none()
    if existing:
        existing.model_id = model_id
        existing.temperature = temperature
        existing.timeout_seconds = timeout
        existing.updated_at = datetime.now(timezone.utc)
        await db.flush()
        await db.commit()
        await db.refresh(existing)
        return _scope_to_dict(existing)
    orm = LLMScopeConfigORM(
        scope_type="global",
        node_id=None,
        model_id=model_id,
        temperature=temperature,
        timeout_seconds=timeout,
    )
    db.add(orm)
    await db.flush()
    await db.commit()
    await db.refresh(orm)
    return _scope_to_dict(orm)


async def set_node_override(
    db: Any,
    node_id: str,
    model_id: str,
    temperature: Optional[float] = None,
    timeout: Optional[int] = None,
) -> Dict[str, Any]:
    result = await db.execute(
        select(LLMScopeConfigORM).where(
            LLMScopeConfigORM.scope_type == "node",
            LLMScopeConfigORM.node_id == node_id,
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        existing.model_id = model_id
        if temperature is not None:
            existing.temperature = temperature
        if timeout is not None:
            existing.timeout_seconds = timeout
        existing.updated_at = datetime.now(timezone.utc)
        await db.flush()
        await db.commit()
        await db.refresh(existing)
        return _scope_to_dict(existing)
    orm = LLMScopeConfigORM(
        scope_type="node",
        node_id=node_id,
        model_id=model_id,
        temperature=temperature if temperature is not None else 0.5,
        timeout_seconds=timeout if timeout is not None else 60,
    )
    db.add(orm)
    await db.flush()
    await db.commit()
    await db.refresh(orm)
    return _scope_to_dict(orm)


async def remove_node_override(db: Any, node_id: str) -> bool:
    result = await db.execute(
        delete(LLMScopeConfigORM)
        .where(
            LLMScopeConfigORM.scope_type == "node",
            LLMScopeConfigORM.node_id == node_id,
        )
        .returning(LLMScopeConfigORM.id)
    )
    deleted = result.scalar_one_or_none()
    await db.flush()
    await db.commit()
    return deleted is not None


async def list_scope_configs(db: Any) -> List[Dict[str, Any]]:
    """Return all scope configs with inheritance info."""
    global_result = await db.execute(
        select(LLMScopeConfigORM).where(LLMScopeConfigORM.scope_type == "global")
    )
    global_cfg = global_result.scalar_one_or_none()

    node_result = await db.execute(
        select(LLMScopeConfigORM).where(LLMScopeConfigORM.scope_type == "node")
    )
    nodes = node_result.scalars().all()

    model_ids = {str(n.model_id) for n in nodes}
    if global_cfg:
        model_ids.add(str(global_cfg.model_id))
    models_map: Dict[str, str] = {}
    if model_ids:
        m_result = await db.execute(
            select(LLMModelORM).where(LLMModelORM.id.in_(model_ids))
        )
        models_map = {str(m.id): m.model_name for m in m_result.scalars().all()}

    items: List[Dict[str, Any]] = []
    if global_cfg:
        items.append(
            {
                "node_id": "__global__",
                "node_type": "global",
                "current_model": models_map.get(str(global_cfg.model_id), "unknown"),
                "source": "global_default",
                "model_id": str(global_cfg.model_id),
                "temperature": global_cfg.temperature,
                "timeout_seconds": global_cfg.timeout_seconds,
            }
        )
    for node in nodes:
        items.append(
            {
                "node_id": node.node_id,
                "node_type": "node",
                "current_model": models_map.get(str(node.model_id), "unknown"),
                "source": "override",
                "model_id": str(node.model_id),
                "temperature": node.temperature,
                "timeout_seconds": node.timeout_seconds,
            }
        )
    return items


async def resolve_model_for_node(db: Any, node_id: str) -> Dict[str, Any]:
    node_result = await db.execute(
        select(LLMScopeConfigORM).where(
            LLMScopeConfigORM.scope_type == "node",
            LLMScopeConfigORM.node_id == node_id,
        )
    )
    node_cfg = node_result.scalar_one_or_none()
    if node_cfg:
        model_result = await db.execute(
            select(LLMModelORM).where(LLMModelORM.id == node_cfg.model_id)
        )
        model = model_result.scalar_one_or_none()
        return {
            "node_id": node_id,
            "source": "override",
            "model_id": str(node_cfg.model_id),
            "model_name": model.model_name if model else "unknown",
            "temperature": node_cfg.temperature,
            "timeout_seconds": node_cfg.timeout_seconds,
        }

    global_result = await db.execute(
        select(LLMScopeConfigORM).where(LLMScopeConfigORM.scope_type == "global")
    )
    global_cfg = global_result.scalar_one_or_none()
    if global_cfg:
        model_result = await db.execute(
            select(LLMModelORM).where(LLMModelORM.id == global_cfg.model_id)
        )
        model = model_result.scalar_one_or_none()
        return {
            "node_id": node_id,
            "source": "global_default",
            "model_id": str(global_cfg.model_id),
            "model_name": model.model_name if model else "unknown",
            "temperature": global_cfg.temperature,
            "timeout_seconds": global_cfg.timeout_seconds,
        }

    return {
        "node_id": node_id,
        "source": "none",
        "model_id": None,
        "model_name": None,
        "temperature": 0.5,
        "timeout_seconds": 60,
    }


async def set_scope_config(
    db: Any,
    scope_type: str,
    model_id: str,
    node_id: Optional[str] = None,
    temperature: Optional[float] = None,
    timeout: Optional[int] = None,
) -> Dict[str, Any]:
    if scope_type == "global":
        return await set_global_default(
            db, model_id, temperature or 0.5, timeout or 60
        )
    if scope_type == "node":
        if not node_id:
            raise ValueError("node_id is required for node scope")
        return await set_node_override(db, node_id, model_id, temperature, timeout)
    raise ValueError("scope_type must be 'global' or 'node'")


async def remove_scope_config(db: Any, config_id: str) -> bool:
    result = await db.execute(
        delete(LLMScopeConfigORM)
        .where(LLMScopeConfigORM.id == config_id)
        .returning(LLMScopeConfigORM.id)
    )
    deleted = result.scalar_one_or_none()
    await db.flush()
    await db.commit()
    return deleted is not None


# ── Usage & Cost ──
async def log_usage(
    db: Any,
    model_id: str,
    node_id: str,
    provider_region: str,
    input_tokens: int,
    output_tokens: int,
    latency_ms: int,
    status: str,
    error: Optional[str] = None,
) -> Dict[str, Any]:
    orm = LLMUsageLogORM(
        model_id=model_id,
        node_id=node_id,
        provider_region=provider_region,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        latency_ms=latency_ms,
        status=status,
        error_message=error,
    )
    db.add(orm)
    await db.flush()
    await db.commit()
    await db.refresh(orm)
    return _usage_to_dict(orm)


def _calc_cost(
    input_tokens: int,
    output_tokens: int,
    inp_price: Optional[Any],
    out_price: Optional[Any],
    currency: str,
) -> float:
    if inp_price is None or out_price is None:
        return 0.0
    cost = (input_tokens / 1000) * float(inp_price) + (output_tokens / 1000) * float(out_price)
    if currency == "USD":
        cost *= 7.2
    return round(cost, 4)


async def get_cost_summary(db: Any, period_days: int = 7) -> Dict[str, Any]:
    since = datetime.now(timezone.utc) - timedelta(days=period_days)

    rows_result = await db.execute(
        select(
            LLMUsageLogORM,
            LLMModelORM.model_name,
            LLMPricingORM.input_price_per_1k,
            LLMPricingORM.output_price_per_1k,
            LLMPricingORM.currency,
        )
        .outerjoin(LLMModelORM, LLMUsageLogORM.model_id == LLMModelORM.id)
        .outerjoin(LLMPricingORM, LLMModelORM.model_name == LLMPricingORM.model_name)
        .where(LLMUsageLogORM.created_at >= since)
    )
    rows = rows_result.all()

    total_calls = len(rows)
    total_input = 0
    total_output = 0
    total_cost = 0.0

    by_model_key: Dict[str, Dict[str, Any]] = defaultdict(
        lambda: {"calls": 0, "input_tokens": 0, "output_tokens": 0, "cost_cny": 0.0}
    )
    by_node_key: Dict[str, Dict[str, Any]] = defaultdict(
        lambda: {"calls": 0, "input_tokens": 0, "output_tokens": 0, "cost_cny": 0.0}
    )
    trend_day: Dict[str, Dict[str, Any]] = defaultdict(
        lambda: {"calls": 0, "input_tokens": 0, "output_tokens": 0, "cost_cny": 0.0}
    )

    for log, model_name, inp_price, out_price, currency in rows:
        cost = _calc_cost(
            log.input_tokens,
            log.output_tokens,
            inp_price,
            out_price,
            currency or "CNY",
        )
        total_input += log.input_tokens
        total_output += log.output_tokens
        total_cost += cost

        m_name = model_name or "unknown"
        by_model_key[m_name]["calls"] += 1
        by_model_key[m_name]["input_tokens"] += log.input_tokens
        by_model_key[m_name]["output_tokens"] += log.output_tokens
        by_model_key[m_name]["cost_cny"] += cost

        by_node_key[log.node_id]["calls"] += 1
        by_node_key[log.node_id]["input_tokens"] += log.input_tokens
        by_node_key[log.node_id]["output_tokens"] += log.output_tokens
        by_node_key[log.node_id]["cost_cny"] += cost

        day = log.created_at.strftime("%Y-%m-%d")
        trend_day[day]["calls"] += 1
        trend_day[day]["input_tokens"] += log.input_tokens
        trend_day[day]["output_tokens"] += log.output_tokens
        trend_day[day]["cost_cny"] += cost

    model_id_map: Dict[str, str] = {}
    if by_model_key:
        m_res = await db.execute(
            select(LLMModelORM.id, LLMModelORM.model_name).where(
                LLMModelORM.model_name.in_(list(by_model_key.keys()))
            )
        )
        model_id_map = {name: str(mid) for mid, name in m_res.all()}

    by_model = [
        {
            "model_id": model_id_map.get(name),
            "model_name": name,
            "calls": data["calls"],
            "cost_cny": round(data["cost_cny"], 4),
        }
        for name, data in sorted(by_model_key.items())
    ]

    by_node = [
        {
            "node_id": node_id,
            "calls": data["calls"],
            "cost_cny": round(data["cost_cny"], 4),
        }
        for node_id, data in sorted(by_node_key.items())
    ]

    trend = [
        {
            "date": day,
            "calls": data["calls"],
            "cost_cny": round(data["cost_cny"], 4),
        }
        for day, data in sorted(trend_day.items())
    ]

    return {
        "period_days": period_days,
        "total_calls": total_calls,
        "total_input_tokens": total_input,
        "total_output_tokens": total_output,
        "estimated_cost_cny": round(total_cost, 4),
        "by_model": by_model,
        "by_node": by_node,
        "trend": trend,
    }


async def get_usage_logs(
    db: Any,
    model_id: Optional[str] = None,
    node_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    query = select(LLMUsageLogORM).order_by(LLMUsageLogORM.created_at.desc())
    if model_id:
        query = query.where(LLMUsageLogORM.model_id == model_id)
    if node_id:
        query = query.where(LLMUsageLogORM.node_id == node_id)
    if start_date:
        query = query.where(LLMUsageLogORM.created_at >= datetime.fromisoformat(start_date))
    if end_date:
        query = query.where(LLMUsageLogORM.created_at <= datetime.fromisoformat(end_date))
    query = query.limit(limit)
    result = await db.execute(query)
    return [_usage_to_dict(u) for u in result.scalars().all()]


# ── LLM Router (Phase 5 P5-1) ──

class LLMRouter:
    """按模态自动路由到合适的 LLM 模型.

    纯决策类：只返回模型配置，不实际调用 LLM。
    """

    @staticmethod
    async def route(
        db: Any,
        modality: str,
        preferred_provider: Optional[str] = None,
    ) -> Dict[str, Any]:
        """按模态路由到最优模型.

        策略:
        1. 查询所有 active 模型，筛选支持该模态的
        2. 国内首选可用 → 返回国内模型
        3. 国内无可用 → 返回海外兜底，标记 cross_border_risk=True
        4. 无可用的 → 抛出 ValueError
        """
        from sqlalchemy import select

        result = await db.execute(
            select(LLMModelORM).where(LLMModelORM.status == "active")
        )
        models = result.scalars().all()

        candidates = []
        for m in models:
            ms = m.modality_support or {}
            if ms.get(modality, False):
                region = get_provider_region(m.provider)
                candidates.append({
                    "model_id": str(m.id),
                    "provider": m.provider,
                    "model_name": m.model_name,
                    "region": region,
                    "endpoint_base_url": m.endpoint_base_url,
                })

        if not candidates:
            raise ValueError(f"No active model supports modality: {modality}")

        # 优先国内
        domestic = [c for c in candidates if c["region"] == "domestic"]
        if domestic:
            # 若有 preferred_provider 则优先匹配
            if preferred_provider:
                matched = [c for c in domestic if c["provider"] == preferred_provider]
                if matched:
                    chosen = matched[0]
                    chosen["cross_border_risk"] = False
                    chosen["reason"] = f"domestic preferred provider: {preferred_provider}"
                    return chosen
            chosen = domestic[0]
            chosen["cross_border_risk"] = False
            chosen["reason"] = "domestic fallback"
            return chosen

        # 海外兜底
        chosen = candidates[0]
        chosen["cross_border_risk"] = True
        chosen["reason"] = "overseas fallback (domestic unavailable)"
        return chosen


async def route_model_by_modality(
    db: Any,
    modality: str,
    preferred_provider: Optional[str] = None,
    node_id: str = "router",
) -> Dict[str, Any]:
    """高层路由入口：调用 LLMRouter + 记录路由决策日志."""
    decision = await LLMRouter.route(db, modality, preferred_provider)

    # 记录路由决策日志
    await log_usage(
        db=db,
        model_id=decision["model_id"],
        node_id=node_id,
        provider_region=decision["region"],
        input_tokens=0,
        output_tokens=0,
        latency_ms=0,
        status="ROUTED",
        error=f"cross_border_risk={decision['cross_border_risk']}; reason={decision['reason']}",
    )

    return decision


# ── Test helpers ──
async def clear_llm_hub_data(db: Any) -> None:
    await db.execute(delete(LLMUsageLogORM))
    await db.execute(delete(LLMScopeConfigORM))
    await db.execute(delete(LLMModelORM))
    await db.flush()
    await db.commit()
