"""Context Manager — compaction and window management for Harness.

Aligned with dev-plan H6: "Context Manager: compaction and window management".

Rules:
  - Sliding window: keep last N messages (default 20)
  - Summarization: when window exceeds N, summarize oldest batch into a single message
  - Priority pinning: system messages and pinned items are never evicted
  - Token budget: approximate token counting for rough estimation
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ContextMessage:
    role: str  # system | user | assistant | tool
    content: str
    pinned: bool = False
    meta: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ContextWindow:
    messages: List[ContextMessage] = field(default_factory=list)
    max_messages: int = 20
    summary: Optional[str] = None


_windows: Dict[str, ContextWindow] = {}


def _approx_tokens(text: str) -> int:
    """Very rough token estimator: ~4 chars per token."""
    return max(1, len(text) // 4)


def _summarize(batch: List[ContextMessage]) -> str:
    """MVP summarization: concatenate roles and truncate."""
    lines = [f"[{m.role}] {m.content[:80]}..." if len(m.content) > 80 else f"[{m.role}] {m.content}" for m in batch]
    return " | ".join(lines)


def create_window(session_id: str, max_messages: int = 20) -> ContextWindow:
    win = ContextWindow(max_messages=max_messages)
    _windows[session_id] = win
    return win


def get_window(session_id: str) -> Optional[ContextWindow]:
    return _windows.get(session_id)


def add_message(session_id: str, role: str, content: str, pinned: bool = False, meta: Optional[Dict[str, Any]] = None) -> ContextWindow:
    """Add a message to the context window, compacting if needed."""
    win = _windows.get(session_id)
    if win is None:
        win = create_window(session_id)

    msg = ContextMessage(role=role, content=content, pinned=pinned, meta=meta or {})
    win.messages.append(msg)

    # Compact: evict oldest non-pinned messages if over limit
    while len([m for m in win.messages if m.pinned]) + len([m for m in win.messages if not m.pinned]) > win.max_messages:
        # Find oldest non-pinned
        for i, m in enumerate(win.messages):
            if not m.pinned:
                # Summarize before removing
                batch = win.messages[:i + 1]
                pinned_in_batch = [m for m in batch if m.pinned]
                evictable = [m for m in batch if not m.pinned]
                if evictable:
                    summary = _summarize(evictable)
                    win.summary = (win.summary or "") + "\n" + summary if win.summary else summary
                    win.messages = pinned_in_batch + win.messages[i + 1:]
                break
        else:
            # All pinned — can't compact further
            break

    return win


def get_messages(session_id: str, include_summary: bool = True) -> List[Dict[str, Any]]:
    """Get all messages in a window, optionally prepending summary."""
    win = _windows.get(session_id)
    if not win:
        return []

    result: List[Dict[str, Any]] = []
    if include_summary and win.summary:
        result.append({"role": "system", "content": f"[Summary of earlier context]: {win.summary[:500]}"})
    for m in win.messages:
        result.append({"role": m.role, "content": m.content, "meta": m.meta})
    return result


def pin_message(session_id: str, index: int) -> bool:
    win = _windows.get(session_id)
    if win and 0 <= index < len(win.messages):
        win.messages[index].pinned = True
        return True
    return False


def clear_window(session_id: str) -> bool:
    return _windows.pop(session_id, None) is not None


def window_stats(session_id: str) -> Dict[str, Any]:
    win = _windows.get(session_id)
    if not win:
        return {"exists": False}
    total_tokens = sum(_approx_tokens(m.content) for m in win.messages)
    return {
        "exists": True,
        "message_count": len(win.messages),
        "pinned_count": sum(1 for m in win.messages if m.pinned),
        "approx_tokens": total_tokens,
        "has_summary": win.summary is not None,
    }
