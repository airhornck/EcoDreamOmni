"""Metrics API — W26: Prometheus-compatible metrics endpoint.

Routes:
  GET /metrics          — Prometheus text format
  GET /health/detailed  — Detailed health with component status
"""

from typing import Dict
from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

router = APIRouter(tags=["metrics"])

# In-memory counters (MVP; production uses prometheus_client)
_counters: Dict[str, int] = {}
_histograms: Dict[str, list] = {}
_gauges: Dict[str, float] = {}


def inc_counter(name: str, labels: Dict[str, str] = None, value: int = 1):
    key = f"{name}" + ("{" + ",".join(f'{k}="{v}"' for k, v in (labels or {}).items()) + "}" if labels else "")
    _counters[key] = _counters.get(key, 0) + value


def observe_histogram(name: str, value: float, labels: Dict[str, str] = None):
    key = f"{name}" + ("{" + ",".join(f'{k}="{v}"' for k, v in (labels or {}).items()) + "}" if labels else "")
    _histograms.setdefault(key, []).append(value)


def set_gauge(name: str, value: float, labels: Dict[str, str] = None):
    key = f"{name}" + ("{" + ",".join(f'{k}="{v}"' for k, v in (labels or {}).items()) + "}" if labels else "")
    _gauges[key] = value


@router.get("/metrics", response_class=PlainTextResponse)
def prometheus_metrics():
    """Prometheus text format metrics."""
    lines = ["# EcoDreamOmni MVP metrics"]

    for key, value in _counters.items():
        lines.append(f"{key} {value}")

    for key, values in _histograms.items():
        if values:
            lines.append(f"{key}_count {len(values)}")
            lines.append(f"{key}_sum {sum(values):.4f}")
            lines.append(f"{key}_avg {sum(values)/len(values):.4f}")

    for key, value in _gauges.items():
        lines.append(f"{key} {value}")

    return "\n".join(lines)


@router.get("/health/detailed")
def detailed_health():
    """Detailed health check with component status."""
    from src.services import tenant_service, pool_predictor_service

    components = {
        "api": "ok",
        "auth": "ok",
        "predictor": "ok" if pool_predictor_service.model_metrics() else "degraded",
        "tenants": "ok" if tenant_service.list_tenants() is not None else "degraded",
    }

    all_ok = all(v == "ok" for v in components.values())
    return {
        "status": "ok" if all_ok else "degraded",
        "components": components,
        "uptime_seconds": 0,  # MVP placeholder
        "version": "0.2.0-phase3",
    }
