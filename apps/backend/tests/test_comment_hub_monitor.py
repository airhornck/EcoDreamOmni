"""Tests for CommentHub Monitor — v4.0 Phase 2 P2-3."""


from src.services.comment_hub_monitor import (
    AlertRule,
    CommentHubMonitor,
    CommentMonitor,
    MonitoredComment,
    ReplyRule,
    ReplyStrategyEngine,
    SentimentAlertEngine,
)


class TestCommentMonitor:
    def test_fetch_comments(self):
        cm = CommentMonitor()
        comments = cm.fetch_comments("content_001", "acc_001", count=5)
        assert len(comments) == 5
        assert all(c.content_id == "content_001" for c in comments)

    def test_list_comments_with_filter(self):
        cm = CommentMonitor()
        cm.fetch_comments("content_001", "acc_001", count=10)
        all_comments = cm.list_comments()
        assert len(all_comments) >= 10

        negative = cm.list_comments(sentiment="negative")
        # At least some should be negative from sample data
        assert isinstance(negative, list)


class TestReplyStrategyEngine:
    def test_match_thanks(self):
        engine = ReplyStrategyEngine()
        matches = engine.match("谢谢分享，非常有用！", "positive")
        assert len(matches) > 0
        assert any(m.id == "rule_thanks" for m in matches)

    def test_match_question(self):
        engine = ReplyStrategyEngine()
        matches = engine.match("这个怎么弄？")
        assert any(m.id == "rule_question" for m in matches)

    def test_match_negative(self):
        engine = ReplyStrategyEngine()
        matches = engine.match("感觉很坑，踩雷了", "negative")
        assert any(m.id == "rule_negative" for m in matches)

    def test_generate_reply(self):
        engine = ReplyStrategyEngine()
        result = engine.generate_reply("谢谢分享，非常有用！", "positive")
        assert result is not None
        assert result["rule_id"] == "rule_thanks"
        assert "不用谢" in result["reply"]

    def test_no_match_returns_none(self):
        engine = ReplyStrategyEngine()
        result = engine.generate_reply("xyz abc 12345")
        assert result is None

    def test_add_custom_rule(self):
        engine = ReplyStrategyEngine()
        engine.add_rule(ReplyRule(
            id="rule_custom",
            name="Custom",
            keywords=["custom"],
            reply_template="Custom reply",
        ))
        matches = engine.match("this is custom")
        assert any(m.id == "rule_custom" for m in matches)


class TestSentimentAlertEngine:
    def test_evaluate_no_alert_when_safe(self):
        engine = SentimentAlertEngine()
        rule = AlertRule(id="ar_1", negative_threshold=0.5, min_comment_count=5)
        engine.add_rule(rule)

        comments = [
            MonitoredComment(
                id=f"c{i}", content_id="c1", account_id="a1",
                author_id="u1", text="good", sentiment="positive",
                created_at="2026-06-03T10:00:00+00:00",
            )
            for i in range(10)
        ]
        alerts = engine.evaluate(comments, "ar_1")
        assert len(alerts) == 0

    def test_evaluate_triggers_alert(self):
        engine = SentimentAlertEngine()
        rule = AlertRule(id="ar_1", negative_threshold=0.3, min_comment_count=5)
        engine.add_rule(rule)

        comments = [
            MonitoredComment(
                id=f"c{i}", content_id="c1", account_id="a1",
                author_id="u1", text="bad", sentiment="negative",
                created_at="2026-06-03T10:00:00+00:00",
            )
            for i in range(10)
        ]
        alerts = engine.evaluate(comments, "ar_1")
        assert len(alerts) == 1
        assert alerts[0].level in ("warning", "critical")
        assert alerts[0].negative_ratio == 1.0

    def test_list_alerts_with_filter(self):
        engine = SentimentAlertEngine()
        rule = AlertRule(id="ar_1", negative_threshold=0.1, min_comment_count=1)
        engine.add_rule(rule)

        comments = [
            MonitoredComment(
                id="c1", content_id="c1", account_id="a1",
                author_id="u1", text="bad", sentiment="negative",
                created_at="2026-06-03T10:00:00+00:00",
            )
        ]
        engine.evaluate(comments, "ar_1")
        assert len(engine.list_alerts()) == 1
        assert len(engine.list_alerts(level="warning")) == 0  # 100% negative → critical
        assert len(engine.list_alerts(level="critical")) == 1


class TestCommentHubMonitorFacade:
    def test_facade_initialized(self):
        hub = CommentHubMonitor()
        assert hub.monitor is not None
        assert hub.strategy is not None
        assert hub.alert is not None
