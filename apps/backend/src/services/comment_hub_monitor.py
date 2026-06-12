"""CommentHub Monitor — v4.0 Phase 2 P2-3.

扩展 CommentHub 职责：
1. 评论监控（批量抓取 + 实时监控）
2. 自动回复策略（规则引擎）
3. 舆情预警（负面评论聚合 + 趋势分析 + 阈值告警）
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

from src.services.comment_hub import _analyze_sentiment


# ═══════════════════════════════════════════════════════
# 1. Comment Monitor
# ═══════════════════════════════════════════════════════

@dataclass
class MonitoredComment:
    id: str
    content_id: str
    account_id: str
    author_id: str
    text: str
    sentiment: str  # positive | neutral | negative
    created_at: str
    platform: str = "xhs"


class CommentMonitor:
    """Monitor and collect comments for content items."""

    def __init__(self):
        self._comments: Dict[str, MonitoredComment] = {}

    def fetch_comments(
        self,
        content_id: str,
        account_id: str,
        count: int = 20,
    ) -> List[MonitoredComment]:
        """MVP: Simulate fetching comments from platform."""
        results = []
        for i in range(count):
            cid = f"cm_{secrets.token_urlsafe(6)}"
            text = self._sample_comment_text(i)
            sentiment = _analyze_sentiment(text)
            comment = MonitoredComment(
                id=cid,
                content_id=content_id,
                account_id=account_id,
                author_id=f"user_{i}",
                text=text,
                sentiment=sentiment,
                created_at=datetime.now(timezone.utc).isoformat(),
            )
            self._comments[cid] = comment
            results.append(comment)
        return results

    def list_comments(
        self,
        content_id: Optional[str] = None,
        account_id: Optional[str] = None,
        sentiment: Optional[str] = None,
    ) -> List[MonitoredComment]:
        results = list(self._comments.values())
        if content_id:
            results = [c for c in results if c.content_id == content_id]
        if account_id:
            results = [c for c in results if c.account_id == account_id]
        if sentiment:
            results = [c for c in results if c.sentiment == sentiment]
        return results

    def get_comment(self, comment_id: str) -> Optional[MonitoredComment]:
        return self._comments.get(comment_id)

    @staticmethod
    def _sample_comment_text(index: int) -> str:
        samples = [
            "谢谢分享，非常有用！",
            "这个办法真的有效吗？",
            "我家猫咪也有这个问题，怎么办？",
            "内容很棒，收藏了！",
            "有点误导人吧，不太靠谱",
            "博主讲得很清楚，学到了",
            "这是什么牌子的产品？",
            "感觉没什么用，踩坑了",
            "太及时了，正好需要",
            "为什么我的猫不一样",
        ]
        return samples[index % len(samples)]


# ═══════════════════════════════════════════════════════
# 2. Auto-Reply Strategy Engine
# ═══════════════════════════════════════════════════════

@dataclass
class ReplyRule:
    id: str
    name: str
    keywords: List[str]
    sentiment: Optional[str] = None  # match any if None
    reply_template: str = ""
    action: str = "suggest"  # suggest | auto_reply | flag
    priority: int = 0
    enabled: bool = True


_DEFAULT_RULES: List[ReplyRule] = [
    ReplyRule(
        id="rule_thanks",
        name="感谢回复",
        keywords=["谢谢", "感谢", "有用", "学到了"],
        sentiment="positive",
        reply_template="不用谢~ 有帮助就好！有问题随时交流 😊",
        action="suggest",
        priority=10,
    ),
    ReplyRule(
        id="rule_question",
        name="提问回复",
        keywords=["怎么", "怎么办", "如何", "为什么", "吗？"],
        reply_template="感谢提问！具体情况建议咨询专业兽医，也可以参考我之前的笔记~",
        action="suggest",
        priority=20,
    ),
    ReplyRule(
        id="rule_negative",
        name="负面评论标记",
        keywords=["坑", "骗", "没用", "踩坑", "失望"],
        sentiment="negative",
        reply_template="抱歉给您带来不好的体验，可以私信告诉我具体情况吗？",
        action="flag",
        priority=100,
    ),
]


class ReplyStrategyEngine:
    """Rule-based engine for auto-reply strategies."""

    def __init__(self):
        self._rules: Dict[str, ReplyRule] = {r.id: r for r in _DEFAULT_RULES}

    def add_rule(self, rule: ReplyRule) -> None:
        self._rules[rule.id] = rule

    def list_rules(self) -> List[ReplyRule]:
        return sorted(
            [r for r in self._rules.values() if r.enabled],
            key=lambda r: r.priority,
            reverse=True,
        )

    def match(self, comment_text: str, comment_sentiment: str = "neutral") -> List[ReplyRule]:
        """Find all matching rules for a comment."""
        matches = []
        for rule in self.list_rules():
            # Check sentiment match
            if rule.sentiment and rule.sentiment != comment_sentiment:
                continue
            # Check keyword match
            if any(kw in comment_text for kw in rule.keywords):
                matches.append(rule)
        return matches

    def generate_reply(self, comment_text: str, comment_sentiment: str = "neutral") -> Optional[Dict[str, Any]]:
        """Generate a reply suggestion based on matching rules."""
        matches = self.match(comment_text, comment_sentiment)
        if not matches:
            return None
        best = matches[0]
        return {
            "rule_id": best.id,
            "rule_name": best.name,
            "reply": best.reply_template,
            "action": best.action,
            "matched_keywords": [kw for kw in best.keywords if kw in comment_text],
        }


# ═══════════════════════════════════════════════════════
# 3. Sentiment Alert Engine
# ═══════════════════════════════════════════════════════

@dataclass
class AlertRule:
    id: str
    account_id: Optional[str] = None
    content_id: Optional[str] = None
    negative_threshold: float = 0.3  # ratio of negative comments
    min_comment_count: int = 10
    window_minutes: int = 60
    enabled: bool = True


@dataclass
class Alert:
    id: str
    rule_id: str
    level: str  # warning | critical
    message: str
    negative_ratio: float
    total_comments: int
    created_at: str
    account_id: Optional[str] = None
    content_id: Optional[str] = None


class SentimentAlertEngine:
    """Monitor sentiment trends and generate alerts."""

    def __init__(self):
        self._alert_rules: Dict[str, AlertRule] = {}
        self._alerts: List[Alert] = []

    def add_rule(self, rule: AlertRule) -> None:
        self._alert_rules[rule.id] = rule

    def list_rules(self) -> List[AlertRule]:
        return list(self._alert_rules.values())

    def evaluate(
        self,
        comments: List[MonitoredComment],
        rule_id: Optional[str] = None,
    ) -> List[Alert]:
        """Evaluate comments against alert rules and generate alerts."""
        new_alerts = []
        rules_to_check = [self._alert_rules[rule_id]] if rule_id else self.list_rules()

        for rule in rules_to_check:
            if not rule.enabled:
                continue

            filtered = comments
            if rule.account_id:
                filtered = [c for c in filtered if c.account_id == rule.account_id]
            if rule.content_id:
                filtered = [c for c in filtered if c.content_id == rule.content_id]

            # Time window filter
            cutoff = datetime.now(timezone.utc) - timedelta(minutes=rule.window_minutes)
            filtered = [
                c for c in filtered
                if datetime.fromisoformat(c.created_at) > cutoff
            ]

            if len(filtered) < rule.min_comment_count:
                continue

            negative_count = sum(1 for c in filtered if c.sentiment == "negative")
            negative_ratio = negative_count / len(filtered)

            if negative_ratio >= rule.negative_threshold:
                level = "critical" if negative_ratio >= 0.5 else "warning"
                alert = Alert(
                    id=f"alt_{secrets.token_urlsafe(8)}",
                    rule_id=rule.id,
                    level=level,
                    message=f"负面评论占比 {negative_ratio:.1%}，超过阈值 {rule.negative_threshold:.0%}",
                    negative_ratio=negative_ratio,
                    total_comments=len(filtered),
                    created_at=datetime.now(timezone.utc).isoformat(),
                    account_id=rule.account_id,
                    content_id=rule.content_id,
                )
                self._alerts.append(alert)
                new_alerts.append(alert)

        return new_alerts

    def list_alerts(
        self,
        level: Optional[str] = None,
        account_id: Optional[str] = None,
    ) -> List[Alert]:
        results = self._alerts
        if level:
            results = [a for a in results if a.level == level]
        if account_id:
            results = [a for a in results if a.account_id == account_id]
        return results


# ═══════════════════════════════════════════════════════
# Facade
# ═══════════════════════════════════════════════════════

class CommentHubMonitor:
    """Unified facade for CommentHub monitoring capabilities."""

    def __init__(self):
        self.monitor = CommentMonitor()
        self.strategy = ReplyStrategyEngine()
        self.alert = SentimentAlertEngine()
