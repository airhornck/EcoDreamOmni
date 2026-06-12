"""DataAnalyst — 24h data回流, MAPE计算, 归因分析, 模型校准触发.

MVP: Simulated data回流 with mock actual metrics.
Production: Real platform API data fetch.
"""

import csv
import io
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

try:
    import pandas as pd
except ImportError:
    pd = None


@dataclass
class DataReport:
    id: str
    account_id: str
    content_id: str
    period: str
    actual_metrics: Dict
    prediction_comparison: Dict
    attribution: Dict
    model_calibration: Dict
    created_at: str = ""


@dataclass
class CalibrationJob:
    id: str
    status: str
    created_at: str
    updated_at: str
    message: str = ""


_report_db: Dict[str, DataReport] = {}
_calibration_jobs: Dict[str, CalibrationJob] = {}
N_MIN = 5


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _compute_actual_ces(actual_likes: int, actual_comments: int, actual_saves: int) -> float:
    """Compute a proxy CES from actual engagement metrics."""
    return max(5.0, float(actual_likes) * 1.5 + float(actual_comments) * 3.0 + float(actual_saves) * 4.5)


def _compute_mape(predicted_ces: float, actual_ces: float) -> float:
    if actual_ces == 0:
        return 0.0
    return abs(predicted_ces - actual_ces) / actual_ces


def _generate_attribution(content_id: str) -> List[Dict]:
    return [
        {"feature": "标题关键词匹配度", "impact": f"+{15 + (hash(content_id) % 10)}%"},
        {"feature": "发布时段", "impact": f"+{8 + (hash(content_id) % 8)}%"},
        {"feature": "标签热度", "impact": f"+{5 + (hash(content_id) % 5)}%"},
    ]


def generate_data_report(
    account_id: str,
    content_id: str,
    predicted_ces: float,
    predicted_pool: str,
    period: str = "24h",
) -> DataReport:
    """Generate a simulated 24h data report."""
    report_id = secrets.token_urlsafe(12)

    # MVP: simulate actual metrics around prediction with noise
    noise = (hash(content_id) % 40) - 20  # -20 to +20
    actual_ces = max(5, predicted_ces + noise)
    actual_exposure = int(actual_ces * 70 + (hash(content_id) % 500))
    actual_likes = int(actual_ces * 0.6)
    actual_comments = int(actual_ces * 0.15)
    actual_saves = int(actual_ces * 0.1)

    mape = _compute_mape(predicted_ces, actual_ces)
    accuracy = predicted_pool == _ces_to_pool(actual_ces)

    attribution_features = _generate_attribution(content_id)

    # Calibration recommendation
    needs_calibration = mape > 0.25
    calibration = {
        "recommendation": "MAPE>25%，建议重训练" if needs_calibration else "MAPE<25%，无需重训练",
        "next_calibration": "立即" if needs_calibration else "7天后",
        "mape": round(mape, 4),
    }

    report = DataReport(
        id=report_id,
        account_id=account_id,
        content_id=content_id,
        period=period,
        actual_metrics={
            "exposure": actual_exposure,
            "likes": actual_likes,
            "saves": actual_saves,
            "comments": actual_comments,
            "shares": int(actual_ces * 0.02),
            "follows": int(actual_ces * 0.01),
            "ces": round(actual_ces, 2),
        },
        prediction_comparison={
            "predicted_ces": round(predicted_ces, 2),
            "actual_ces": round(actual_ces, 2),
            "mape": round(mape, 4),
            "predicted_pool": predicted_pool,
            "actual_pool": _ces_to_pool(actual_ces),
            "accuracy": accuracy,
        },
        attribution={"top_features": attribution_features},
        model_calibration=calibration,
        created_at=_now(),
    )
    _report_db[report_id] = report
    return report


def generate_data_report_from_actuals(
    account_id: str,
    content_id: str,
    actual_likes: int,
    actual_comments: int,
    actual_saves: int,
    predicted_ces: Optional[float] = None,
    predicted_pool: str = "L2",
    period: str = "24h",
) -> DataReport:
    """Generate a data report from actual CSV metrics."""
    report_id = secrets.token_urlsafe(12)
    actual_ces = _compute_actual_ces(actual_likes, actual_comments, actual_saves)

    if predicted_ces is None:
        predicted_ces = actual_ces

    mape = _compute_mape(predicted_ces, actual_ces)
    accuracy = predicted_pool == _ces_to_pool(actual_ces)

    attribution_features = _generate_attribution(content_id)

    needs_calibration = mape > 0.25
    calibration = {
        "recommendation": "MAPE>25%，建议重训练" if needs_calibration else "MAPE<25%，无需重训练",
        "next_calibration": "立即" if needs_calibration else "7天后",
        "mape": round(mape, 4),
    }

    report = DataReport(
        id=report_id,
        account_id=account_id,
        content_id=content_id,
        period=period,
        actual_metrics={
            "likes": actual_likes,
            "saves": actual_saves,
            "comments": actual_comments,
            "ces": round(actual_ces, 2),
        },
        prediction_comparison={
            "predicted_ces": round(predicted_ces, 2),
            "actual_ces": round(actual_ces, 2),
            "mape": round(mape, 4),
            "predicted_pool": predicted_pool,
            "actual_pool": _ces_to_pool(actual_ces),
            "accuracy": accuracy,
        },
        attribution={"top_features": attribution_features},
        model_calibration=calibration,
        created_at=_now(),
    )
    _report_db[report_id] = report
    return report


def import_csv_reports(
    file_content: bytes,
    account_id: str = "",
    predicted_ces: Optional[float] = None,
    predicted_pool: str = "L2",
    period: str = "24h",
) -> List[DataReport]:
    """Parse CSV and create reports for each row."""
    reports = []

    # Try pandas first, fallback to csv module
    df = None
    if pd is not None:
        try:
            df = pd.read_csv(io.BytesIO(file_content))
        except Exception:
            df = None

    if df is None:
        try:
            text = file_content.decode("utf-8-sig")
            reader = csv.DictReader(io.StringIO(text))
            rows = list(reader)
            if not rows:
                raise ValueError("CSV is empty or malformed")
            df = pd.DataFrame(rows)
        except Exception as e:
            raise ValueError(f"Failed to parse CSV: {e}")

    required_cols = {"content_id", "actual_likes", "actual_comments", "actual_saves"}
    if not required_cols.issubset(set(df.columns)):
        raise ValueError(f"CSV must contain columns: {required_cols}")

    for _, row in df.iterrows():
        report = generate_data_report_from_actuals(
            account_id=account_id,
            content_id=str(row["content_id"]),
            actual_likes=int(row["actual_likes"]),
            actual_comments=int(row["actual_comments"]),
            actual_saves=int(row["actual_saves"]),
            predicted_ces=predicted_ces,
            predicted_pool=predicted_pool,
            period=period,
        )
        reports.append(report)
    return reports


def _ces_to_pool(ces: float) -> str:
    if ces < 10:
        return "L0"
    elif ces < 20:
        return "L1"
    elif ces < 35:
        return "L2"
    elif ces < 55:
        return "L3"
    elif ces < 80:
        return "L4"
    else:
        return "L5"


def get_data_report(report_id: str) -> Optional[DataReport]:
    return _report_db.get(report_id)


def get_report_by_content_id(content_id: str) -> Optional[DataReport]:
    """Get the most recent report for a content_id."""
    reports = [r for r in _report_db.values() if r.content_id == content_id]
    if not reports:
        return None
    return sorted(reports, key=lambda r: r.created_at, reverse=True)[0]


def list_data_reports(account_id: Optional[str] = None) -> List[DataReport]:
    reports = list(_report_db.values())
    if account_id:
        reports = [r for r in reports if r.account_id == account_id]
    return sorted(reports, key=lambda r: r.created_at, reverse=True)


def get_dashboard_summary() -> Dict:
    """Aggregate dashboard with empty state and coverage gating."""
    reports = list(_report_db.values())
    if not reports:
        return {
            "has_data": False,
            "guide": "暂无数据，请通过 POST /data-analyst/reports 上传 CSV 或创建报告导入数据。",
            "totalPublished": 0,
            "totalPublishedChange": 0.0,
            "avgCoverage": 0.0,
            "avgMape": 0.0,
            "avgLikes": 0.0,
            "avgLikesChange": 0.0,
            "l3_plus_count": 0,
            "private_messages": 0,
            "week_over_week": "+0%",
            "coverage_applicable": False,
        }

    avg_ces = sum(r.actual_metrics.get("ces", 0) for r in reports) / len(reports)
    avg_likes = sum(r.actual_metrics.get("likes", 0) for r in reports) / len(reports)
    l3_plus = sum(1 for r in reports if r.actual_metrics.get("ces", 0) >= 35)
    pm_count = sum(int(r.actual_metrics.get("ces", 0) * 0.1) for r in reports)

    # Compute coverage and MAPE from prediction comparisons
    valid_comparisons = [r.prediction_comparison for r in reports if r.prediction_comparison]
    avg_coverage = 0.0
    avg_mape = 0.0
    if valid_comparisons:
        avg_coverage = sum(1 for pc in valid_comparisons if pc.get("accuracy", False)) / len(valid_comparisons)
        avg_mape = sum(pc.get("mape", 0) for pc in valid_comparisons) / len(valid_comparisons)

    valid_rows = len(reports)
    coverage_applicable = valid_rows >= N_MIN

    return {
        "has_data": True,
        "published_count": len(reports),
        "totalPublished": len(reports),
        "totalPublishedChange": 0.0,  # MVP mock
        "avgCoverage": round(avg_coverage, 4),
        "avgMape": round(avg_mape, 4),
        "avgLikes": round(avg_likes, 2),
        "avgLikesChange": 0.0,  # MVP mock
        "l3_plus_count": l3_plus,
        "private_messages": pm_count,
        "week_over_week": "+12%",  # MVP mock
        "coverage_applicable": coverage_applicable,
    }


def check_calibration_needed() -> List[Dict]:
    """Check which content items need model calibration."""
    needs_cal = []
    for r in _report_db.values():
        mape = r.prediction_comparison.get("mape", 0)
        if mape > 0.25:
            needs_cal.append({
                "content_id": r.content_id,
                "mape": mape,
                "predicted": r.prediction_comparison.get("predicted_ces"),
                "actual": r.prediction_comparison.get("actual_ces"),
            })
    return needs_cal


def create_calibration_job() -> CalibrationJob:
    """Create a calibration job in pending state (no synchronous retraining)."""
    job_id = secrets.token_urlsafe(12)
    now = _now()
    job = CalibrationJob(
        id=job_id,
        status="pending",
        created_at=now,
        updated_at=now,
        message="等待调度",
    )
    _calibration_jobs[job_id] = job
    return job


def get_calibration_job(job_id: str) -> Optional[CalibrationJob]:
    return _calibration_jobs.get(job_id)


def clear_data_analyst() -> None:
    _report_db.clear()
    _calibration_jobs.clear()
