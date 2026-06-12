"""
实验室 — 爆款笔记分析引擎（三层分析引擎）

架构：
  1. LLM 结构化分析（DeepSeek / 自定义配置）
  2. 规则校准（关键词库 + 结构定义）
  3. Template Converter（→ ContentTemplate）

职责：
  - analyze_note(input) -> AnalysisReport
  - generate_template(report) -> ViralTemplate
  - _call_analysis_llm(input) -> AnalysisReport（LLM 调用）
  - _calibrate_with_rules(report) -> AnalysisReport（规则校准）
  - _convert_to_content_template(viral_template) -> ContentTemplateORM
"""

from __future__ import annotations

import json
import logging
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from src.services.content_generator import call_llm
from src.core.database import get_db
from src.models.content_template import ContentTemplateORM as ContentTemplate

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════
# Pydantic Models
# ═══════════════════════════════════════════════════════

class NoteInput(BaseModel):
    """笔记输入"""
    title: str
    content: str
    coverImage: Optional[str] = None
    metrics: Optional[Dict[str, int]] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None


class KeywordMatch(BaseModel):
    """关键词匹配结果"""
    keyword: str
    dimension: str  # structure | function | emotion | industry | effect
    count: int
    weight: float


class SectionAnalysis(BaseModel):
    """段落分析"""
    score: float = Field(..., ge=0, le=100)
    strengths: List[str]
    weaknesses: List[str]
    suggestions: List[str]


class EmotionNode(BaseModel):
    """情绪曲线节点"""
    position: float  # 0-1 进度
    label: str
    value: float  # 0-100 强度


class ExtractedTemplate(BaseModel):
    """提取的模板结构"""
    name: str
    formula: str
    variables: List[str]
    description: Optional[str] = None


class AnalysisReport(BaseModel):
    """分析报告输出"""
    noteId: str
    structureType: str
    viralScore: float = Field(..., ge=0, le=100)
    keywordMatches: List[KeywordMatch]
    titleAnalysis: SectionAnalysis
    hookAnalysis: SectionAnalysis
    bodyAnalysis: SectionAnalysis
    ctaAnalysis: SectionAnalysis
    emojiAnalysis: SectionAnalysis
    emotionCurve: List[EmotionNode]
    successFactors: List[str]
    extractedTemplate: Optional[ExtractedTemplate] = None


class ViralTemplate(BaseModel):
    """爆款模板输出"""
    templateId: str
    name: str
    derivedFrom: str  # noteId
    category: Optional[str]
    structureType: str
    keywordFormulas: List[str]
    constraints: List[str]
    validationRules: List[str]
    meta: Dict[str, Any]


class ViralAnalyzerService:
    """三层分析引擎核心服务"""

    # ═══════════════════════════════════════════════════
    # Public API
    # ═══════════════════════════════════════════════════

    async def analyze_note(
        self,
        input_data: NoteInput,
        *,
        llm_config: Optional[Dict[str, Any]] = None,
        db=None,
    ) -> AnalysisReport:
        """三层分析：LLM → 规则校准 → 报告"""
        logger.info("[ViralAnalyzer] Starting analysis for title=%s", input_data.title[:30])

        # Step 1: LLM 结构化分析
        raw_report = await self._call_analysis_llm(input_data, llm_config=llm_config)

        # Step 2: 规则校准
        calibrated = await self._calibrate_with_rules(raw_report, input_data, db=db)

        logger.info("[ViralAnalyzer] Analysis complete — score=%.1f structure=%s",
                    calibrated.viralScore, calibrated.structureType)
        return calibrated

    async def generate_template(
        self,
        report: AnalysisReport,
        *,
        platform: str = "xiaohongshu",
        category: Optional[str] = None,
        llm_config: Optional[Dict[str, Any]] = None,
    ) -> ViralTemplate:
        """从分析报告生成爆款模板"""
        logger.info("[ViralAnalyzer] Generating template from noteId=%s", report.noteId)

        template_id = str(uuid.uuid4())[:8]

        # 构建模板公式
        formulas = self._build_formulas(report)
        constraints = self._build_constraints(report)
        validation_rules = self._build_validation_rules(report)

        # 可选：LLM 优化模板描述
        if llm_config is not False:
            optimized = await self._optimize_template_with_llm(report, formulas, llm_config=llm_config)
            if optimized:
                formulas = optimized.get("formulas", formulas)
                constraints = optimized.get("constraints", constraints)

        template = ViralTemplate(
            templateId=template_id,
            name=f"爆款{report.structureType}模板 #{template_id}",
            derivedFrom=report.noteId,
            category=category,
            structureType=report.structureType,
            keywordFormulas=formulas,
            constraints=constraints,
            validationRules=validation_rules,
            meta={
                "platform": platform,
                "viralScore": report.viralScore,
                "sourceStructure": report.structureType,
                "generatedAt": datetime.now(timezone.utc).isoformat(),
            },
        )

        logger.info("[ViralAnalyzer] Template generated — id=%s formulas=%d",
                    template.templateId, len(template.keywordFormulas))
        return template

    async def save_template(
        self,
        template: ViralTemplate,
        tenant_id: str = "default",
        created_by: str = "system",
        db=None,
    ) -> str:
        """将 ViralTemplate 保存到 content_templates 表"""
        orm = self._convert_to_content_template(template, tenant_id=tenant_id, created_by=created_by)

        if db is None:
            db = await anext(get_db())

        db.add(orm)
        await db.commit()
        await db.refresh(orm)

        logger.info("[ViralAnalyzer] Template saved to DB — id=%s", orm.id)
        return str(orm.id)

    # ═══════════════════════════════════════════════════
    # Step 1: LLM 结构化分析
    # ═══════════════════════════════════════════════════

    async def _call_analysis_llm(
        self,
        input_data: NoteInput,
        llm_config: Optional[Dict[str, Any]] = None,
    ) -> AnalysisReport:
        """调用 LLM 进行结构化分析"""

        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(input_data)

        try:
            raw = call_llm(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                llm_config=llm_config,
                max_tokens=3000,
            )
        except Exception as exc:
            logger.error("[ViralAnalyzer] LLM call failed: %s", exc)
            # Fallback: 返回基础分析
            return self._fallback_analysis(input_data)

        # 解析 JSON 响应
        try:
            # 尝试提取 JSON 块
            json_str = self._extract_json(raw)
            data = json.loads(json_str)
        except Exception as exc:
            logger.warning("[ViralAnalyzer] JSON parse failed, using regex fallback: %s", exc)
            data = self._parse_llm_text_fallback(raw, input_data)

        # 组装报告（带完整异常回退）
        try:
            note_id = str(uuid.uuid4())[:12]

            # 清洗 emotion_curve 数据（LLM 可能返回字符串 position）
            emotion_curve_raw = data.get("emotion_curve", [])
            emotion_curve = []
            for i, node in enumerate(emotion_curve_raw):
                pos = node.get("position", i * 0.25)
                if isinstance(pos, str):
                    # 尝试将中文标签映射为数字，或直接用索引
                    pos = min(i * 0.25, 1.0)
                val = node.get("value", 50)
                if isinstance(val, str):
                    try:
                        val = float(val)
                    except (ValueError, TypeError):
                        val = 50
                emotion_curve.append(EmotionNode(
                    position=float(pos),
                    label=node.get("label", f"节点{i}"),
                    value=float(val),
                ))
            if not emotion_curve:
                emotion_curve = self._default_emotion_curve()

            # 清洗 successFactors（确保是字符串列表）
            success_factors = data.get("success_factors", [])
            if not isinstance(success_factors, list):
                success_factors = [str(success_factors)] if success_factors else []
            else:
                success_factors = [str(sf) for sf in success_factors if sf]

            report = AnalysisReport(
                noteId=note_id,
                structureType=str(data.get("structure_type", "种草测评型")),
                viralScore=float(data.get("viral_score", 70.0)),
                keywordMatches=[
                    KeywordMatch(**km) for km in data.get("keyword_matches", [])
                    if isinstance(km, dict) and "keyword" in km
                ],
                titleAnalysis=SectionAnalysis(**data.get("title_analysis", {
                    "score": 70, "strengths": [], "weaknesses": [], "suggestions": []
                })),
                hookAnalysis=SectionAnalysis(**data.get("hook_analysis", {
                    "score": 70, "strengths": [], "weaknesses": [], "suggestions": []
                })),
                bodyAnalysis=SectionAnalysis(**data.get("body_analysis", {
                    "score": 70, "strengths": [], "weaknesses": [], "suggestions": []
                })),
                ctaAnalysis=SectionAnalysis(**data.get("cta_analysis", {
                    "score": 70, "strengths": [], "weaknesses": [], "suggestions": []
                })),
                emojiAnalysis=SectionAnalysis(**data.get("emoji_analysis", {
                    "score": 70, "strengths": [], "weaknesses": [], "suggestions": []
                })),
                emotionCurve=emotion_curve,
                successFactors=success_factors,
                extractedTemplate=ExtractedTemplate(**data["extracted_template"])
                if data.get("extracted_template") and isinstance(data["extracted_template"], dict) else None,
            )
            return report
        except Exception as exc:
            logger.error("[ViralAnalyzer] Report assembly failed, using fallback: %s", exc)
            return self._fallback_analysis(input_data)

    # ═══════════════════════════════════════════════════
    # Step 2: 规则校准
    # ═══════════════════════════════════════════════════

    async def _calibrate_with_rules(
        self,
        report: AnalysisReport,
        input_data: NoteInput,
        db=None,
    ) -> AnalysisReport:
        """基于规则库校准 LLM 输出"""

        text = f"{input_data.title}\n{input_data.content}"
        calibrated = report.model_copy(deep=True)

        # 1. 关键词权重校准
        if db is not None:
            try:
                keyword_matches = await self._match_keywords_db(text, db)
            except Exception:
                keyword_matches = self._match_keywords_rules(text)
        else:
            keyword_matches = self._match_keywords_rules(text)

        # 合并 LLM 和规则匹配的关键词
        existing_keywords = {km.keyword for km in calibrated.keywordMatches}
        for km in keyword_matches:
            if km.keyword not in existing_keywords:
                calibrated.keywordMatches.append(km)

        # 2. 关键词覆盖度校准 viralScore
        keyword_bonus = min(len(calibrated.keywordMatches) * 2, 10)
        calibrated.viralScore = min(calibrated.viralScore + keyword_bonus, 100)

        # 3. 结构类型校准（简单规则）
        structure_scores = self._score_structures(text)
        best_structure = max(structure_scores, key=structure_scores.get)
        if structure_scores[best_structure] > structure_scores.get(calibrated.structureType, 0) + 3:
            calibrated.structureType = best_structure

        # 4. 互动数据加权
        if input_data.metrics:
            likes = input_data.metrics.get("likes", 0)
            if likes > 1000:
                calibrated.viralScore = min(calibrated.viralScore + 5, 100)
            elif likes < 50:
                calibrated.viralScore = max(calibrated.viralScore - 5, 0)

        return calibrated

    # ═══════════════════════════════════════════════════
    # Step 3: Template Converter
    # ═══════════════════════════════════════════════════

    def _convert_to_content_template(
        self,
        template: ViralTemplate,
        tenant_id: str = "default",
        created_by: str = "system",
    ) -> ContentTemplate:
        """ViralTemplate -> ContentTemplate ORM"""
        variables = self._extract_variables(template.keywordFormulas)

        return ContentTemplate(
            template_id=f"tmpl_{template.templateId}",
            tenant_id=tenant_id,
            source_platform_id=template.meta.get("platform", "xiaohongshu"),
            source_content_url=None,
            source_content_id=template.derivedFrom,
            source="viral_analyzer",
            analysis_report=None,
            extracted_structure={
                "structure_type": template.structureType,
                "keyword_formulas": template.keywordFormulas,
            },
            prompt_template="\n".join(template.keywordFormulas),
            variables=variables,
            engagement_benchmark=None,
            platform_content_type_style_id=None,
            created_by=created_by,
            usage_count=0,
            avg_generated_engagement=None,
            status="active",
        )

    # ═══════════════════════════════════════════════════
    # Helper: Prompt Builders
    # ═══════════════════════════════════════════════════

    def _build_system_prompt(self) -> str:
        return """你是一位小红书爆款内容分析专家。请分析用户提供的笔记内容，输出严格 JSON 格式。

## 分析维度

1. **structure_type**: 结构类型（种草测评型/干货合集型/避坑排雷型/教程攻略型/对比测评型/个人故事型）
2. **viral_score**: 爆款潜力评分 0-100
3. **keyword_matches**: 关键词匹配列表 [{keyword, dimension, count, weight}]
   - dimension 可选: structure, function, emotion, industry, effect
4. **title_analysis**: 标题分析 {score, strengths[], weaknesses[], suggestions[]}
5. **hook_analysis**: 开头分析 {score, strengths[], weaknesses[], suggestions[]}
6. **body_analysis**: 正文分析 {score, strengths[], weaknesses[], suggestions[]}
7. **cta_analysis**: 结尾/CTA分析 {score, strengths[], weaknesses[], suggestions[]}
8. **emoji_analysis**: Emoji使用分析 {score, strengths[], weaknesses[], suggestions[]}
9. **emotion_curve**: 情绪曲线 [{position, label, value}]
10. **success_factors**: Top3 成功因子 ["...", "...", "..."]
11. **extracted_template**: 提取的模板 {name, formula, variables[], description}

## 输出要求
- 仅输出 JSON，不要 markdown 代码块
- 所有字段必须存在，不能为空
- score 范围 0-100
- value 范围 0-100"""

    def _build_user_prompt(self, input_data: NoteInput) -> str:
        metrics_str = ""
        if input_data.metrics:
            parts = []
            for k, v in input_data.metrics.items():
                parts.append(f"{k}: {v}")
            metrics_str = f"\n互动数据: {', '.join(parts)}"

        tags_str = f"\n标签: {', '.join(input_data.tags)}" if input_data.tags else ""
        category_str = f"\n分类: {input_data.category}" if input_data.category else ""

        return f"""请分析以下笔记内容：

标题: {input_data.title}
正文: {input_data.content}{category_str}{tags_str}{metrics_str}

请输出 JSON 分析结果。"""

    # ═══════════════════════════════════════════════════
    # Helper: Fallback & Parsing
    # ═══════════════════════════════════════════════════

    def _fallback_analysis(self, input_data: NoteInput) -> AnalysisReport:
        """LLM 失败时的降级分析"""
        return AnalysisReport(
            noteId=str(uuid.uuid4())[:12],
            structureType="种草测评型",
            viralScore=60.0,
            keywordMatches=self._match_keywords_rules(f"{input_data.title}\n{input_data.content}"),
            titleAnalysis=SectionAnalysis(
                score=60, strengths=["有标题"], weaknesses=["未深入分析"], suggestions=["优化标题吸引力"]
            ),
            hookAnalysis=SectionAnalysis(
                score=60, strengths=[], weaknesses=["未深入分析"], suggestions=["开头增加钩子"]
            ),
            bodyAnalysis=SectionAnalysis(
                score=60, strengths=[], weaknesses=["未深入分析"], suggestions=["丰富正文内容"]
            ),
            ctaAnalysis=SectionAnalysis(
                score=60, strengths=[], weaknesses=["未深入分析"], suggestions=["增加行动号召"]
            ),
            emojiAnalysis=SectionAnalysis(
                score=60, strengths=[], weaknesses=["未深入分析"], suggestions=["适当使用 emoji"]
            ),
            emotionCurve=self._default_emotion_curve(),
            successFactors=["内容完整", "有互动数据", "结构清晰"],
            extractedTemplate=None,
        )

    def _extract_json(self, text: str) -> str:
        """从 LLM 响应中提取 JSON"""
        # 尝试 markdown 代码块
        match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
        if match:
            return match.group(1).strip()
        # 尝试直接 JSON
        match = re.search(r'\{[\s\S]*\}', text)
        if match:
            return match.group(0).strip()
        return text.strip()

    def _parse_llm_text_fallback(self, text: str, input_data: NoteInput) -> Dict[str, Any]:
        """文本解析降级"""
        structure_type = "种草测评型"
        for st in ["避坑", "排雷"]:
            if st in input_data.title:
                structure_type = "避坑排雷型"
                break
        for st in ["教程", "攻略"]:
            if st in input_data.title:
                structure_type = "教程攻略型"
                break

        viral_score = 65.0
        try:
            if "评分" in text or "score" in text.lower():
                nums = re.findall(r'(\d{2,3})\s*分', text)
                if nums:
                    viral_score = float(nums[0])
        except Exception:
            pass

        return {
            "structure_type": structure_type,
            "viral_score": viral_score,
            "keyword_matches": [],
            "title_analysis": {"score": 60, "strengths": [], "weaknesses": [], "suggestions": []},
            "hook_analysis": {"score": 60, "strengths": [], "weaknesses": [], "suggestions": []},
            "body_analysis": {"score": 60, "strengths": [], "weaknesses": [], "suggestions": []},
            "cta_analysis": {"score": 60, "strengths": [], "weaknesses": [], "suggestions": []},
            "emoji_analysis": {"score": 60, "strengths": [], "weaknesses": [], "suggestions": []},
            "emotion_curve": [],
            "success_factors": [],
            "extracted_template": None,
        }

    def _default_emotion_curve(self) -> List[EmotionNode]:
        return [
            EmotionNode(position=0.0, label="开头", value=50),
            EmotionNode(position=0.25, label="引入", value=60),
            EmotionNode(position=0.5, label="核心", value=70),
            EmotionNode(position=0.75, label="高潮", value=65),
            EmotionNode(position=1.0, label="结尾", value=55),
        ]

    # ═══════════════════════════════════════════════════
    # Helper: Keyword Matching
    # ═══════════════════════════════════════════════════

    def _match_keywords_rules(self, text: str) -> List[KeywordMatch]:
        """基于规则的关键词匹配（MVP ~30 关键词）"""
        keyword_rules = [
            # (keyword, dimension, weight, structures)
            ("避坑", "structure", 1.2, ["避坑排雷型"]),
            ("误区", "structure", 1.1, ["避坑排雷型"]),
            ("种草", "structure", 1.2, ["种草测评型"]),
            ("测评", "structure", 1.1, ["种草测评型", "对比测评型"]),
            ("教程", "structure", 1.1, ["教程攻略型"]),
            ("攻略", "structure", 1.1, ["教程攻略型"]),
            ("合集", "structure", 1.1, ["干货合集型"]),
            ("故事", "structure", 1.0, ["个人故事型"]),
            ("指南", "function", 1.0, ["避坑排雷型", "教程攻略型"]),
            ("推荐", "function", 1.0, ["种草测评型"]),
            ("分享", "function", 0.9, []),
            ("必看", "function", 1.0, []),
            ("干货", "function", 1.0, ["干货合集型"]),
            ("焦虑", "emotion", 0.9, ["避坑排雷型"]),
            ("惊喜", "emotion", 0.9, ["种草测评型"]),
            ("共鸣", "emotion", 0.9, ["个人故事型"]),
            ("信任", "emotion", 0.8, ["教程攻略型"]),
            ("愤怒", "emotion", 0.9, ["避坑排雷型"]),
            ("向往", "emotion", 0.8, ["种草测评型"]),
            ("驱虫", "industry", 1.5, ["避坑排雷型", "种草测评型"]),
            ("猫粮", "industry", 1.3, ["种草测评型", "对比测评型"]),
            ("疫苗", "industry", 1.3, ["教程攻略型"]),
            ("铲屎官", "industry", 1.0, []),
            ("养猫", "industry", 1.2, []),
            ("狗狗", "industry", 1.2, []),
            ("省钱", "effect", 1.1, ["避坑排雷型", "种草测评型"]),
            ("有效", "effect", 1.0, ["种草测评型"]),
            ("快速", "effect", 0.9, ["教程攻略型"]),
            ("简单", "effect", 0.9, ["教程攻略型"]),
            ("真实", "effect", 1.0, ["个人故事型"]),
        ]

        results = []
        for keyword, dimension, weight, structures in keyword_rules:
            count = len(re.findall(re.escape(keyword), text))
            if count > 0:
                results.append(KeywordMatch(
                    keyword=keyword,
                    dimension=dimension,
                    count=count,
                    weight=weight,
                ))
        return results

    async def _match_keywords_db(self, text: str, db) -> List[KeywordMatch]:
        """从数据库关键词库匹配（预留接口）"""
        # TODO: 查询 keyword_library 表
        return self._match_keywords_rules(text)

    # ═══════════════════════════════════════════════════
    # Helper: Structure Scoring
    # ═══════════════════════════════════════════════════

    def _score_structures(self, text: str) -> Dict[str, int]:
        """基于关键词匹配评分结构类型"""
        structure_keywords = {
            "种草测评型": ["种草", "测评", "推荐", "亲测", "好用", "必入"],
            "干货合集型": ["合集", "干货", "盘点", "总结", "攻略", "大全"],
            "避坑排雷型": ["避坑", "排雷", "误区", "千万别", "错误", "注意"],
            "教程攻略型": ["教程", "攻略", "步骤", "手把手", "怎么做", "方法"],
            "对比测评型": ["对比", "测评", "vs", "哪个好", "区别", "优劣"],
            "个人故事型": ["故事", "经历", "我记得", "当时", "感动", "真实"],
        }

        scores = {}
        for structure_type, keywords in structure_keywords.items():
            score = sum(1 for kw in keywords if kw in text)
            scores[structure_type] = score
        return scores

    # ═══════════════════════════════════════════════════
    # Helper: Template Builders
    # ═══════════════════════════════════════════════════

    def _build_formulas(self, report: AnalysisReport) -> List[str]:
        """从分析报告构建模板公式"""
        formulas = []

        # 标题公式
        title_formula = self._infer_title_formula(report.titleAnalysis)
        formulas.append(f"标题: {title_formula}")

        # 开头公式
        hook_formula = self._infer_hook_formula(report.hookAnalysis)
        formulas.append(f"开头: {hook_formula}")

        # 正文公式
        body_formula = self._infer_body_formula(report.structureType)
        formulas.append(f"正文: {body_formula}")

        # 结尾公式
        cta_formula = self._infer_cta_formula(report.ctaAnalysis)
        formulas.append(f"结尾: {cta_formula}")

        # Emoji 公式
        if report.emojiAnalysis.score > 70:
            formulas.append("emoji: {主要情绪emoji} {辅助说明emoji}")

        return formulas

    def _infer_title_formula(self, title_analysis: SectionAnalysis) -> str:
        """推断标题公式"""
        if title_analysis.score >= 80:
            return "{痛点/好奇词} + {数字/对比} + {核心关键词}"
        elif title_analysis.score >= 60:
            return "{场景词} + {核心关键词} + {效果词}"
        return "{核心关键词} + {价值主张}"

    def _infer_hook_formula(self, hook_analysis: SectionAnalysis) -> str:
        """推断开头公式"""
        if hook_analysis.score >= 80:
            return "{痛点共鸣} + {数字/权威背书} + {核心承诺}"
        return "{场景引入} + {问题提出}"

    def _infer_body_formula(self, structure_type: str) -> str:
        """根据结构类型推断正文公式"""
        formulas = {
            "种草测评型": "{使用场景} → {痛点描述} → {产品介绍} → {使用体验} → {效果对比}",
            "干货合集型": "{总起句} → {要点1} → {要点2} → {要点3} → {总结} → {行动号召}",
            "避坑排雷型": "{常见误区} → {错误做法} → {正确方案} → {对比效果} → {注意事项}",
            "教程攻略型": "{目标说明} → {步骤1} → {步骤2} → {步骤3} → {常见问题} → {总结}",
            "对比测评型": "{测评对象} → {维度1对比} → {维度2对比} → {总结推荐} → {适用人群}",
            "个人故事型": "{背景设定} → {冲突/转折} → {过程描述} → {情感升华} → {收获总结}",
        }
        return formulas.get(structure_type, "{引入} → {展开} → {总结}")

    def _infer_cta_formula(self, cta_analysis: SectionAnalysis) -> str:
        """推断结尾公式"""
        if cta_analysis.score >= 80:
            return "{总结价值} + {互动提问} + {关注引导}"
        return "{总结} + {互动引导}"

    def _build_constraints(self, report: AnalysisReport) -> List[str]:
        """构建约束条件"""
        constraints = [
            f"结构类型必须为: {report.structureType}",
            "标题字数控制在 20 字以内",
            "正文段落数建议 5-8 段",
        ]

        if report.emojiAnalysis.score > 70:
            constraints.append("每段使用 1-2 个 emoji 增强情感表达")
        else:
            constraints.append("适度使用 emoji（每 100 字 1-2 个）")

        if report.viralScore >= 80:
            constraints.append("保持高爆款评分标准（≥80分）")

        return constraints

    def _build_validation_rules(self, report: AnalysisReport) -> List[str]:
        """构建验证规则"""
        return [
            "标题必须包含至少 1 个核心关键词",
            "开头前 30 字必须出现痛点或钩子",
            "正文必须包含至少 1 个数据/案例支撑",
            "结尾必须包含互动引导",
            "emoji 使用不可超过正文 5%",
        ]

    async def _optimize_template_with_llm(
        self,
        report: AnalysisReport,
        formulas: List[str],
        llm_config: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, List[str]]]:
        """可选：LLM 优化模板描述"""
        # MVP 阶段暂不启用，预留接口
        return None

    def _extract_variables(self, formulas: List[str]) -> List[str]:
        """从公式中提取变量名"""
        variables = set()
        for formula in formulas:
            matches = re.findall(r'\{(.*?)\}', formula)
            for match in matches:
                # 清理描述性文字，只保留核心变量名
                var = match.split('/')[0].strip()
                variables.add(var)
        return sorted(list(variables))

    # ═══════════════════════════════════════════════════
    # Strategy Element Extraction (v4.0)
    # ═══════════════════════════════════════════════════

    def extract_strategy_elements(
        self,
        report: AnalysisReport,
        platform: str = "xiaohongshu",
    ) -> List[Dict[str, Any]]:
        """从分析报告提取多个独立的策略元素（替代生成单个 Template）.

        Returns:
            List[Dict]: 每个 dict 可直接用于创建 StrategyElementORM
        """
        return [
            self._extract_structure_framework(report, platform),
            self._extract_hook_pattern(report, platform),
            self._extract_body_structure(report, platform),
            self._extract_cta_pattern(report, platform),
            self._extract_keyword_strategy(report, platform),
            self._extract_emotion_curve(report, platform),
            self._extract_engagement_formula(report, platform),
        ]

    def _generate_element_id(self) -> str:
        import secrets
        return f"elem_{secrets.token_hex(6)}"

    def _make_template_variables(self, raw_vars: List[str]) -> List[Dict[str, str]]:
        """将原始变量名列表转换为 TemplateVariable 格式."""
        return [
            {"name": var, "label": var, "type": "text", "default_value": ""}
            for var in raw_vars
        ]

    def _extract_structure_framework(self, report: AnalysisReport, platform: str) -> Dict[str, Any]:
        body_formula = self._infer_body_formula(report.structureType)
        raw_vars = self._extract_variables([body_formula])

        return {
            "element_id": self._generate_element_id(),
            "element_type": "structure_framework",
            "element_subtype": report.structureType,
            "name": f"结构框架：{report.structureType}",
            "description": f"从 viral_score={report.viralScore} 的爆款笔记提取的 {report.structureType} 结构框架",
            "content": {
                "structure_type": report.structureType,
                "sections": [
                    {"type": "hook", "description": "痛点引入/好奇钩子", "word_count": 50},
                    {"type": "body", "description": "正文展开", "word_count": 400},
                    {"type": "cta", "description": "互动引导", "word_count": 50},
                ],
                "body_formula": body_formula,
                "rationale": f"该结构类型来自爆款评分 {report.viralScore} 的笔记分析",
            },
            "render_template": """【内容结构框架】
结构类型：{{ structure_type }}
段落安排：
{% for section in sections %}- {{ section.type }}: {{ section.description }}（建议 {{ section.word_count }} 字）
{% endfor %}
正文公式：{{ body_formula }}
{% if rationale %}说明：{{ rationale }}{% endif %}""",
            "variables": self._make_template_variables(raw_vars),
            "source": "viral_analyzer",
            "source_content_id": report.noteId,
            "platform": platform,
        }

    def _extract_hook_pattern(self, report: AnalysisReport, platform: str) -> Dict[str, Any]:
        hook_formula = self._infer_hook_formula(report.hookAnalysis)
        title_formula = self._infer_title_formula(report.titleAnalysis)
        raw_vars = self._extract_variables([hook_formula, title_formula])

        return {
            "element_id": self._generate_element_id(),
            "element_type": "hook_pattern",
            "element_subtype": "痛点共鸣型" if report.hookAnalysis.score >= 80 else "场景引入型",
            "name": f"Hook 模式：{report.structureType}",
            "description": f"标题得分 {report.titleAnalysis.score}，开头得分 {report.hookAnalysis.score}",
            "content": {
                "title_formula": title_formula,
                "hook_formula": hook_formula,
                "title_score": report.titleAnalysis.score,
                "hook_score": report.hookAnalysis.score,
                "examples": [report.noteId],
                "rationale": f"Hook 模式来自 viral_score={report.viralScore} 的爆款笔记",
            },
            "render_template": """【开头 Hook 要求】
标题公式：{{ title_formula }}
首段公式：{{ hook_formula }}
{% if examples %}来源笔记：{% for ex in examples %}{{ ex }}{% endfor %}{% endif %}
{% if rationale %}说明：{{ rationale }}{% endif %}""",
            "variables": self._make_template_variables(raw_vars),
            "source": "viral_analyzer",
            "source_content_id": report.noteId,
            "platform": platform,
        }

    def _extract_body_structure(self, report: AnalysisReport, platform: str) -> Dict[str, Any]:
        body_formula = self._infer_body_formula(report.structureType)
        raw_vars = self._extract_variables([body_formula])

        return {
            "element_id": self._generate_element_id(),
            "element_type": "body_structure",
            "element_subtype": report.structureType,
            "name": f"正文结构：{report.structureType}",
            "description": f"正文得分 {report.bodyAnalysis.score}",
            "content": {
                "structure_type": report.structureType,
                "body_formula": body_formula,
                "body_score": report.bodyAnalysis.score,
                "strengths": report.bodyAnalysis.strengths,
                "rationale": "爆款笔记的正文组织方式",
            },
            "render_template": """【正文结构要求】
结构类型：{{ structure_type }}
段落公式：{{ body_formula }}
{% if strengths %}优势特征：
{% for s in strengths %}- {{ s }}
{% endfor %}{% endif %}
{% if rationale %}说明：{{ rationale }}{% endif %}""",
            "variables": self._make_template_variables(raw_vars),
            "source": "viral_analyzer",
            "source_content_id": report.noteId,
            "platform": platform,
        }

    def _extract_cta_pattern(self, report: AnalysisReport, platform: str) -> Dict[str, Any]:
        cta_formula = self._infer_cta_formula(report.ctaAnalysis)
        raw_vars = self._extract_variables([cta_formula])

        return {
            "element_id": self._generate_element_id(),
            "element_type": "cta_pattern",
            "element_subtype": "强引导型" if report.ctaAnalysis.score >= 80 else "温和引导型",
            "name": f"CTA 模式：{report.structureType}",
            "description": f"结尾/CTA 得分 {report.ctaAnalysis.score}",
            "content": {
                "cta_formula": cta_formula,
                "cta_score": report.ctaAnalysis.score,
                "rationale": f"来自 viral_score={report.viralScore} 的爆款笔记结尾模式",
            },
            "render_template": """【结尾 CTA 要求】
结尾公式：{{ cta_formula }}
{% if rationale %}说明：{{ rationale }}{% endif %}""",
            "variables": self._make_template_variables(raw_vars),
            "source": "viral_analyzer",
            "source_content_id": report.noteId,
            "platform": platform,
        }

    def _extract_keyword_strategy(self, report: AnalysisReport, platform: str) -> Dict[str, Any]:
        primary_keywords = [km.keyword for km in report.keywordMatches if km.dimension in ("industry", "effect")][:5]
        secondary_keywords = [km.keyword for km in report.keywordMatches if km.dimension in ("structure", "function")][:5]
        emotion_keywords = [km.keyword for km in report.keywordMatches if km.dimension == "emotion"][:3]

        return {
            "element_id": self._generate_element_id(),
            "element_type": "keyword_strategy",
            "element_subtype": "爆款关键词组合",
            "name": f"关键词策略：{report.structureType}",
            "description": f"从笔记中提取 {len(report.keywordMatches)} 个关键词匹配",
            "content": {
                "primary_keywords": primary_keywords,
                "secondary_keywords": secondary_keywords,
                "emotion_keywords": emotion_keywords,
                "density_target": 0.03,
                "placement_rules": [
                    "标题必须包含至少 1 个核心关键词",
                    "正文前 100 字出现 2 个关键词",
                    "标签使用 3-5 个辅助关键词",
                ],
                "rationale": f"基于 keyword_library 匹配结果和结构类型 {report.structureType}",
            },
            "render_template": """【关键词策略】
核心关键词：{{ primary_keywords | join(', ') }}
辅助关键词：{{ secondary_keywords | join(', ') }}
情感关键词：{{ emotion_keywords | join(', ') }}
目标密度：{{ density_target * 100 }}%
放置规则：
{% for rule in placement_rules %}- {{ rule }}
{% endfor %}
{% if rationale %}说明：{{ rationale }}{% endif %}""",
            "variables": [],
            "source": "viral_analyzer",
            "source_content_id": report.noteId,
            "platform": platform,
        }

    def _extract_emotion_curve(self, report: AnalysisReport, platform: str) -> Dict[str, Any]:
        curve_data = [
            {
                "position": node.position,
                "emotion": node.label,
                "intensity": node.value / 100.0,
                "label": node.label,
            }
            for node in report.emotionCurve
        ]

        return {
            "element_id": self._generate_element_id(),
            "element_type": "emotion_curve",
            "element_subtype": "爆款情感曲线",
            "name": f"情感曲线：{report.structureType}",
            "description": f"从笔记情绪分析提取的情感波动策略",
            "content": {
                "curve": curve_data,
                "rationale": f"情感曲线来自 viral_score={report.viralScore} 的爆款笔记",
            },
            "render_template": """【情感曲线要求】
创作时请按以下情感节奏组织内容：
{% for point in curve %}- {{ '%.0f' | format(point.position * 100) }}% 处：{{ point.emotion }}（强度 {{ '%.0f' | format(point.intensity * 100) }}%）
{% endfor %}
{% if rationale %}说明：{{ rationale }}{% endif %}""",
            "variables": [],
            "source": "viral_analyzer",
            "source_content_id": report.noteId,
            "platform": platform,
        }

    def _extract_engagement_formula(self, report: AnalysisReport, platform: str) -> Dict[str, Any]:
        emoji_density = "每段使用 1-2 个 emoji" if report.emojiAnalysis.score > 70 else "适度使用 emoji（每 100 字 1-2 个）"
        success_factors = report.successFactors[:3]

        return {
            "element_id": self._generate_element_id(),
            "element_type": "engagement_formula",
            "element_subtype": "互动公式",
            "name": f"互动公式：{report.structureType}",
            "description": f"Emoji 得分 {report.emojiAnalysis.score}，成功因子 {len(success_factors)} 条",
            "content": {
                "emoji_density": emoji_density,
                "sentence_rhythm": "短句为主（15-20 字），穿插 1-2 个长句",
                "interaction_hooks": ["你有没有遇到过类似情况？", "评论区告诉我", "点赞收藏不迷路"],
                "visual_cues": ["分段使用 emoji 小标题", "关键数据加粗"],
                "success_factors": success_factors,
                "rationale": f"互动策略来自 viral_score={report.viralScore} 的爆款笔记",
            },
            "render_template": """【互动公式要求】
Emoji 密度：{{ emoji_density }}
句式节奏：{{ sentence_rhythm }}
互动钩子：
{% for hook in interaction_hooks %}- {{ hook }}
{% endfor %}
视觉提示：
{% for cue in visual_cues %}- {{ cue }}
{% endfor %}
{% if success_factors %}成功因子：
{% for factor in success_factors %}- {{ factor }}
{% endfor %}{% endif %}
{% if rationale %}说明：{{ rationale }}{% endif %}""",
            "variables": [],
            "source": "viral_analyzer",
            "source_content_id": report.noteId,
            "platform": platform,
        }

    async def save_strategy_elements(
        self,
        elements: List[Dict[str, Any]],
        tenant_id: str = "default",
        created_by: str = "system",
        db=None,
    ) -> List[str]:
        """批量保存策略元素到元素库."""
        from src.models.strategy_element import StrategyElementORM
        from src.core.database import get_db

        if db is None:
            db = await anext(get_db())

        saved_ids = []
        for elem in elements:
            orm = StrategyElementORM(
                element_id=elem["element_id"],
                tenant_id=tenant_id,
                element_type=elem["element_type"],
                element_subtype=elem.get("element_subtype"),
                name=elem["name"],
                description=elem.get("description"),
                content=elem["content"],
                render_template=elem["render_template"],
                variables=elem.get("variables", []),
                source=elem.get("source", "viral_analyzer"),
                source_content_id=elem.get("source_content_id"),
                platform=elem.get("platform"),
                methodology_stage_id=elem.get("methodology_stage_id"),
                created_by=created_by,
            )
            db.add(orm)
            saved_ids.append(elem["element_id"])

        await db.commit()
        logger.info("[ViralAnalyzer] Saved %d strategy elements", len(saved_ids))
        return saved_ids

    async def save_as_strategy_set(
        self,
        elements: List[Dict[str, Any]],
        name: str,
        tenant_id: str = "default",
        created_by: str = "system",
        platform: Optional[str] = None,
        db=None,
    ) -> str:
        """将一组策略元素保存为可复用的策略组合（StrategySet）."""
        from src.models.strategy_set import StrategySetORM
        from src.core.database import get_db

        if db is None:
            db = await anext(get_db())

        set_id = f"set_{uuid.uuid4().hex[:8]}"
        strategy_set = StrategySetORM(
            set_id=set_id,
            tenant_id=tenant_id,
            name=name,
            element_refs=[
                {"element_id": e["element_id"], "priority": 50, "override_variables": {}}
                for e in elements
            ],
            default_variables={},
            source="viral_analyzer",
            source_content_id=elements[0].get("source_content_id") if elements else None,
            platform=platform or (elements[0].get("platform") if elements else None),
            created_by=created_by,
        )
        db.add(strategy_set)
        await db.commit()
        await db.refresh(strategy_set)

        logger.info("[ViralAnalyzer] Saved strategy set %s with %d elements", set_id, len(elements))
        return set_id


# ═══════════════════════════════════════════════════════
# Singleton
# ═══════════════════════════════════════════════════════

_viral_analyzer_service: Optional[ViralAnalyzerService] = None


def get_viral_analyzer_service() -> ViralAnalyzerService:
    """获取分析引擎单例"""
    global _viral_analyzer_service
    if _viral_analyzer_service is None:
        _viral_analyzer_service = ViralAnalyzerService()
    return _viral_analyzer_service
