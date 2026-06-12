"""Publish scheduler: staggered dispatch with frequency ladder per account.

Aligned with detailed design §5.7 — config-driven newbie/growth/mature limits.
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

# Frequency ladder: lifecycle phase -> daily publish limit
_FREQUENCY_LADDER = {
    "cold_start": 1,
    "growth": 3,
    "mature": 5,
}

_DEFAULT_LIMIT = 5

# Time slot spacing (minutes)
_SLOT_SPACING_MINUTES = 30

# Track scheduled times per account
_account_schedule_log: Dict[str, List[str]] = {}


def _today_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _parse_scheduled(at: Optional[str]) -> datetime:
    if at:
        return datetime.fromisoformat(at)
    return datetime.now(timezone.utc)


def _get_daily_limit(account_id: str) -> int:
    """Resolve daily publish limit from account lifecycle phase."""
    from src.models.account_pool import list_pool_entries

    for entry in list_pool_entries():
        if entry.id == account_id or entry.account_id == account_id:
            return _FREQUENCY_LADDER.get(entry.lifecycle_phase, _DEFAULT_LIMIT)
    return _DEFAULT_LIMIT


def _count_today(account_id: str) -> int:
    """Count how many tasks this account has scheduled for today."""
    today = _today_str()
    logs = _account_schedule_log.get(account_id, [])
    return sum(1 for log in logs if log.startswith(today))


def _get_next_slot(account_id: str) -> datetime:
    """Find the next available time slot for this account."""
    now = datetime.now(timezone.utc)
    # Start from next hour boundary
    base = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)

    logs = _account_schedule_log.get(account_id, [])
    occupied_slots = set()
    for log in logs:
        try:
            dt = datetime.fromisoformat(log)
            occupied_slots.add(dt.strftime("%H:%M"))
        except ValueError:
            continue

    # Find first unoccupied slot
    for offset in range(0, 48):  # Up to 24 hours, 30-min slots
        candidate = base + timedelta(minutes=offset * _SLOT_SPACING_MINUTES)
        slot_key = candidate.strftime("%H:%M")
        if slot_key not in occupied_slots:
            return candidate

    # Fallback: just return now + 1 day
    return now + timedelta(days=1)


def schedule_publish(
    draft_id: str,
    account_id: str,
    platform: str,
    preferred_time: Optional[str] = None,
) -> Dict:
    """Schedule a publish task with frequency ladder and stagger enforcement.

    Returns:
        {"success": bool, "task_id": str, "scheduled_at": str, "reason": str}
    """
    # Check daily limit against frequency ladder
    limit = _get_daily_limit(account_id)
    if _count_today(account_id) >= limit:
        return {
            "success": False,
            "task_id": "",
            "scheduled_at": "",
            "reason": f"Account {account_id} has reached daily publish limit ({limit})",
        }

    # Determine time slot
    if preferred_time:
        scheduled_at = datetime.fromisoformat(preferred_time)
    else:
        scheduled_at = _get_next_slot(account_id)

    scheduled_str = scheduled_at.isoformat()

    # Log the slot
    if account_id not in _account_schedule_log:
        _account_schedule_log[account_id] = []
    _account_schedule_log[account_id].append(scheduled_str)

    return {
        "success": True,
        "task_id": "",
        "scheduled_at": scheduled_str,
        "reason": "",
    }


def clear_schedule_log() -> None:
    _account_schedule_log.clear()
