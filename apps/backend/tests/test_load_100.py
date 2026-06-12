"""Load Tests — W28: 100-account concurrency + degradation.

Targets (upgraded from W22):
  - 100 concurrent predictions: P95 < 600ms
  - 100 concurrent compliance: P95 < 300ms
  - Mixed workload: P95 < 3000ms
  - Degradation: system remains responsive under overload
"""

import pytest
import time
import concurrent.futures
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.services import compliance_service, pool_predictor_service
from src.services.prediction_engine import predict_engagement
from src.services.api_platform import check_rate_limit


# Warm-up jieba before timed tests
def _warmup():
    compliance_service.check_single("warmup", content_id="warmup")


@pytest.fixture(scope="module", autouse=True)
def warmup_compliance():
    _warmup()


def _predict_one(i: int) -> dict:
    start = time.perf_counter()
    result = predict_engagement(
        platform="xhs",
        lifecycle_phase="growth",
        content_type="note",
        word_count=300,
        has_image=True,
        publish_hour=12 + (i % 12),
        topic_heat=50.0 + (i % 50),
    )
    elapsed = (time.perf_counter() - start) * 1000
    return {"success": True, "latency_ms": elapsed, "result": result}


def _compliance_one(i: int) -> dict:
    start = time.perf_counter()
    result = compliance_service.check_single(
        text="Dog nutrition tips for beginners",
        content_id=f"load-100-{i}",
    )
    elapsed = (time.perf_counter() - start) * 1000
    return {"success": True, "latency_ms": elapsed, "result": result}


def _rate_limit_one(i: int, tenant: str) -> dict:
    start = time.perf_counter()
    result = check_rate_limit(tenant, "api", max_requests=500, window_seconds=60)
    elapsed = (time.perf_counter() - start) * 1000
    return {"success": True, "latency_ms": elapsed, "allowed": result["allowed"]}


# ─── 100 Concurrent Prediction ───

def test_prediction_concurrent_100():
    with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
        futures = [executor.submit(_predict_one, i) for i in range(100)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    latencies = [r["latency_ms"] for r in results]
    p95 = sorted(latencies)[int(len(latencies) * 0.95) - 1]
    assert p95 < 600, f"P95 prediction latency {p95}ms exceeds 600ms target"
    assert all(r["success"] for r in results)


# ─── 100 Concurrent Compliance ───

def test_compliance_concurrent_100():
    with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
        futures = [executor.submit(_compliance_one, i) for i in range(100)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    latencies = [r["latency_ms"] for r in results]
    p95 = sorted(latencies)[int(len(latencies) * 0.95) - 1]
    assert p95 < 300, f"P95 compliance latency {p95}ms exceeds 300ms target"
    assert all(r["success"] for r in results)


# ─── Rate Limit Under Load ───

def test_rate_limit_100_requests():
    tenant = "load-test-tenant"
    with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
        futures = [executor.submit(_rate_limit_one, i, tenant) for i in range(100)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    assert all(r["success"] for r in results)
    # With max_requests=500, all 100 should be allowed
    allowed_count = sum(1 for r in results if r["allowed"])
    assert allowed_count == 100


# ─── Mixed Workload 100 ───

def test_mixed_workload_100():
    def mixed_op(i: int) -> dict:
        start = time.perf_counter()
        _predict_one(i)
        _compliance_one(i)
        elapsed = (time.perf_counter() - start) * 1000
        return {"success": True, "latency_ms": elapsed}

    with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
        futures = [executor.submit(mixed_op, i) for i in range(100)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    assert all(r["success"] for r in results)
    latencies = [r["latency_ms"] for r in results]
    p95 = sorted(latencies)[int(len(latencies) * 0.95) - 1]
    assert p95 < 3000, f"P95 mixed workload latency {p95}ms exceeds 3000ms target"


# ─── Degradation: overload with rate limit ───

def test_degradation_rate_limited():
    tenant = "degrade-test"
    # Exhaust the bucket
    for _ in range(105):
        check_rate_limit(tenant, "strict", max_requests=100, window_seconds=60)

    # Should be rejected
    result = check_rate_limit(tenant, "strict", max_requests=100, window_seconds=60)
    assert result["allowed"] is False
    assert result["remaining"] == 0
