"""Dashboard service: data aggregation for operations homepage."""

from typing import List, Optional, Tuple

from src.models.dashboard import (
    ActivityEntry,
    Alert,
    QuickAction,
    TodayOverview,
    get_activity_log,
    get_alerts,
    get_overview,
    get_quick_actions,
)


def fetch_overview() -> TodayOverview:
    return get_overview()


def fetch_quick_actions() -> List[QuickAction]:
    return get_quick_actions()


def fetch_alerts(level: Optional[str] = None) -> List[Alert]:
    return get_alerts(level)


def fetch_activity_log(limit: int = 20, offset: int = 0) -> Tuple[List[ActivityEntry], int]:
    return get_activity_log(limit, offset)
