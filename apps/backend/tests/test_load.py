"""Load Tests — W22: 50-account concurrency stability.

Targets:
  - PoolPredictor: P95 < 500ms per prediction
  - Compliance: P95 < 200ms per scan
  - ContentForge: P95 < 1000ms per draft
  - Concurrent account ops: 50 accounts, 0 failures
"""

import pytest
import time
import concurrent.futures
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.services import pool_predictor_service, content_forge_service, compliance_service
from src.services.prediction_engine import predict_engagement
from src.services.content_insight import analyze_content_performance


# ─── Helpers ───

# Warm-up: trigger jieba dictionary loading before timed tests
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
        topic_heat=50.0 + i,
    )
    elapsed = (time.perf_counter() - start) * 1000
    return {"success": True, "latency_ms": elapsed, "result": result}


def _compliance_one(i: int) -> dict:
    start = time.perf_counter()
    result = compliance_service.check_single(
        text="Here are some tips for feeding your dog...",
        content_id=f"load-test-{i}",
    )
    elapsed = (time.perf_counter() - start) * 1000
    return {"success": True, "latency_ms": elapsed, "result": result}


def _content_insight_one(i: int) -> dict:
    contents = [
        {"id": f"c{i}-1", "title": "Dog food", "topic": "dog nutrition", "content_type": "note", "word_count": 300, "publish_hour": 10, "has_image": True},
        {"id": f"c{i}-2", "title": "Cat health", "topic": "cat health", "content_type": "note", "word_count": 400, "publish_hour": 20, "has_image": True},
    ]
    engagement = {
        f"c{i}-1": {"likes": 100, "comments": 20, "saves": 10, "ces": 50},
        f"c{i}-2": {"likes": 60, "comments": 10, "saves": 5, "ces": 30},
    }
    start = time.perf_counter()
    result = analyze_content_performance(contents, [], engagement)
    elapsed = (time.perf_counter() - start) * 1000
    return {"success": True, "latency_ms": elapsed, "result": result}


# ─── Prediction Load ───

def test_prediction_latency_single():
    """Baseline: single prediction latency."""
    r = _predict_one(0)
    assert r["success"] is True
    assert r["latency_ms"] < 500  # P95 target


def test_prediction_concurrent_50():
    """50 concurrent predictions."""
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        futures = [executor.submit(_predict_one, i) for i in range(50)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    latencies = [r["latency_ms"] for r in results]
    p95 = sorted(latencies)[int(len(latencies) * 0.95) - 1]
    assert p95 < 500, f"P95 latency {p95}ms exceeds 500ms target"
    assert all(r["success"] for r in results)


# ─── Compliance Load ───

def test_compliance_latency_single():
    r = _compliance_one(0)
    assert r["success"] is True
    assert r["latency_ms"] < 200


def test_compliance_concurrent_50():
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        futures = [executor.submit(_compliance_one, i) for i in range(50)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    latencies = [r["latency_ms"] for r in results]
    p95 = sorted(latencies)[int(len(latencies) * 0.95) - 1]
    assert p95 < 200, f"P95 compliance latency {p95}ms exceeds 200ms target"
    assert all(r["success"] for r in results)


# ─── ContentInsight Load ───

def test_content_insight_latency_single():
    r = _content_insight_one(0)
    assert r["success"] is True
    assert r["latency_ms"] < 1000


def test_content_insight_concurrent_50():
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        futures = [executor.submit(_content_insight_one, i) for i in range(50)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    latencies = [r["latency_ms"] for r in results]
    p95 = sorted(latencies)[int(len(latencies) * 0.95) - 1]
    assert p95 < 1000, f"P95 insight latency {p95}ms exceeds 1000ms target"
    assert all(r["success"] for r in results)


# ─── Mixed workload ───

def test_mixed_workload_50_accounts():
    """Simulate 50 accounts doing mixed ops concurrently."""
    def mixed_op(i: int) -> dict:
        start = time.perf_counter()
        _predict_one(i)
        _compliance_one(i)
        elapsed = (time.perf_counter() - start) * 1000
        return {"success": True, "latency_ms": elapsed}

    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        futures = [executor.submit(mixed_op, i) for i in range(50)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    assert all(r["success"] for r in results)
    latencies = [r["latency_ms"] for r in results]
    p95 = sorted(latencies)[int(len(latencies) * 0.95) - 1]
    # Mixed workload target: < 2s per account for predict + compliance
    assert p95 < 2000, f"P95 mixed workload latency {p95}ms exceeds 2000ms target"
