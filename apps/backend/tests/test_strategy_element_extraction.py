"""Tests for ViralAnalyzer Strategy Element Extraction."""


from src.services.viral_analyzer_service import (
    AnalysisReport,
    EmotionNode,
    KeywordMatch,
    SectionAnalysis,
    ViralAnalyzerService,
)


def _make_sample_report() -> AnalysisReport:
    return AnalysisReport(
        noteId="note_test_001",
        structureType="避坑排雷型",
        viralScore=85.0,
        keywordMatches=[
            KeywordMatch(keyword="新手养猫", dimension="industry", count=2, weight=1.2),
            KeywordMatch(keyword="驱虫攻略", dimension="industry", count=1, weight=1.0),
            KeywordMatch(keyword="避坑", dimension="structure", count=1, weight=1.0),
            KeywordMatch(keyword="省钱", dimension="effect", count=1, weight=1.1),
        ],
        titleAnalysis=SectionAnalysis(score=82, strengths=["吸睛"], weaknesses=[], suggestions=[]),
        hookAnalysis=SectionAnalysis(score=85, strengths=["痛点直击"], weaknesses=[], suggestions=[]),
        bodyAnalysis=SectionAnalysis(score=80, strengths=["结构清晰"], weaknesses=[], suggestions=[]),
        ctaAnalysis=SectionAnalysis(score=78, strengths=["引导明确"], weaknesses=[], suggestions=[]),
        emojiAnalysis=SectionAnalysis(score=75, strengths=["适度"], weaknesses=[], suggestions=[]),
        emotionCurve=[
            EmotionNode(position=0.0, label="好奇", value=80.0),
            EmotionNode(position=0.3, label="共鸣", value=90.0),
            EmotionNode(position=0.7, label="紧迫感", value=75.0),
            EmotionNode(position=1.0, label="信任", value=85.0),
        ],
        successFactors=["痛点直击", "数据支撑", "互动引导"],
    )


def test_extract_strategy_elements_count():
    service = ViralAnalyzerService()
    report = _make_sample_report()

    elements = service.extract_strategy_elements(report, platform="xiaohongshu")

    assert len(elements) == 7
    element_types = {e["element_type"] for e in elements}
    assert "structure_framework" in element_types
    assert "hook_pattern" in element_types
    assert "body_structure" in element_types
    assert "cta_pattern" in element_types
    assert "keyword_strategy" in element_types
    assert "emotion_curve" in element_types
    assert "engagement_formula" in element_types


def test_extract_structure_framework():
    service = ViralAnalyzerService()
    report = _make_sample_report()

    elements = service.extract_strategy_elements(report, platform="xiaohongshu")
    structure = next(e for e in elements if e["element_type"] == "structure_framework")

    assert structure["element_subtype"] == "避坑排雷型"
    assert structure["content"]["structure_type"] == "避坑排雷型"
    assert "body_formula" in structure["content"]
    assert len(structure["variables"]) > 0
    assert "render_template" in structure


def test_extract_keyword_strategy():
    service = ViralAnalyzerService()
    report = _make_sample_report()

    elements = service.extract_strategy_elements(report, platform="xiaohongshu")
    keyword_elem = next(e for e in elements if e["element_type"] == "keyword_strategy")

    assert "新手养猫" in keyword_elem["content"]["primary_keywords"]
    assert "省钱" in keyword_elem["content"]["primary_keywords"]
    assert "避坑" in keyword_elem["content"]["secondary_keywords"]
    assert keyword_elem["content"]["density_target"] == 0.03


def test_extract_emotion_curve():
    service = ViralAnalyzerService()
    report = _make_sample_report()

    elements = service.extract_strategy_elements(report, platform="xiaohongshu")
    emotion_elem = next(e for e in elements if e["element_type"] == "emotion_curve")

    curve = emotion_elem["content"]["curve"]
    assert len(curve) == 4
    assert curve[0]["emotion"] == "好奇"
    assert curve[0]["intensity"] == 0.8
