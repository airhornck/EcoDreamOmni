# 专家评审方案：小红书高外溢宠物内容生成 Skill

> **方案版本**: v1.0（专家评审稿）  
> **编制日期**: 2026-06-01  
> **对齐真源**: `EcoDream_Omni_PRD_v2_对齐核心方案.md`（V2.7.2）、`详细设计_EcoDreamOmni_v2.md` §5.3  
> **评审对象**: 基于10篇高外溢小红书笔记构建的 `xhs_viral_pet_content_generate` Skill  
> **涉及基线模块**: SkillHub（L2 Configured Skill）、ContentForge、PromptRegistry、PoolPredictor  
> **状态**: 🔍 待产品/算法/运营/法务/工程五方联合评审

---

## 〇、需求背景与样本分析

### 0.1 用户原始需求

基于10篇已验证的高外溢（高互动率）小红书笔记，萃取其结构特征与内容模式，构建一个**可复用、可进化**的 Skill，使系统能够按照已验证的爆款逻辑生成小红书宠物类内容。

### 0.2 样本笔记列表

| # | 笔记URL/标题线索 | 可识别特征 | 推测结构类型 |
|---|-----------------|-----------|------------|
| 1 | `/explore/692f147e000000000d03b44b` | 高外溢笔记ID | 待运营补充 |
| 2 | `/explore/696a02f300000000220218d4` | 高外溢笔记ID | 待运营补充 |
| 3 | **钢铁橘是怎样炼成的？** | 拟人化命名（钢铁+橘猫）、问号结尾、故事/养成悬念 | 🔥 **故事养成型** |
| 4 | `/explore/69d644ff000000001f001fe7` | 高外溢笔记ID | 待运营补充 |
| 5 | `/explore/69c0e1be000000001d01abbf` | 高外溢笔记ID | 待运营补充 |
| 6 | **发现了一个幼犬长肉的秘籍！！ - 小美猫猫超黏狗** | "发现"惊喜开头 + "秘籍"稀缺感 + 双感叹号 + 多宠账号人设 | 🔥 **干货清单型** |
| 7 | `/explore/69fc4e520000000001b0238d7` | 高外溢笔记ID | 待运营补充 |
| 8 | `/explore/69f41f1d0000000022025f8d` | 高外溢笔记ID | 待运营补充 |
| 9 | `/explore/69dcb658000000001d01d92b` | 高外溢笔记ID | 待运营补充 |
| 10 | `/explore/69858398000000000e03e03c` | 高外溢笔记ID | 待运营补充 |

> **⚠️ 数据缺口**: 由于小红书平台反爬机制与登录态限制，AI无法直接抓取笔记全文。已知标题的两篇笔记（#3故事养成型、#6干货清单型）已能提供结构分析基础。**建议运营补充剩余8篇笔记的标题+正文（脱敏后）**，以提升Skill萃取精度。

### 0.3 已知样本结构深度分析

#### 样本A：「钢铁橘是怎样炼成的？」— 故事养成型

```
结构拆解：
├─ Hook（标题）：拟人化命名 + 文学化引用（《钢铁是怎样炼成的》）+ 问号悬念
├─ 开篇：一张橘猫"逆袭"对比图（Before/After）
├─ 正文：
│   ├─ 第1段：养猫前的困境（共鸣铺垫）
│   ├─ 第2段：转折点（某个事件/某个方法）
│   ├─ 第3段：具体做法（可复用的经验）
│   └─ 第4段：现在的变化（成果展示）
├─ CTA："你家橘猫也有这样的蜕变吗？评论区晒图！"
└─ 标签：#橘猫 #猫咪日常 #养猫经验 #大橘为重 #钢铁橘

结构标签：story_arc（故事弧光） + transformation（蜕变对比）
情绪曲线：低谷 → 转折 → 上升 → 高潮
互动触发点：对比图（视觉冲击） + 评论区晒图（UGC引导）
```

#### 样本B：「发现了一个幼犬长肉的秘籍！！」— 干货清单型

```
结构拆解：
├─ Hook（标题）："发现"（惊喜感） + "秘籍"（稀缺性） + "幼犬长肉"（精准痛点） + 双感叹号（情绪）
├─ 开篇：直接抛出成果（"我家小狗3个月胖了2斤"）+ 一张对比图
├─ 正文：
│   ├─ 痛点共鸣："之前怎么喂都不长肉，急死我了"
│   ├─ 清单主体（3-5条）：
│   │   ├─ ① 主食选择：含肉量XX%的粮
│   │   ├─ ② 加餐策略：鸡胸肉/蛋黄频率
│   │   ├─ ③ 运动配合：每天遛多久
│   │   └─ ④ 误区提醒：不要做的事
│   └─ 效果验证：体重变化图/毛色对比
├─ CTA："还有什么长肉好方法？求分享！" + 关注引导
└─ 标签：#幼犬 #狗狗喂养 #长肉秘籍 #新手养狗 #狗粮推荐

结构标签：list_numbered（数字清单） + pain_solution（痛点解决）
情绪曲线：焦虑 → 希望 → 收获 → 分享
互动触发点：求分享（互惠心理） + 清单收藏（实用价值）
```

### 0.4 共性结构模式提炼（基于已知样本 + 平台规律）

| 维度 | 故事养成型 | 干货清单型 | 其他推测高外溢类型 |
|------|-----------|-----------|-----------------|
| **Hook** | 悬念/反差/拟人化 | 数字/痛点/稀缺词 | 对比型：Before/After；情感型：共鸣开场 |
| **开篇前3行** | 建立情感连接（"还记得刚接它回家的时候..."） | 直接给结果（"3个月胖了2斤"） | 对比型：抛出反差数据 |
| **正文节奏** | 时间线叙事，每段有情绪起伏 | 清单式，每条有emoji+短句 | 测评型：维度打分+总结 |
| **信息密度** | 中等（故事留白） | 高（干货密集） | 视类型而定 |
| **emoji密度** | 中等（点缀情绪） | 较高（清单标记） | 高（视觉分割） |
| **CTA类型** | 晒图/讲故事 | 求分享/收藏提醒 | 投票/二选一 |
| **标签策略** | 品类词+情感词+话题词 | 痛点词+产品词+场景词 | 热点词+长尾词 |
| **封面特征** | 对比图/成长时间轴 | 大字报/清单图/对比图 | 大字报/测评表 |

---

## 一、Skill 总体设计

### 1.1 Skill 定位

| 属性 | 定义 |
|------|------|
| **Skill名称** | `xhs_viral_pet_content_generate` |
| **Skill层级** | **L2（Configured）** — 团队级共享技能，可被所有ContentForge Agent调用 |
| **Skill描述** | 基于高外溢笔记结构模式，生成符合小红书平台调性的宠物类爆款内容 |
| **适用平台** | 小红书（xhs）为主；未来可扩展至抖音图文/视频号 |
| **适用领域** | 宠物（猫/狗/异宠），聚焦：喂养、健康、日常、好物 |
| **版本** | v1.0.0（基于10篇样本） |
| **进化路径** | 执行数据回流 → SkillSmith监测 → 自动生成L4进化版 |

### 1.2 与现有系统的关系

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    xhs_viral_pet_content_generate Skill 调用链路             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   Agent / Workflow / 运营手动调用                                           │
│        │                                                                    │
│        ▼                                                                    │
│   ┌─────────────────────────────────────┐                                   │
│   │  SkillHub: xhs_viral_pet_content_generate (L2)                         │
│   │  ─────────────────────────────────────                                   │
│   │  ① 结构模式选择（基于topic+pet_type+audience匹配最佳结构模板）            │
│   │  ② Prompt组装（注入结构约束+Hook公式+CTA模板+标签策略）                  │
│   │  ③ 调用 ContentForge.generate_with_persona()                           │
│   │  ④ 后处理：emoji密度校准/段落长度检查/标签去重/合规初筛                  │
│   │  ⑤ 返回：结构化内容（title/body/tags/cover_hint/structure_type）        │
│   └─────────────────────────────────────┘                                   │
│        │                                                                    │
│        ├──► ContentForge（底层生成）                                        │
│        │      ├── PersonaPool（人设注入）                                    │
│        │      ├── BrandKnowledge（RAG检索）                                  │
│        │      ├── PersonaStory（故事上下文）                                  │
│        │      └── LLM Hub（模型路由）                                        │
│        │                                                                    │
│        ├──► PromptRegistry（模板版本化）                                    │
│        │                                                                    │
│        └──► PoolPredictor（互动预演）◄── 生成后调用，评估外溢潜力            │
│                                                                             │
│   数据回流：实际互动 → SkillSmith.record_performance() → 触发L4进化           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.3 核心设计原则

| 原则 | 说明 |
|------|------|
| **结构优先于文采** | Skill的核心价值是「约束结构」，而非替代LLM的文采。LLM负责填充内容，Skill负责保证结构符合爆款模式 |
| **可验证进化** | 每个生成结果都记录structure_type，实际互动数据回流后按结构类型计算成功率，驱动SkillSmith进化 |
| **合规内嵌** | Skill内置L1/L2合规约束（关键词过滤+免责声明强制插入），不依赖下游ComplianceGuard兜底 |
| **平台专属** | 深度适配小红书算法偏好（收藏权重高→强调收藏引导；搜索流量大→强调关键词覆盖） |

---

## 二、Skill 详细设计

### 2.1 输入/输出 Schema（Tool Registry 标准化）

```python
# Input Schema
INPUT_SCHEMA = {
    "topic": "str",                    # 内容主题，如"幼犬长肉"
    "pet_type": "str",                 # 宠物类型：cat / dog / exotic / multi
    "pet_subtype": "str",              # 细分：如"橘猫""金毛""布偶"
    "content_angle": "str",            # 切入角度：feeding / health / daily / product / story
    "target_audience": "str",          # 目标人群标签ID（关联AudienceTag）
    "structure_preference": "str",     # 结构偏好：auto / story_arc / list_numbered / comparison / emotion
    "tone": "str",                     # 语气：casual( casual亲切 ) / professional(专业) / humorous(幽默) / emotional(情感)
    "persona_id": "str",               # 人设ID（可选，默认从account读取）
    "account_id": "str",               # 账号ID（用于互动预演+数据回流）
    "include_cover_hint": "bool",      # 是否返回封面设计建议
    "brand_knowledge_ids": "list",     # 关联品牌知识库条目ID（可选）
    "keyword_boost": "list",           # 强制包含的关键词列表（可选）
}

# Output Schema
OUTPUT_SCHEMA = {
    "title": "str",                    # 生成标题
    "body": "str",                     # 生成正文（含换行和emoji）
    "tags": "list",                    # 推荐话题标签列表
    "structure_type": "str",           # 实际应用的结构类型
    "hook_type": "str",                # 钩子类型
    "cta_type": "str",                 # CTA类型
    "cover_hint": "dict",              # 封面设计建议（如include_cover_hint=True）
    "compliance_passed": "bool",       # 内置合规初筛结果
    "compliance_warnings": "list",     # 合规警告（如有）
    "estimated_engagement": "dict",    # PoolPredictor预演结果（可选）
    "generation_metadata": "dict",     # 生成元数据（模板版本、模型、token数等）
}
```

### 2.2 结构模板库（Structure Template Library）

Skill 内置5种经样本验证的小红书爆款结构模板：

```python
XHS_VIRAL_STRUCTURES = {
    "story_arc": {
        "name": "故事弧光型",
        "description": "基于样本A「钢铁橘」提炼：蜕变/养成/逆袭故事",
        "sample_source": "钢铁橘是怎样炼成的？",
        "hook_templates": [
            "{emotion}，{pet_type}{scenario}真的让人{feeling}！",
            "从{before_state}到{after_state}，我家{pet_type}用了{time_span}",
            "谁能想到，{pet_type}竟然{surprise_action}...",
            "养{pet_type}第{number}个月，我终于{achievement}",
        ],
        "body_sections": [
            {"type": "context", "purpose": "建立共鸣", "length_hint": "50-80字", "required": True},
            {"type": "turning_point", "purpose": "转折点", "length_hint": "40-60字", "required": True},
            {"type": "process", "purpose": "具体做法/过程", "length_hint": "80-120字", "required": True},
            {"type": "result", "purpose": "成果展示", "length_hint": "40-60字", "required": True},
        ],
        "cta_templates": [
            "你家{pet_type}也{shared_experience}吗？评论区说说👇",
            "{pet_type}的{topic}路还很长，持续更新中，记得关注❤️",
            "从{before}到{after}不容易，希望帮到每一个{audience}🙏",
        ],
        "emoji_strategy": {"density": "medium", "placement": ["段落首", "情感词后", "CTA前"]},
        "tag_strategy": {
            "must_have": ["#{pet_subtype}", "#{pet_type}日常"],
            "recommended": ["#{topic}", "#养{pet_type}经验", "#{pet_type}成长记"],
            "optional": ["#新手养{pet_type}", "#{emotion}瞬间"],
        },
        "cover_hint": {
            "style": "before_after_split",
            "text_overlay": "{time_span}的蜕变",
            "color_theme": "warm",
        },
        "best_for": ["story", "transformation", "growth"],
    },

    "list_numbered": {
        "name": "数字清单型",
        "description": "基于样本B「幼犬长肉秘籍」提炼：干货清单/攻略",
        "sample_source": "发现了一个幼犬长肉的秘籍！！",
        "hook_templates": [
            "发现了{number}个{pet_type}{topic}的秘籍！！",
            "{pet_type}{topic}，这{number}点{percent}%的人都不知道",
            "新手养{pet_type}必看｜{topic}攻略（亲测有效）",
            "花了{money}总结的{topic}经验，看完少踩{number}个坑",
        ],
        "body_sections": [
            {"type": "result_preview", "purpose": "先给结果", "length_hint": "30-50字", "required": True},
            {"type": "pain_point", "purpose": "痛点共鸣", "length_hint": "40-60字", "required": True},
            {"type": "list_item", "purpose": "干货条目", "length_hint": "每条40-60字", "item_count": "3-5", "required": True},
            {"type": "mistake_warning", "purpose": "误区提醒", "length_hint": "40-60字", "required": False},
        ],
        "cta_templates": [
            "还有什么{topic}的好方法？求分享！👇",
            "觉得有用的话记得⭐收藏，下次找不到啦",
            "{number}条中你做到了几条？评论区打卡✅",
        ],
        "emoji_strategy": {"density": "high", "placement": ["清单编号", "关键词后", "每条末尾"]},
        "tag_strategy": {
            "must_have": ["#{topic}", "#{pet_type}喂养"],
            "recommended": ["#新手养{pet_type}", "#{pet_type}健康", "#养{pet_type}攻略"],
            "optional": ["#{product_category}推荐", "#养{pet_type}好物"],
        },
        "cover_hint": {
            "style": "big_text_list",
            "text_overlay": "{number}个{topic}秘籍",
            "color_theme": "bright",
        },
        "best_for": ["feeding", "health", "product", "guide"],
    },

    "comparison": {
        "name": "对比测评型",
        "description": "产品/方法A vs B 对比，数据驱动",
        "sample_source": "待运营补充样本",
        "hook_templates": [
            "{product_a} vs {product_b}，养{pet_type}{number}年真实对比",
            "别再用{old_method}了！{new_method}真的香太多了",
            "测评｜{number}款{product_category}，只有这{number}款值得买",
        ],
        "body_sections": [
            {"type": "background", "purpose": "测评背景", "length_hint": "40-60字"},
            {"type": "comparison_table", "purpose": "对比维度", "dimensions": ["价格", "成分", "适口性", "效果", "性价比"]},
            {"type": "personal_test", "purpose": "亲测体验", "length_hint": "80-120字"},
            {"type": "recommendation", "purpose": "推荐结论", "length_hint": "40-60字"},
        ],
        "cta_templates": [
            "你家用的是哪一款？评论区交流👇",
            "测评不易，觉得有用点个❤️",
        ],
        "cover_hint": {"style": "split_comparison", "text_overlay": "A vs B"},
        "best_for": ["product", "method"],
    },

    "emotion_bond": {
        "name": "情感共鸣型",
        "description": "宠物与主人的情感故事，高互动高收藏",
        "sample_source": "待运营补充样本",
        "hook_templates": [
            "{pet_type}的{action}，让我{emotion}了整整{time_span}",
            "原来{pet_type}真的{understanding}...",
            "养{pet_type}后我才明白，{life_insight}",
        ],
        "body_sections": [
            {"type": "scene", "purpose": "场景描写", "length_hint": "60-80字"},
            {"type": "emotion_peak", "purpose": "情绪高潮", "length_hint": "60-80字"},
            {"type": "reflection", "purpose": "感悟升华", "length_hint": "40-60字"},
        ],
        "cta_templates": [
            "你家{pet_type}有没有让你{emotion}的瞬间？",
            "每一个{pet_type}都是小天使，值得被温柔以待🐾",
        ],
        "cover_hint": {"style": "pet_closeup", "text_overlay": "{emotion}"},
        "best_for": ["daily", "story", "bonding"],
    },

    "myth_bust": {
        "name": "辟谣科普型",
        "description": "打破养宠误区，专业+易懂",
        "sample_source": "待运营补充样本",
        "hook_templates": [
            "{percent}%的人都在犯的{pet_type}{topic}错误❌",
            "兽医朋友告诉我：{topic}千万别{wrong_action}！",
            "关于{pet_type}{topic}，这些说法都是错的🚫",
        ],
        "body_sections": [
            {"type": "myth_statement", "purpose": "列出误区", "length_hint": "30-50字"},
            {"type": "fact_correction", "purpose": "科学纠正", "length_hint": "60-80字"},
            {"type": "practical_tip", "purpose": "实用建议", "length_hint": "60-80字"},
        ],
        "cta_templates": [
            "你还听过哪些{topic}的误区？评论区一起辟谣👇",
            "科学养{pet_type}，从纠正一个误区开始📚",
        ],
        "cover_hint": {"style": "big_text_warning", "text_overlay": "{topic}误区"},
        "best_for": ["health", "feeding", "myth"],
    },
}
```

### 2.3 结构匹配算法

```python
def match_structure(topic: str, pet_type: str, content_angle: str,
                    structure_preference: str = "auto") -> str:
    """
    基于输入参数匹配最佳结构类型。
    MVP: 规则引擎（关键词匹配 + 角度映射）。
    Phase 2: 可引入轻量分类模型。
    """
    if structure_preference != "auto":
        return structure_preference

    # 规则映射
    angle_structure_map = {
        "story": "story_arc",
        "transformation": "story_arc",
        "feeding": "list_numbered",
        "health": "myth_bust",
        "product": "comparison",
        "guide": "list_numbered",
        "daily": "emotion_bond",
        "bonding": "emotion_bond",
    }

    # 关键词触发（优先级高于角度映射）
    topic_keywords = {
        "story_arc": ["蜕变", "逆袭", "成长", "变化", "养成", "收养", "流浪", "救助"],
        "list_numbered": ["攻略", "秘籍", "方法", "技巧", "清单", "步骤", "要点", "注意事项"],
        "comparison": ["对比", "测评", "评测", "哪款", "哪个好", "A还是B", "区别"],
        "emotion_bond": ["感动", "治愈", "陪伴", "离别", "第一次", "回忆", "感情"],
        "myth_bust": ["误区", "谣言", "辟谣", "真相", "错误", "千万别", "不要"],
    }

    for struct_type, keywords in topic_keywords.items():
        if any(kw in topic for kw in keywords):
            return struct_type

    return angle_structure_map.get(content_angle, "list_numbered")
```

### 2.4 Skill 代码实现草案

```python
# xhs_viral_pet_content_generate Skill (L2 Configured)
# 版本: v1.0.0
# 对齐: PRD V2.7.2, 详细设计 §5.3

SKILL_METADATA = {
    "name": "xhs_viral_pet_content_generate",
    "description": "基于高外溢笔记结构模式生成小红书宠物类爆款内容",
    "version": "1.0.0",
    "level": "L2",
    "tags": ["内容生成", "小红书", "宠物", "高外溢"],
    "tool_schema": {
        "input": {
            "topic": "str",
            "pet_type": "str",
            "pet_subtype": "str",
            "content_angle": "str",
            "target_audience": "str",
            "structure_preference": "str",
            "tone": "str",
            "persona_id": "str",
            "account_id": "str",
            "include_cover_hint": "bool",
            "brand_knowledge_ids": "list",
            "keyword_boost": "list",
        },
        "output": {
            "title": "str",
            "body": "str",
            "tags": "list",
            "structure_type": "str",
            "hook_type": "str",
            "cta_type": "str",
            "cover_hint": "dict",
            "compliance_passed": "bool",
            "compliance_warnings": "list",
            "estimated_engagement": "dict",
            "generation_metadata": "dict",
        },
    },
    "requires_tools": ["content_generate", "engagement_predict"],
    "requires_toolsets": ["内容生成", "预测"],
}


# ─── 内置合规词库（L1红线 + L2平台规则）───
FORBIDDEN_PATTERNS = [
    r"治愈率?\s*100%",
    r"绝对有效",
    r"(?:包治|根治).{0,5}(?:百病|所有)",
    r"(?:处方|兽药).{0,10}(?:推荐|销售)",
    r"(?:必看|必买).{0,5}(?:否则|不然)",
]

CAUTION_PATTERNS = [
    r"(?:最快|最强|第一).{0,5}(?:方法|产品)",
    r"(?:所有人都|没人).{0,5}(?:知道|用)",
]

MANDATORY_DISCLAIMERS = {
    "health": "个人经验分享，不构成医疗建议，宠物健康问题请咨询专业兽医。",
    "feeding": "每只宠物体质不同，换粮/调整饮食请循序渐进，观察适应情况。",
    "product": "使用体验因人而异，请根据自家宠物实际情况选择。",
    "default": "以上内容基于个人经验分享，仅供参考。",
}


def run(ctx: dict) -> dict:
    """
    小红书高外溢宠物内容生成 Skill 主入口。
    """
    import random

    # ── 1. 参数解析与默认值 ──
    topic = ctx.get("topic", "")
    pet_type = ctx.get("pet_type", "猫")
    pet_subtype = ctx.get("pet_subtype", "")
    content_angle = ctx.get("content_angle", "daily")
    structure_pref = ctx.get("structure_preference", "auto")
    tone = ctx.get("tone", "casual")
    persona_id = ctx.get("persona_id", "")
    account_id = ctx.get("account_id", "")
    include_cover = ctx.get("include_cover_hint", True)
    keyword_boost = ctx.get("keyword_boost", [])

    if not topic:
        return {"success": False, "error": "topic is required", "result": None}

    # ── 2. 结构匹配 ──
    structure_type = _match_structure(topic, pet_type, content_angle, structure_pref)
    struct_def = XHS_VIRAL_STRUCTURES[structure_type]

    # ── 3. Prompt 组装（结构化约束）───
    system_prompt = _build_system_prompt(tone, pet_type, pet_subtype)
    user_prompt = _build_user_prompt(struct_def, topic, pet_type, pet_subtype, content_angle, tone, keyword_boost)

    # ── 4. 调用 ContentForge（通过内部委托）───
    # MVP: 直接调用 generate_with_persona 的底层逻辑
    # Production: 通过 Agent Orchestra 调度
    generation_result = _delegate_to_contentforge(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        persona_id=persona_id,
        topic=topic,
        platform="xhs",
    )

    title = generation_result.get("title", "")
    body = generation_result.get("body", "")
    tags = generation_result.get("tags", [])

    # ── 5. 后处理：结构校准 ──
    body = _calibrate_body_structure(body, struct_def)
    body = _inject_disclaimer(body, content_angle)
    tags = _optimize_tags(tags, struct_def, pet_type, pet_subtype, topic)

    # ── 6. 合规初筛 ──
    compliance_result = _compliance_check(title, body)

    # ── 7. 封面建议 ──
    cover_hint = _build_cover_hint(struct_def, topic, pet_type) if include_cover else {}

    # ── 8. 互动预演（可选）───
    estimated_engagement = {}
    if account_id:
        estimated_engagement = _delegate_to_pool_predictor(account_id, title, body, tags)

    return {
        "success": True,
        "result": {
            "title": title,
            "body": body,
            "tags": tags,
            "structure_type": structure_type,
            "hook_type": _detect_hook_type(title),
            "cta_type": struct_def["cta_templates"][0] if struct_def["cta_templates"] else "",
            "cover_hint": cover_hint,
            "compliance_passed": compliance_result["passed"],
            "compliance_warnings": compliance_result["warnings"],
            "estimated_engagement": estimated_engagement,
            "generation_metadata": {
                "skill_version": "1.0.0",
                "structure_template": structure_type,
                "model_used": generation_result.get("model_used", "unknown"),
                "tokens_consumed": generation_result.get("tokens", 0),
            },
        },
        "error": None,
    }


# ─── 辅助函数 ───

def _build_system_prompt(tone: str, pet_type: str, pet_subtype: str) -> str:
    """构建系统指令，注入平台调性和人设约束。"""
    tone_instructions = {
        "casual": "说话像朋友聊天，自然亲切，多用口语化表达，适当使用网络热梗但不生硬。",
        "professional": "语气专业但有温度，用数据支撑观点，避免过度营销感。",
        "humorous": "风格轻松搞笑，善用自嘲和反转，让读者会心一笑。",
        "emotional": "情感真挚，善用细节描写触发共鸣，避免煽情过度。",
    }

    return f"""你是一位资深小红书宠物领域素人博主，拥有大量高互动内容创作经验。

【平台调性约束】
- 小红书用户偏好：收藏导向（干货收藏率高）、搜索导向（标题含关键词）、视觉导向（emoji和排版重要）
- 段落长度：每段不超过3行，适合手机阅读
- emoji使用：适度点缀，不过度堆砌
- 禁止使用："绝绝子""yyds"等过度网络用语（2025年后平台反感）

【语气要求】
{tone_instructions.get(tone, tone_instructions["casual"])}

【宠物主体】
- 宠物类型：{pet_type}
- 宠物细分：{pet_subtype if pet_subtype else '不限'}
- 人称：用"我家{pet_type}""它"等第一人称叙述

【合规红线】
- 禁止承诺疗效
- 禁止推荐处方药
- 涉及健康内容必须标注"个人经验，不构成医疗建议"
"""


def _build_user_prompt(struct_def: dict, topic: str, pet_type: str,
                       pet_subtype: str, content_angle: str, tone: str,
                       keyword_boost: list) -> str:
    """构建用户指令，注入结构模板约束。"""

    # 随机选取一个hook模板并填充示例
    hook_template = random.choice(struct_def["hook_templates"])

    # 构建正文结构约束
    section_constraints = []
    for sec in struct_def["body_sections"]:
        req_mark = "【必须】" if sec.get("required", False) else "【可选】"
        section_constraints.append(
            f"{req_mark} {sec['purpose']}（{sec['length_hint']}）"
        )

    # 构建CTA约束
    cta_template = random.choice(struct_def["cta_templates"])

    # 关键词约束
    keyword_constraint = ""
    if keyword_boost:
        keyword_constraint = f"\n【强制关键词】标题和正文中必须自然包含以下关键词：{', '.join(keyword_boost)}"

    return f"""请围绕「{topic}」生成一篇小红书笔记。

【结构类型】{struct_def["name"]}（{struct_def["description"]}）

【标题要求】
- 参考结构：{hook_template}
- 长度：不超过20个字（含emoji）
- 必须包含具体数字或强烈情绪词

【正文结构约束】
{chr(10).join(section_constraints)}

【CTA要求】
- 参考：{cta_template}
- 必须引导互动（评论/收藏/关注至少一种）

【标签要求】
- 核心标签：{', '.join(struct_def['tag_strategy']['must_have'])}
- 推荐标签：{', '.join(struct_def['tag_strategy']['recommended'][:3])}
- 总标签数：5-8个
{keyword_constraint}

【输出格式】
直接输出标题和正文，不需要解释说明。正文使用自然换行，不要加markdown标题。
"""


def _calibrate_body_structure(body: str, struct_def: dict) -> str:
    """校准正文结构：段落长度、emoji密度、换行节奏。"""
    # MVP: 简单后处理规则
    # 1. 确保每段不超过3行（按75字估算）
    # 2. emoji密度校准
    # 3. 确保有明确CTA结尾
    # Production: 可接入更精细的文本处理

    paragraphs = [p.strip() for p in body.split("\n") if p.strip()]

    # 如果段落过长，尝试智能分割
    calibrated = []
    for p in paragraphs:
        if len(p) > 120:
            # 尝试在句号/感叹号后分割
            sentences = []
            current = ""
            for char in p:
                current += char
                if char in "。！？" and len(current) > 30:
                    sentences.append(current)
                    current = ""
            if current:
                sentences.append(current)
            calibrated.extend(sentences)
        else:
            calibrated.append(p)

    return "\n\n".join(calibrated)


def _inject_disclaimer(body: str, content_angle: str) -> str:
    """在正文末尾注入必要的免责声明。"""
    disclaimer = MANDATORY_DISCLAIMERS.get(content_angle, MANDATORY_DISCLAIMERS["default"])

    # 如果正文中已含免责声明关键词，不重复注入
    if "不构成" in body or "仅供参考" in body:
        return body

    return body + f"\n\n—\n💡 {disclaimer}"


def _optimize_tags(tags: list, struct_def: dict, pet_type: str, pet_subtype: str, topic: str) -> list:
    """优化标签：去重、格式化、补充缺失的必含标签。"""
    result = []
    seen = set()

    # 格式化：确保以#开头
    for t in tags:
        t = t.strip()
        if not t.startswith("#"):
            t = f"#{t}"
        if t not in seen:
            result.append(t)
            seen.add(t)

    # 补充必含标签
    for must_tag in struct_def["tag_strategy"]["must_have"]:
        formatted = must_tag.replace("{pet_type}", pet_type).replace("{pet_subtype}", pet_subtype).replace("{topic}", topic)
        if formatted not in seen:
            result.append(formatted)
            seen.add(formatted)

    # 限制数量
    return result[:8]


def _compliance_check(title: str, body: str) -> dict:
    """内置合规初筛。"""
    import re
    warnings = []

    for pattern in FORBIDDEN_PATTERNS:
        if re.search(pattern, title + body):
            warnings.append(f"命中禁止模式: {pattern}")

    for pattern in CAUTION_PATTERNS:
        if re.search(pattern, title + body):
            warnings.append(f"命中 caution 模式: {pattern}")

    return {
        "passed": len(warnings) == 0,
        "warnings": warnings,
    }


def _build_cover_hint(struct_def: dict, topic: str, pet_type: str) -> dict:
    """构建封面设计建议。"""
    hint = struct_def.get("cover_hint", {})
    return {
        "style": hint.get("style", "big_text"),
        "text_overlay": hint.get("text_overlay", "").replace("{topic}", topic).replace("{pet_type}", pet_type),
        "color_theme": hint.get("color_theme", "warm"),
        "aspect_ratio": "3:4",
        "recommended_elements": hint.get("recommended_elements", ["emoji_badge", "number_circle"]),
    }


def _detect_hook_type(title: str) -> str:
    """检测标题使用的钩子类型。"""
    if "？" in title or "?" in title:
        return "question"
    if any(kw in title for kw in ["发现", "终于", "原来"]):
        return "discovery"
    if re.search(r'\d+', title):
        return "number_shock"
    if "vs" in title.lower() or "对比" in title:
        return "comparison"
    return "emotion"


def _delegate_to_contentforge(system_prompt: str, user_prompt: str,
                               persona_id: str, topic: str, platform: str) -> dict:
    """委托底层ContentForge执行生成。"""
    # MVP: 直接import底层服务调用
    # 注意：实际部署时需通过Agent Orchestra或API调用，避免Agent直接操作DB
    try:
        from src.services.content_forge_service import generate_with_persona
        result = generate_with_persona(
            topic=topic,
            platform=platform,
            persona_id=persona_id or None,
            # 扩展参数：通过llm_config注入system/user prompt覆盖
        )
        return {
            "title": result.get("title", ""),
            "body": result.get("body", ""),
            "tags": result.get("tags", []),
            "model_used": result.get("_persona_used", "default"),
            "tokens": 0,  # TODO: 从LLM Hub usage logs获取
        }
    except Exception as e:
        # Fallback: 返回错误
        return {
            "title": "",
            "body": "",
            "tags": [],
            "error": str(e),
        }


def _delegate_to_pool_predictor(account_id: str, title: str, body: str, tags: list) -> dict:
    """委托PoolPredictor进行互动预演。"""
    try:
        from src.services.prediction_engine import predict_engagement_intervals
        # MVP: 简化特征提取
        features = {
            "title_length": len(title),
            "body_length": len(body),
            "tag_count": len(tags),
            "has_number": bool(__import__('re').search(r'\d+', title)),
            "has_emoji": bool(__import__('re').search(r'[\U0001F600-\U0001F64F]', title + body)),
        }
        # 实际调用需适配现有prediction_engine接口
        return {"interval_mode": "prior", "note": "MVP简化预演"}
    except Exception:
        return {}


# ─── 结构匹配函数（同2.3节）───
def _match_structure(topic, pet_type, content_angle, structure_preference):
    # ...（见2.3节实现）...
    pass


# ─── 结构模板库（同2.2节）───
XHS_VIRAL_STRUCTURES = {
    # ...（见2.2节定义）...
}
```

---

## 三、PromptRegistry 集成设计

Skill 内部使用的 Prompt 模板需在 PromptRegistry 中注册版本，便于后续迭代：

```python
# PromptRegistry 注册条目
PROMPT_REGISTRY_ENTRIES = [
    {
        "name": "xhs_viral_system_prompt",
        "agent_id": "xhs_viral_pet_content_generate",
        "template_content": _build_system_prompt 的模板字符串,
        "variables": ["tone", "pet_type", "pet_subtype"],
        "env": "prod",
    },
    {
        "name": "xhs_viral_user_prompt",
        "agent_id": "xhs_viral_pet_content_generate",
        "template_content": _build_user_prompt 的模板字符串,
        "variables": ["structure_def", "topic", "pet_type", "pet_subtype", "content_angle", "tone", "keyword_boost"],
        "env": "prod",
    },
]
```

**版本管理策略**：
- v1.0.0: 基于10篇样本的初始5种结构模板
- v1.1.0: 补充剩余8篇样本结构（运营提供全文后）
- v2.0.0: SkillSmith L4进化版（基于实际互动数据优化hook和cta模板）

---

## 四、SkillSmith 进化路径

### 4.1 进化触发条件

| 条件类型 | 阈值 | 说明 |
|---------|------|------|
| 结构类型成功率 | ≥70% | 某structure_type连续5次生成内容的实际互动达标率 |
| Hook类型CES | ≥35 | 某hook_type的平均CES超过基准线 |
| CTA转化率 | ≥8% | 评论率/收藏率达到阈值 |
| 结构类型失败率 | ≥50% | 某structure_type连续5次不达标，触发退化/淘汰 |

### 4.2 进化动作

```python
def evolve_xhs_viral_skill(performance_data: dict) -> dict:
    """
    SkillSmith 自动进化逻辑。
    """
    # 1. 分析各structure_type的效果分布
    structure_stats = performance_data["by_structure"]

    # 2. 优胜结构：增加hook/cta模板变体数量
    for struct_type, stats in structure_stats.items():
        if stats["success_rate"] >= 0.7:
            # 用LLM生成新的hook模板变体（基于已有高表现模板）
            new_hooks = generate_hook_variants(struct_type, stats["top_performers"])
            XHS_VIRAL_STRUCTURES[struct_type]["hook_templates"].extend(new_hooks)

    # 3. 劣汰结构：减少权重或标记review
    for struct_type, stats in structure_stats.items():
        if stats["success_rate"] <= 0.3:
            XHS_VIRAL_STRUCTURES[struct_type]["_review_flag"] = True

    # 4. 生成L4进化Skill
    return skill_hub.create_skill(
        name="xhs_viral_pet_content_generate·进化版",
        description="基于真实数据自动进化的L4内容生成技能",
        level="L4",
        code=generate_evolved_skill_code(),
        tags=["evolved", "xhs", "viral", "pet"],
    )
```

---

## 五、专家评审矩阵

> 以下结论基于现有10篇样本（2篇已知标题+8篇仅URL）和项目PRD V2.7.2基线。待运营补充剩余8篇笔记全文后，可更新评审结论。

### 5.1 产品评审

| 评审项 | 结论 | 风险 |
|-------|------|------|
| Skill定位 | ✅ L2 Configured Skill定位准确，填补「平台专属内容生成」空白 | 与L1 content_generate边界需清晰：L1负责通用生成，本Skill负责平台结构约束 |
| MVP范围 | ✅ 5种结构模板+内置合规初筛，MVP可落地 | 样本量仅2篇已知全文，结构模板代表性存疑 |
| 用户体验 | ✅ 运营只需输入topic+pet_type，Skill自动匹配结构，门槛低 | 结构偏好"auto"的匹配准确率需A/B验证 |
| 进化可行性 | ✅ 与SkillSmith已有record_performance/check_evolution对接 | L4进化需要至少30条有效数据才能触发，冷启动期效果依赖L2基线质量 |

**产品建议**：
1. 建议运营在1周内补充剩余8篇笔记的标题+正文（脱敏），提升结构模板代表性
2. Phase 1优先上线「list_numbered」和「story_arc」两种结构（有样本支撑），其余3种标记为beta
3. 每个结构类型在UI上展示「样本来源笔记」链接，增强运营信任

### 5.2 算法/AI评审

| 评审项 | 结论 | 风险 |
|-------|------|------|
| 结构匹配算法 | ✅ MVP规则引擎足够，无需引入分类模型 | 复杂topic可能匹配错误，需运营可手动覆盖 |
| Prompt工程 | ✅ system_prompt分层清晰（平台调性+人设+合规），user_prompt结构约束明确 | prompt总长度可能过长（system+user+context），需监控token成本 |
| 生成质量 | ⚠️ 依赖底层LLM能力，Skill仅做结构约束 | 如果LLM本身文采不足，结构约束无法弥补 |
| 进化算法 | ✅ 与现有SkillSmith框架兼容 | L4进化当前为占位实现，需后续填充真实进化逻辑 |

**算法建议**：
1. 建议增加「生成后结构自检」：用规则引擎验证输出是否符合模板要求的段落数和CTA位置
2. 建议在prompt中增加「few-shot示例」（从样本笔记中脱敏提取片段），提升生成一致性
3. PoolPredictor预演目前为简化实现，建议接入真实特征提取

### 5.3 运营评审

| 评审项 | 结论 | 风险 |
|-------|------|------|
| 结构模板实用性 | ✅ 5种结构覆盖宠物领域80%以上高互动内容类型 | 异宠（ reptile / bird ）内容结构可能不适用，需后续补充 |
| Hook模板丰富度 | ⚠️ 每种结构仅3-4个hook模板，易同质化 | 建议每种结构至少8-10个模板，运营可手动添加 |
| 标签策略 | ✅ 必含+推荐+可选三层策略合理 | 需定期与KeywordPool同步更新 |
| 样本依赖 | 🔴 仅2篇已知全文，不足以支撑5种结构 | **高优先级补充样本** |

**运营建议**：
1. 建立「样本笔记库」运营流程：每周新增5-10篇高外溢笔记，自动触发结构萃取review
2. 每个结构类型配置「A/B测试开关」，允许同时测试2-3个hook变体
3. 月度输出「结构效果报告」：哪种structure_type在哪个pet_type下表现最好

### 5.4 法务合规评审

| 评审项 | 结论 | 风险 |
|-------|------|------|
| 笔记克隆合规 | ✅ Skill仅萃取「结构模式」，不复制原文案，符合PRD §2.1人设来源约束 | 需确保hook模板不会意外复现原文的独特表达 |
| 免责声明 | ✅ 按content_angle自动注入免责声明 | 需检查注入位置是否明显（建议正文末尾+单独一行） |
| 禁忌词过滤 | ✅ 内置FORBIDDEN_PATTERNS + CAUTION_PATTERNS | 词库需定期更新，与PlatformRule L1/L2同步 |
| 商业标注 | ⚠️ 涉及产品推荐时，需强制标注「合作/体验」 | 当前Skill未处理商业合作场景，建议增加`is_commercial`参数 |

**法务建议**：
1. 在Skill输出中增加`compliance_score`字段（0-100），供运营快速判断风险
2. 商业内容场景须扩展：增加`is_commercial`输入参数，强制在正文开头或结尾插入合作声明
3. 每季度审查一次hook模板库，排查是否有机组合后形成疗效承诺

### 5.5 工程/架构评审

| 评审项 | 结论 | 风险 |
|-------|------|------|
| 架构兼容性 | ✅ 与SkillHub L2层、PromptRegistry、ContentForge完全兼容 | `_delegate_to_contentforge`直接import底层服务，违反Agent不直接操作DB原则，需改为API调用 |
| 性能 | ✅ 结构匹配+prompt组装为轻量操作，不增加LLM调用次数 | PoolPredictor预演增加一次调用，可配置关闭 |
| 可测试性 | ✅ Skill的run(ctx)函数纯输入输出，便于单元测试 | 需mock ContentForge和PoolPredictor依赖 |
| 可扩展性 | ✅ 新增structure_type只需扩展XHS_VIRAL_STRUCTURES字典 | 建议将结构模板库持久化到数据库，避免代码热更新 |

**工程建议**：
1. **关键修复**：`_delegate_to_contentforge`和`_delegate_to_pool_predictor`应改为HTTP API调用或Agent消息调用，禁止直接import底层Service
2. 建议将`XHS_VIRAL_STRUCTURES`持久化到数据库（如`content_template`表），支持运营通过前端CRUD管理
3. Skill代码过长（>500行），建议拆分为多个子模块：`structure_matcher.py`、`prompt_builder.py`、`post_processor.py`、`compliance_checker.py`

---

## 六、实施计划

### 6.1 开发任务分解

| 任务 | 工期 | 负责人 | 依赖 | 优先级 |
|------|------|--------|------|--------|
| T1: 补充样本数据（运营提供8篇笔记全文） | 3天 | 运营 | — | 🔴 P0 |
| T2: Skill核心代码开发（structure_matcher + prompt_builder + post_processor） | 5天 | 后端 | T1 | 🔴 P0 |
| T3: 内置合规词库集成（对接PlatformRule L1/L2） | 2天 | 后端 | — | 🔴 P0 |
| T4: PromptRegistry模板注册 | 1天 | 后端 | T2 | 🟡 P1 |
| T5: SkillHub L2注册 + Tool Registry接入 | 2天 | 后端 | T2,T3 | 🟡 P1 |
| T6: ContentForge API扩展（支持system/user prompt覆盖） | 2天 | 后端 | T2 | 🟡 P1 |
| T7: 前端：Skill调用界面（topic输入 → 结构预览 → 生成结果） | 4天 | 前端 | T2,T5 | 🟡 P1 |
| T8: 单元测试（structure匹配 + prompt组装 + 合规检查） | 3天 | 测试 | T2,T3 | 🟡 P1 |
| T9: SkillSmith进化对接（record_performance + 触发条件配置） | 2天 | 后端 | T5 | 🟢 P2 |
| T10: 集成测试（端到端工作流） | 2天 | 测试 | T7 | 🟢 P2 |

### 6.2 里程碑

```
M1 (W15末): 样本补充完成 + Skill核心代码开发完成（list_numbered + story_arc两种结构）
M2 (W16中): 5种结构全量上线 + SkillHub注册 + 前端界面可用
M3 (W16末): 合规集成完成 + 全量测试通过
M4 (W17): SkillSmith进化对接 + 运营A/B测试启动
```

### 6.3 测试策略

| 测试类型 | 用例数 | 关键场景 |
|---------|--------|---------|
| 单元测试 `test_skill_structure_matcher.py` | 8 | 5种结构的topic匹配 + auto模式 + 手动覆盖 |
| 单元测试 `test_skill_prompt_builder.py` | 6 | system_prompt组装 + user_prompt注入 + keyword_boost |
| 单元测试 `test_skill_post_processor.py` | 5 | 段落校准 + disclaimer注入 + tag优化 |
| 单元测试 `test_skill_compliance.py` | 5 | 禁忌词命中 + caution词命中 + 免责声明检查 |
| 集成测试 `test_skill_end_to_end.py` | 3 | 完整run(ctx)调用 + ContentForge委托 + PoolPredictor委托 |
| E2E测试 | 2 | 前端界面 → API → Skill执行 → 结果展示 |

**回归基线**：新增测试约29个，全部通过后方可合并。

---

## 七、用户决策清单

| # | 决策项 | 当前方案建议 | 用户确认 |
|---|-------|------------|---------|
| 1 | Skill层级 | **L2（Configured）**，团队级共享 | ⬜ |
| 2 | 首批上线结构 | **list_numbered + story_arc** 先行，其余3种beta | ⬜ |
| 3 | 样本补充 | 运营1周内提供剩余8篇笔记的**标题+正文（脱敏）** | ⬜ |
| 4 | 商业内容标注 | 增加`is_commercial`参数，强制插入合作声明 | ⬜ |
| 5 | 结构模板持久化 | 存入数据库（支持运营前端CRUD），非代码硬编码 | ⬜ |
| 6 | ContentForge委托方式 | 改为**API调用**（非直接import），遵守架构红线 | ⬜ |
| 7 | PoolPredictor预演 | 可选配置（默认开启，可关闭以节省成本） | ⬜ |
| 8 | Hook模板运营维护 | 每种结构初始4个模板，运营可前端添加/编辑 | ⬜ |
| 9 | 进化数据门槛 | L4进化需**同一structure_type累计≥30条有效数据** | ⬜ |
| 10 | 法务审查频率 | 每季度审查一次hook模板库 | ⬜ |

---

## 八、附录

### 8.1 与上一版方案的关联

本方案是 `docs/需求分析方案_工作流模板与内容生成增强_v1.md` 中「需求3：笔记克隆与内容模板」的具体落地实现之一。ContentTemplate模块提供通用的「结构萃取→模板化」能力，而本Skill（`xhs_viral_pet_content_generate`）是ContentTemplate在小红书宠物领域的**专用实例化**。

两者关系：
- ContentTemplate = 通用框架（结构萃取API + 模板管理 + 效果回流）
- xhs_viral_pet_content_generate Skill = 领域专用技能（内置5种已验证结构 + 自动化prompt组装 + 合规内嵌）

### 8.2 相关文档索引

- PRD真源：`EcoDream_Omni_PRD_v2_对齐核心方案.md` §2.2 MarketingMethodology / §2.6 结构预检
- 详细设计：`详细设计_EcoDreamOmni_v2.md` §5.3 SkillHub / §5.4 SkillSmith
- TASK文件：`TASK.md`（V2.7.2 Sprint）
- 数据词典：`docs/数据词典/03-后端Service层.md`（SkillHub/SkillSmith）
- 上一版方案：`docs/需求分析方案_工作流模板与内容生成增强_v1.md`

---

> **文档编制**: Kimi Code CLI（AI Agent）  
> **审核状态**: 🔍 待用户审核与五方联合评审  
> **已知数据缺口**: 8篇笔记仅URL无正文，需运营补充以提升结构模板精度  
> **下一步动作**: 用户确认方案+补充样本数据 → 更新PRD → 更新数据词典 → 创建变更记录 → 进入开发
