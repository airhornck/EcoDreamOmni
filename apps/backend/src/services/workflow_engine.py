"""Workflow Engine — Serial Pipeline orchestration.

Aligned with detailed design §8 / PRD V2.6 §10.4.
MVP: Serial pipelines only (no DAG branching, parallel nodes, or conditional jumps).
"""

import secrets
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class NodeType(str, Enum):
    AGENT = "AGENT"
    HUMAN_APPROVAL = "HUMAN_APPROVAL"
    TIMER = "TIMER"
    SKILL = "SKILL"


class FailStrategy(str, Enum):
    FAIL_FAST = "FAIL_FAST"
    CONTINUE = "CONTINUE"
    RETRY_THEN_FAIL = "RETRY_THEN_FAIL"


class WorkflowStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class ExecutionStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    TIMEOUT = "TIMEOUT"
    HUMAN_WAIT = "HUMAN_WAIT"


# ─── Dataclasses ───

@dataclass
class WorkflowNode:
    node_index: int
    node_type: NodeType
    node_name: str
    agent_id: Optional[str] = None
    prompt_template_id: Optional[str] = None
    fail_strategy: FailStrategy = FailStrategy.FAIL_FAST
    human_config: Optional[Dict[str, Any]] = None
    timer_seconds: Optional[int] = None
    skill_id: Optional[str] = None
    depends_on: List[int] = field(default_factory=list)
    inputs: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class WorkflowTemplate:
    id: str
    name: str
    description: str
    source_preset: Optional[str]
    version: int
    status: str  # DRAFT / ACTIVE / DEPRECATED
    owner: str
    nodes: List[WorkflowNode]
    created_at: str
    updated_at: str


@dataclass
class WorkflowExecution:
    id: str
    task_id: str
    template_id: str
    template_version: int
    status: WorkflowStatus
    current_node_index: int
    context: Dict[str, Any] = field(default_factory=dict)
    started_at: Optional[str] = None
    ended_at: Optional[str] = None
    created_at: str = ""
    completed_nodes: List[int] = field(default_factory=list)
    failed_nodes: List[int] = field(default_factory=list)
    resumed_count: int = 0


@dataclass
class NodeExecution:
    id: str
    execution_id: str
    node_index: int
    node_type: str
    status: ExecutionStatus
    input_context: Dict[str, Any] = field(default_factory=dict)
    output_context: Dict[str, Any] = field(default_factory=dict)
    started_at: Optional[str] = None
    ended_at: Optional[str] = None
    duration_ms: Optional[int] = None
    error_message: Optional[str] = None
    created_at: str = ""


# ─── DAG Compilation ───

@dataclass
class CompiledDAG:
    """编译期 DAG 结果：拓扑序 + 邻接表 + 层级分组."""

    topological_order: List[int]
    adjacency: Dict[int, List[int]]
    reverse_adjacency: Dict[int, List[int]]
    levels: List[List[int]]


def compile_dag(nodes: List[WorkflowNode]) -> CompiledDAG:
    """编译工作流模板为 DAG，验证无环并返回拓扑序.

    - 若节点 depends_on 为空，隐式依赖前一个 node_index（向后兼容串行模板）
    - 使用 Kahn 算法检测环并计算层级
    """
    nodes_by_index = {n.node_index: n for n in nodes}
    if not nodes_by_index:
        return CompiledDAG(topological_order=[], adjacency={}, reverse_adjacency={}, levels=[])

    adjacency: Dict[int, List[int]] = {idx: [] for idx in nodes_by_index}
    reverse_adj: Dict[int, List[int]] = {idx: [] for idx in nodes_by_index}
    in_degree: Dict[int, int] = {idx: 0 for idx in nodes_by_index}

    for idx, node in nodes_by_index.items():
        deps = node.depends_on
        if not deps:
            # 向后兼容：隐式依赖前一个索引
            prev_candidates = [i for i in nodes_by_index if i < idx]
            if prev_candidates:
                deps = [max(prev_candidates)]
        for dep in (deps or []):
            if dep not in nodes_by_index:
                raise ValueError(f"Dependency node {dep} not found for node {idx}")
            adjacency[dep].append(idx)
            reverse_adj[idx].append(dep)
            in_degree[idx] += 1

    # Kahn 拓扑排序 + 层级分组
    queue = sorted([idx for idx, deg in in_degree.items() if deg == 0])
    topo_order: List[int] = []
    levels: List[List[int]] = []

    while queue:
        levels.append(list(queue))
        next_queue: List[int] = []
        for u in queue:
            topo_order.append(u)
            for v in adjacency[u]:
                in_degree[v] -= 1
                if in_degree[v] == 0:
                    next_queue.append(v)
        queue = sorted(next_queue)

    if len(topo_order) != len(nodes_by_index):
        raise ValueError("DAG cycle detected in workflow template")

    return CompiledDAG(
        topological_order=topo_order,
        adjacency=adjacency,
        reverse_adjacency=reverse_adj,
        levels=levels,
    )


def _find_next_executable_node(dag: CompiledDAG, execution: WorkflowExecution) -> Optional[int]:
    """找到下一个可执行的节点（所有依赖已完成）."""
    completed = set(execution.completed_nodes)
    failed = set(execution.failed_nodes)
    done = completed | failed

    for idx in dag.topological_order:
        if idx in done:
            continue
        deps = dag.reverse_adjacency.get(idx, [])
        if all(d in done for d in deps):
            return idx
    return None


# ─── Checkpoint integration ───

_checkpoint_mgr: Optional[Any] = None


def set_checkpoint_manager(mgr: Any) -> None:
    """注入 CheckpointManager（由应用启动时调用）."""
    global _checkpoint_mgr
    _checkpoint_mgr = mgr


def _get_checkpoint_mgr() -> Any:
    """获取 CheckpointManager，未注入时返回 None."""
    return _checkpoint_mgr


# ─── Preset Templates ───

CONTENT_CREATION_STANDARD = WorkflowTemplate(
    id="content_creation_standard",
    name="标准内容生产工作流",
    description="热点侦察→结构分析→品牌知识注入→合规预检→关键词注入→框架生成→正文生成→图片生成→合规审核→互动预演→人工审核→发布",
    source_preset="content_creation_standard",
    version=2,
    status="ACTIVE",
    owner="system",
    nodes=[
        WorkflowNode(0, NodeType.AGENT, "热点侦察", agent_id="trend-scout", fail_strategy=FailStrategy.FAIL_FAST),
        WorkflowNode(1, NodeType.AGENT, "结构分析", agent_id="marketing-methodology", fail_strategy=FailStrategy.FAIL_FAST),
        WorkflowNode(2, NodeType.SKILL, "品牌知识注入", skill_id="brand_knowledge_inject", fail_strategy=FailStrategy.FAIL_FAST),
        WorkflowNode(3, NodeType.AGENT, "合规预检", agent_id="vetdrug-validate", fail_strategy=FailStrategy.FAIL_FAST),
        WorkflowNode(4, NodeType.SKILL, "关键词注入", skill_id="keyword_inject", fail_strategy=FailStrategy.FAIL_FAST),
        WorkflowNode(5, NodeType.AGENT, "框架生成", agent_id="content-forge", prompt_template_id="cf-outline", fail_strategy=FailStrategy.FAIL_FAST),
        WorkflowNode(6, NodeType.AGENT, "正文生成", agent_id="content-forge", prompt_template_id="cf-body", fail_strategy=FailStrategy.FAIL_FAST),
        WorkflowNode(7, NodeType.AGENT, "图片生成", agent_id="image-forge", fail_strategy=FailStrategy.CONTINUE),
        WorkflowNode(8, NodeType.AGENT, "合规审核", agent_id="compliance-guard", fail_strategy=FailStrategy.FAIL_FAST),
        WorkflowNode(9, NodeType.AGENT, "互动预演", agent_id="pool-predictor", fail_strategy=FailStrategy.CONTINUE),
        WorkflowNode(10, NodeType.HUMAN_APPROVAL, "人工审核", human_config={"review_type": "CONTENT_PUBLISH", "timeout_hours": 24, "required_role": "content_reviewer"}),
        WorkflowNode(11, NodeType.AGENT, "发布", agent_id="publisher", fail_strategy=FailStrategy.FAIL_FAST),
    ],
    created_at="",
    updated_at="",
)

CONTENT_CREATION_LIGHT = WorkflowTemplate(
    id="content_creation_light",
    name="轻量内容生产工作流",
    description="简化版：框架生成→正文生成→关键词注入→合规审核→互动预演→人工审核→发布",
    source_preset="content_creation_light",
    version=2,
    status="ACTIVE",
    owner="system",
    nodes=[
        WorkflowNode(0, NodeType.AGENT, "框架生成", agent_id="content-forge", prompt_template_id="cf-outline", fail_strategy=FailStrategy.FAIL_FAST),
        WorkflowNode(1, NodeType.AGENT, "正文生成", agent_id="content-forge", prompt_template_id="cf-body", fail_strategy=FailStrategy.FAIL_FAST),
        WorkflowNode(2, NodeType.SKILL, "关键词注入", skill_id="keyword_inject", fail_strategy=FailStrategy.FAIL_FAST),
        WorkflowNode(3, NodeType.AGENT, "合规审核", agent_id="compliance-guard", fail_strategy=FailStrategy.FAIL_FAST),
        WorkflowNode(4, NodeType.AGENT, "互动预演", agent_id="pool-predictor", fail_strategy=FailStrategy.CONTINUE),
        WorkflowNode(5, NodeType.HUMAN_APPROVAL, "人工审核", human_config={"review_type": "CONTENT_PUBLISH", "timeout_hours": 24}),
        WorkflowNode(6, NodeType.AGENT, "发布", agent_id="publisher", fail_strategy=FailStrategy.FAIL_FAST),
    ],
    created_at="",
    updated_at="",
)

TREND_SCOUT_ONLY = WorkflowTemplate(
    id="trend_scout_only",
    name="热点侦察工作流",
    description="仅执行 TrendScout 节点",
    source_preset="trend_scout_only",
    version=1,
    status="ACTIVE",
    owner="system",
    nodes=[
        WorkflowNode(0, NodeType.AGENT, "热点侦察", agent_id="trend-scout", fail_strategy=FailStrategy.FAIL_FAST),
    ],
    created_at="",
    updated_at="",
)

DATA_ANALYSIS_ONLY = WorkflowTemplate(
    id="data_analysis_only",
    name="数据分析工作流",
    description="仅执行 DataAnalyst 节点",
    source_preset="data_analysis_only",
    version=1,
    status="ACTIVE",
    owner="system",
    nodes=[
        WorkflowNode(0, NodeType.AGENT, "数据分析", agent_id="data-analyst", fail_strategy=FailStrategy.FAIL_FAST),
    ],
    created_at="",
    updated_at="",
)

# ─── Content Format Specific Templates (Phase 2) ───

CONTENT_CREATION_NOTE_IMAGE = WorkflowTemplate(
    id="content_creation_note_image",
    name="图文内容生产工作流",
    description="专为图文笔记优化：热点侦察→结构分析→品牌知识注入→合规预检→关键词注入→图文框架→正文生成→图片生成→合规审核→互动预演→人工审核→发布",
    source_preset="content_creation_note_image",
    version=2,
    status="ACTIVE",
    owner="system",
    nodes=[
        WorkflowNode(0, NodeType.AGENT, "热点侦察", agent_id="trend-scout", fail_strategy=FailStrategy.FAIL_FAST),
        WorkflowNode(1, NodeType.AGENT, "结构分析", agent_id="marketing-methodology", fail_strategy=FailStrategy.FAIL_FAST),
        WorkflowNode(2, NodeType.SKILL, "品牌知识注入", skill_id="brand_knowledge_inject", fail_strategy=FailStrategy.FAIL_FAST),
        WorkflowNode(3, NodeType.AGENT, "合规预检", agent_id="vetdrug-validate", fail_strategy=FailStrategy.FAIL_FAST),
        WorkflowNode(4, NodeType.SKILL, "关键词注入", skill_id="keyword_inject", fail_strategy=FailStrategy.FAIL_FAST),
        WorkflowNode(5, NodeType.AGENT, "图文框架", agent_id="content-forge", prompt_template_id="cf-outline", fail_strategy=FailStrategy.FAIL_FAST),
        WorkflowNode(6, NodeType.AGENT, "正文生成", agent_id="content-forge", prompt_template_id="cf-body", fail_strategy=FailStrategy.FAIL_FAST),
        WorkflowNode(7, NodeType.AGENT, "图片生成", agent_id="image-forge", fail_strategy=FailStrategy.CONTINUE),
        WorkflowNode(8, NodeType.AGENT, "合规审核", agent_id="compliance-guard", fail_strategy=FailStrategy.FAIL_FAST),
        WorkflowNode(9, NodeType.AGENT, "互动预演", agent_id="pool-predictor", fail_strategy=FailStrategy.CONTINUE),
        WorkflowNode(10, NodeType.HUMAN_APPROVAL, "人工审核", human_config={"review_type": "CONTENT_PUBLISH", "timeout_hours": 24, "required_role": "content_reviewer"}),
        WorkflowNode(11, NodeType.AGENT, "发布", agent_id="publisher", fail_strategy=FailStrategy.FAIL_FAST),
    ],
    created_at="",
    updated_at="",
)

CONTENT_CREATION_VIDEO_CLONE = WorkflowTemplate(
    id="content_creation_video_clone",
    name="视频复刻工作流",
    description="视频复刻：热点侦察→结构分析→品牌知识注入→合规预检→关键词注入→脚本拆解→复刻脚本生成→合规审核→互动预演→人工审核→发布",
    source_preset="content_creation_video_clone",
    version=2,
    status="ACTIVE",
    owner="system",
    nodes=[
        WorkflowNode(0, NodeType.AGENT, "热点侦察", agent_id="trend-scout", fail_strategy=FailStrategy.FAIL_FAST),
        WorkflowNode(1, NodeType.AGENT, "结构分析", agent_id="marketing-methodology", fail_strategy=FailStrategy.FAIL_FAST),
        WorkflowNode(2, NodeType.SKILL, "品牌知识注入", skill_id="brand_knowledge_inject", fail_strategy=FailStrategy.FAIL_FAST),
        WorkflowNode(3, NodeType.AGENT, "合规预检", agent_id="vetdrug-validate", fail_strategy=FailStrategy.FAIL_FAST),
        WorkflowNode(4, NodeType.SKILL, "关键词注入", skill_id="keyword_inject", fail_strategy=FailStrategy.FAIL_FAST),
        WorkflowNode(5, NodeType.AGENT, "脚本拆解", agent_id="content-forge", prompt_template_id="cf-video-deconstruct", fail_strategy=FailStrategy.FAIL_FAST),
        WorkflowNode(6, NodeType.AGENT, "复刻脚本", agent_id="content-forge", prompt_template_id="cf-video-clone", fail_strategy=FailStrategy.FAIL_FAST),
        WorkflowNode(7, NodeType.AGENT, "合规审核", agent_id="compliance-guard", fail_strategy=FailStrategy.FAIL_FAST),
        WorkflowNode(8, NodeType.AGENT, "互动预演", agent_id="pool-predictor", fail_strategy=FailStrategy.CONTINUE),
        WorkflowNode(9, NodeType.HUMAN_APPROVAL, "人工审核", human_config={"review_type": "CONTENT_PUBLISH", "timeout_hours": 24, "required_role": "content_reviewer"}),
        WorkflowNode(10, NodeType.AGENT, "发布", agent_id="publisher", fail_strategy=FailStrategy.FAIL_FAST),
    ],
    created_at="",
    updated_at="",
)

CONTENT_CREATION_VIDEO_ORIGINAL = WorkflowTemplate(
    id="content_creation_video_original",
    name="视频原创工作流",
    description="视频原创：热点侦察→结构分析→品牌知识注入→合规预检→关键词注入→原创脚本生成→分镜设计→合规审核→互动预演→人工审核→发布",
    source_preset="content_creation_video_original",
    version=2,
    status="ACTIVE",
    owner="system",
    nodes=[
        WorkflowNode(0, NodeType.AGENT, "热点侦察", agent_id="trend-scout", fail_strategy=FailStrategy.FAIL_FAST),
        WorkflowNode(1, NodeType.AGENT, "结构分析", agent_id="marketing-methodology", fail_strategy=FailStrategy.FAIL_FAST),
        WorkflowNode(2, NodeType.SKILL, "品牌知识注入", skill_id="brand_knowledge_inject", fail_strategy=FailStrategy.FAIL_FAST),
        WorkflowNode(3, NodeType.AGENT, "合规预检", agent_id="vetdrug-validate", fail_strategy=FailStrategy.FAIL_FAST),
        WorkflowNode(4, NodeType.SKILL, "关键词注入", skill_id="keyword_inject", fail_strategy=FailStrategy.FAIL_FAST),
        WorkflowNode(5, NodeType.AGENT, "原创脚本", agent_id="content-forge", prompt_template_id="cf-video-script", fail_strategy=FailStrategy.FAIL_FAST),
        WorkflowNode(6, NodeType.AGENT, "分镜设计", agent_id="content-forge", prompt_template_id="cf-storyboard", fail_strategy=FailStrategy.FAIL_FAST),
        WorkflowNode(7, NodeType.AGENT, "合规审核", agent_id="compliance-guard", fail_strategy=FailStrategy.FAIL_FAST),
        WorkflowNode(8, NodeType.AGENT, "互动预演", agent_id="pool-predictor", fail_strategy=FailStrategy.CONTINUE),
        WorkflowNode(9, NodeType.HUMAN_APPROVAL, "人工审核", human_config={"review_type": "CONTENT_PUBLISH", "timeout_hours": 24, "required_role": "content_reviewer"}),
        WorkflowNode(10, NodeType.AGENT, "发布", agent_id="publisher", fail_strategy=FailStrategy.FAIL_FAST),
    ],
    created_at="",
    updated_at="",
)

CONTENT_CREATION_TEXT_ARTICLE = WorkflowTemplate(
    id="content_creation_text_article",
    name="长文章生产工作流",
    description="长文章：热点侦察→结构分析→品牌知识注入→合规预检→关键词注入→文章大纲→长文生成→合规审核→互动预演→人工审核→发布",
    source_preset="content_creation_text_article",
    version=2,
    status="ACTIVE",
    owner="system",
    nodes=[
        WorkflowNode(0, NodeType.AGENT, "热点侦察", agent_id="trend-scout", fail_strategy=FailStrategy.FAIL_FAST),
        WorkflowNode(1, NodeType.AGENT, "结构分析", agent_id="marketing-methodology", fail_strategy=FailStrategy.FAIL_FAST),
        WorkflowNode(2, NodeType.SKILL, "品牌知识注入", skill_id="brand_knowledge_inject", fail_strategy=FailStrategy.FAIL_FAST),
        WorkflowNode(3, NodeType.AGENT, "合规预检", agent_id="vetdrug-validate", fail_strategy=FailStrategy.FAIL_FAST),
        WorkflowNode(4, NodeType.SKILL, "关键词注入", skill_id="keyword_inject", fail_strategy=FailStrategy.FAIL_FAST),
        WorkflowNode(5, NodeType.AGENT, "文章大纲", agent_id="content-forge", prompt_template_id="cf-article-outline", fail_strategy=FailStrategy.FAIL_FAST),
        WorkflowNode(6, NodeType.AGENT, "长文生成", agent_id="content-forge", prompt_template_id="cf-article-body", fail_strategy=FailStrategy.FAIL_FAST),
        WorkflowNode(7, NodeType.AGENT, "合规审核", agent_id="compliance-guard", fail_strategy=FailStrategy.FAIL_FAST),
        WorkflowNode(8, NodeType.AGENT, "互动预演", agent_id="pool-predictor", fail_strategy=FailStrategy.CONTINUE),
        WorkflowNode(9, NodeType.HUMAN_APPROVAL, "人工审核", human_config={"review_type": "CONTENT_PUBLISH", "timeout_hours": 24, "required_role": "content_reviewer"}),
        WorkflowNode(10, NodeType.AGENT, "发布", agent_id="publisher", fail_strategy=FailStrategy.FAIL_FAST),
    ],
    created_at="",
    updated_at="",
)


# ─── In-memory stores ───
_template_db: Dict[str, WorkflowTemplate] = {}
_template_version_history: Dict[str, List[WorkflowTemplate]] = {}  # {template_id: [older_versions...]}
_execution_db: Dict[str, WorkflowExecution] = {}
_node_execution_db: List[NodeExecution] = []


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id(prefix: str) -> str:
    return f"{prefix}_{secrets.token_urlsafe(8)}"


# ─── Template Management ───

def create_template(
    name: str,
    nodes: List[Dict[str, Any]],
    *,
    description: str = "",
    source_preset: Optional[str] = None,
    owner: str = "",
) -> WorkflowTemplate:
    tmpl_id = _new_id("wf")
    now = _now()

    parsed_nodes = []
    for i, n in enumerate(nodes):
        node = WorkflowNode(
            node_index=n.get("node_index", i),
            node_type=NodeType(n["node_type"]),
            node_name=n["node_name"],
            agent_id=n.get("agent_id"),
            prompt_template_id=n.get("prompt_template_id"),
            fail_strategy=FailStrategy(n.get("fail_strategy", "FAIL_FAST")),
            human_config=n.get("human_config"),
            timer_seconds=n.get("timer_seconds"),
            skill_id=n.get("skill_id"),
            depends_on=n.get("depends_on", []),
            inputs=n.get("inputs", []),
        )
        parsed_nodes.append(node)

    # Red line: any workflow containing Publisher must have human_approval
    has_publisher = any(n.agent_id == "publisher" for n in parsed_nodes if n.node_type == NodeType.AGENT)
    has_human = any(n.node_type == NodeType.HUMAN_APPROVAL for n in parsed_nodes)
    if has_publisher and not has_human:
        raise ValueError("任何含 Publisher 的工作流模板必须包含 human_approval 节点")

    tmpl = WorkflowTemplate(
        id=tmpl_id,
        name=name,
        description=description,
        source_preset=source_preset,
        version=1,
        status="DRAFT",
        owner=owner,
        nodes=parsed_nodes,
        created_at=now,
        updated_at=now,
    )
    _template_db[tmpl_id] = tmpl
    return tmpl


def get_template(template_id: str) -> Optional[WorkflowTemplate]:
    return _template_db.get(template_id)


def list_templates(
    status: Optional[str] = None,
    source_preset: Optional[str] = None,
) -> List[WorkflowTemplate]:
    results = list(_template_db.values())
    if status:
        results = [t for t in results if t.status == status]
    if source_preset:
        results = [t for t in results if t.source_preset == source_preset]
    return results


def update_template(template_id: str, **kwargs) -> Optional[WorkflowTemplate]:
    tmpl = _template_db.get(template_id)
    if not tmpl:
        return None
    for key, value in kwargs.items():
        if hasattr(tmpl, key):
            setattr(tmpl, key, value)
    tmpl.updated_at = _now()
    return tmpl


def delete_template(template_id: str) -> bool:
    return _template_db.pop(template_id, None) is not None


def load_presets():
    """Load system preset templates into the database.

    P8-4: 优先从外部 YAML 加载，失败时回退到内联定义（向后兼容）。
    """
    try:
        from src.core.template_loader import load_all_templates
        external = load_all_templates()
        if external:
            _template_db.update(external)
            print(f"[workflow_engine] Loaded {len(external)} templates from YAML files")
            return
    except Exception as exc:
        print(f"[workflow_engine] External template load failed, falling back to inline: {exc}")

    # Fallback: inline presets (backward compatibility)
    for preset in [
        CONTENT_CREATION_STANDARD,
        CONTENT_CREATION_LIGHT,
        TREND_SCOUT_ONLY,
        DATA_ANALYSIS_ONLY,
        CONTENT_CREATION_NOTE_IMAGE,
        CONTENT_CREATION_VIDEO_CLONE,
        CONTENT_CREATION_VIDEO_ORIGINAL,
        CONTENT_CREATION_TEXT_ARTICLE,
    ]:
        preset.created_at = _now()
        preset.updated_at = _now()
        _template_db[preset.id] = preset


def reload_presets() -> int:
    """Hot-reload templates from external YAML files."""
    try:
        from src.core.template_loader import load_all_templates
        external = load_all_templates()
        for tid, tmpl in external.items():
            _template_db[tid] = tmpl
        return len(external)
    except Exception as exc:
        print(f"[workflow_engine] Hot-reload failed: {exc}")
        return 0


# ─── Execution Engine ───

def start_execution(
    task_id: str,
    template_id: str,
    prompt_variables: Optional[Dict[str, Any]] = None,
) -> WorkflowExecution:
    tmpl = _template_db.get(template_id)
    if not tmpl:
        raise ValueError(f"Template not found: {template_id}")

    exec_id = _new_id("exec")
    now = _now()
    execution = WorkflowExecution(
        id=exec_id,
        task_id=task_id,
        template_id=template_id,
        template_version=tmpl.version,
        status=WorkflowStatus.RUNNING,
        current_node_index=0,
        context=dict(prompt_variables or {}),
        started_at=now,
        created_at=now,
    )
    _execution_db[exec_id] = execution
    return execution


def _get_node_by_index(tmpl: WorkflowTemplate, node_index: int) -> Optional[WorkflowNode]:
    """按 node_index 查找节点（兼容 node_index 不连续的模板）."""
    for n in tmpl.nodes:
        if n.node_index == node_index:
            return n
    return None


def _run_brand_knowledge_inject(context: Dict[str, Any]) -> Dict[str, Any]:
    """品牌知识注入 Skill（MVP：静态返回，生产环境应从 BrandKnowledge 服务读取）."""
    return {
        "brand_voice": "专业、温暖、可信赖",
        "brand_keywords": ["科学养宠", "宠物健康"],
        "brand_knowledge_injected": True,
    }


def _run_skill_node(node: WorkflowNode, context: Dict[str, Any]) -> Dict[str, Any]:
    """执行 SKILL 类型节点，返回输出."""
    if node.skill_id == "keyword_inject":
        from src.skills import keyword_inject

        return keyword_inject.execute(context)
    if node.skill_id == "brand_knowledge_inject":
        return _run_brand_knowledge_inject(context)
    # 预留：其他 skill 路由
    return {"skill_output": f"skill {node.skill_id} not implemented"}


def execute_next_node(
    execution_id: str,
    node_output: Optional[Dict[str, Any]] = None,
    node_error: Optional[str] = None,
) -> Dict[str, Any]:
    """Execute the next node in the workflow. Returns execution state.

    v4.0 增强：
    - DAG 拓扑序调度（支持并行层级编译，执行仍单步推进）
    - SKILL 节点自动路由
    - Checkpoint 保存（best-effort，不阻塞）
    """
    execution = _execution_db.get(execution_id)
    if not execution:
        raise ValueError(f"Execution not found: {execution_id}")

    if execution.status not in (WorkflowStatus.RUNNING, WorkflowStatus.PENDING):
        return {"status": execution.status.value, "done": True}

    tmpl = _template_db.get(execution.template_id)
    if not tmpl:
        raise ValueError(f"Template not found: {execution.template_id}")

    # 编译 DAG
    dag = compile_dag(tmpl.nodes)

    # 若所有节点已完成，标记 COMPLETED
    completed_set = set(execution.completed_nodes)
    failed_set = set(execution.failed_nodes)
    done_set = completed_set | failed_set
    if len(done_set) >= len(tmpl.nodes):
        execution.status = WorkflowStatus.COMPLETED
        execution.ended_at = _now()
        return {"status": execution.status.value, "done": True}

    # 确定当前要执行的节点
    current_idx = execution.current_node_index
    if current_idx in done_set:
        next_idx = _find_next_executable_node(dag, execution)
        if next_idx is None:
            execution.status = WorkflowStatus.COMPLETED
            execution.ended_at = _now()
            return {"status": execution.status.value, "done": True}
        execution.current_node_index = next_idx
        current_idx = next_idx

    node = _get_node_by_index(tmpl, current_idx)
    if node is None:
        raise ValueError(f"Node index {current_idx} not found in template")

    now = _now()

    # Record node execution
    node_exec = NodeExecution(
        id=_new_id("node"),
        execution_id=execution_id,
        node_index=node.node_index,
        node_type=node.node_type.value,
        status=ExecutionStatus.RUNNING,
        input_context=dict(execution.context),
        started_at=now,
        created_at=now,
    )
    _node_execution_db.append(node_exec)

    # ── Execute node ──
    success = node_error is None
    output = node_output or {}

    if success and node.node_type == NodeType.SKILL:
        try:
            output = _run_skill_node(node, execution.context)
        except Exception as exc:
            success = False
            node_error = str(exc)

    if success:
        node_exec.status = ExecutionStatus.SUCCESS
        node_exec.output_context = output
        execution.context.update(output)
        execution.completed_nodes.append(node.node_index)
    else:
        node_exec.status = ExecutionStatus.FAILED
        node_exec.error_message = node_error
        execution.failed_nodes.append(node.node_index)

    node_exec.ended_at = _now()
    if node_exec.started_at:
        started = datetime.fromisoformat(node_exec.started_at)
        ended = datetime.fromisoformat(node_exec.ended_at)
        node_exec.duration_ms = int((ended - started).total_seconds() * 1000)

    # ── Checkpoint（best-effort）──
    mgr = _get_checkpoint_mgr()
    if mgr is not None:
        try:
            mgr.save_sync(
                execution_id=execution_id,
                node_id=str(node.node_index),
                input_data=dict(node_exec.input_context),
                output_data=dict(node_exec.output_context),
                status=node_exec.status.value,
                started_at=node_exec.started_at,
                completed_at=node_exec.ended_at,
                latency_ms=node_exec.duration_ms,
            )
        except Exception:
            pass  # Checkpoint 失败不阻塞主流程

    # ── Handle failure strategy ──
    if not success:
        if node.fail_strategy == FailStrategy.FAIL_FAST:
            execution.status = WorkflowStatus.FAILED
            execution.ended_at = _now()
            return {"status": execution.status.value, "done": True, "node_failed": node.node_index}
        elif node.fail_strategy == FailStrategy.CONTINUE:
            # Continue to next node
            pass
        elif node.fail_strategy == FailStrategy.RETRY_THEN_FAIL:
            retry_key = f"_retry_count_{node.node_index}"
            retry_count = execution.context.get(retry_key, 0)
            if retry_count < 1:
                execution.context[retry_key] = retry_count + 1
                # 从 failed_nodes 中移除，允许重试
                if node.node_index in execution.failed_nodes:
                    execution.failed_nodes.remove(node.node_index)
                return {"status": execution.status.value, "done": False, "retrying": True, "node": node.node_index}
            else:
                execution.status = WorkflowStatus.FAILED
                execution.ended_at = _now()
                return {"status": execution.status.value, "done": True, "node_failed": node.node_index}

    # ── Advance to next node ──
    next_idx = _find_next_executable_node(dag, execution)
    if next_idx is None:
        execution.status = WorkflowStatus.COMPLETED
        execution.ended_at = _now()
        return {"status": execution.status.value, "done": True}

    execution.current_node_index = next_idx
    return {"status": execution.status.value, "done": False, "next_node": next_idx}


def pause_execution(execution_id: str) -> Optional[WorkflowExecution]:
    execution = _execution_db.get(execution_id)
    if not execution:
        return None
    execution.status = WorkflowStatus.PAUSED
    _audit_log(execution, "PAUSED", "人工暂停")
    return execution


def resume_execution(execution_id: str) -> Optional[WorkflowExecution]:
    """恢复执行：从 Checkpoint 重建状态（若存在 Checkpoint）."""
    execution = _execution_db.get(execution_id)
    if not execution:
        return None

    # 尝试从 Checkpoint 恢复
    mgr = _get_checkpoint_mgr()
    if mgr is not None:
        try:
            checkpoints = mgr.load_all_sync(execution_id)
            if checkpoints:
                # 重建 completed_nodes / failed_nodes / context
                execution.completed_nodes = []
                execution.failed_nodes = []
                execution.context = {}
                for cp in checkpoints:
                    if cp.node_status == "SUCCESS":
                        execution.completed_nodes.append(int(cp.node_id))
                        if cp.output_data:
                            execution.context.update(cp.output_data)
                    elif cp.node_status == "FAILED":
                        execution.failed_nodes.append(int(cp.node_id))

                # 找到下一个可执行节点
                tmpl = _template_db.get(execution.template_id)
                if tmpl:
                    dag = compile_dag(tmpl.nodes)
                    next_idx = _find_next_executable_node(dag, execution)
                    if next_idx is not None:
                        execution.current_node_index = next_idx
        except Exception:
            pass  # Checkpoint 恢复失败则保持原状态

    execution.status = WorkflowStatus.RUNNING
    execution.resumed_count += 1
    _audit_log(execution, "RESUMED", f"从断点恢复（第 {execution.resumed_count} 次）")
    return execution


def _audit_log(execution: WorkflowExecution, action: str, reason: str) -> None:
    """记录人工干预审计日志到 execution context."""
    log_key = "_audit_log"
    if log_key not in execution.context:
        execution.context[log_key] = []
    execution.context[log_key].append(
        {
            "action": action,
            "reason": reason,
            "timestamp": _now(),
            "resumed_count": execution.resumed_count,
        }
    )


def cancel_execution(execution_id: str) -> Optional[WorkflowExecution]:
    execution = _execution_db.get(execution_id)
    if not execution:
        return None
    execution.status = WorkflowStatus.CANCELLED
    execution.ended_at = _now()
    return execution


def get_execution(execution_id: str) -> Optional[WorkflowExecution]:
    return _execution_db.get(execution_id)


def delete_execution(execution_id: str) -> bool:
    """Delete a workflow execution and its node execution records."""
    if execution_id not in _execution_db:
        return False
    del _execution_db[execution_id]
    global _node_execution_db
    _node_execution_db = [n for n in _node_execution_db if n.execution_id != execution_id]
    return True


def list_executions(
    template_id: Optional[str] = None,
    status: Optional[str] = None,
) -> List[WorkflowExecution]:
    results = list(_execution_db.values())
    if template_id:
        results = [e for e in results if e.template_id == template_id]
    if status:
        results = [e for e in results if e.status.value == status]
    return results


def get_node_executions(execution_id: str) -> List[NodeExecution]:
    return [n for n in _node_execution_db if n.execution_id == execution_id]


# ─── Context Store (memory simulation of Redis workflow_context:{task_id}) ───

def get_context(execution_id: str) -> Dict[str, Any]:
    execution = _execution_db.get(execution_id)
    return execution.context if execution else {}


def set_context(execution_id: str, key: str, value: Any) -> None:
    execution = _execution_db.get(execution_id)
    if execution:
        execution.context[key] = value


# ─── Template Recommendation (Phase 3) ───

_TEMPLATE_RECOMMENDATIONS: Dict[str, str] = {
    "xiaohongshu-图文": "content_creation_note_image",
    "xiaohongshu-视频": "content_creation_video_original",
    "xiaohongshu-仅文字": "content_creation_text_article",
    "douyin-视频": "content_creation_video_clone",
    "douyin-视频复刻": "content_creation_video_clone",
    "wechat_channels-图文": "content_creation_text_article",
    "wechat_channels-视频": "content_creation_video_original",
    "bilibili-视频": "content_creation_video_original",
    "bilibili-视频复刻": "content_creation_video_clone",
}


def recommend_template(platform_id: str, content_format: str) -> Optional[WorkflowTemplate]:
    """Recommend a workflow template based on platform and content format."""
    key = f"{platform_id}-{content_format}"
    template_id = _TEMPLATE_RECOMMENDATIONS.get(key)
    if template_id:
        return _template_db.get(template_id)
    # Fallback: return standard template
    return _template_db.get("content_creation_standard")


# ─── W17: Template Version Management ───

def upgrade_template_version(template_id: str, change_reason: str = "") -> Optional[WorkflowTemplate]:
    """Archive current version and bump version number."""
    tmpl = _template_db.get(template_id)
    if not tmpl:
        return None

    # Archive current version
    if template_id not in _template_version_history:
        _template_version_history[template_id] = []
    # Create a shallow copy for history (MVP: just store reference with version)
    from copy import copy
    archived = copy(tmpl)
    _template_version_history[template_id].append(archived)

    # Bump version
    tmpl.version += 1
    tmpl.updated_at = _now()
    return tmpl


def get_template_versions(template_id: str) -> List[Dict[str, Any]]:
    """Get version history for a template."""
    history = _template_version_history.get(template_id, [])
    current = _template_db.get(template_id)
    versions = []
    for i, h in enumerate(history):
        versions.append({
            "version": h.version,
            "created_at": h.created_at,
            "updated_at": h.updated_at,
        })
    if current:
        versions.append({
            "version": current.version,
            "created_at": current.created_at,
            "updated_at": current.updated_at,
            "is_current": True,
        })
    return versions


# ─── W17: Dry Run ───

def dry_run_execution(template_id: str, initial_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Simulate workflow execution without side effects."""
    tmpl = _template_db.get(template_id)
    if not tmpl:
        raise ValueError(f"Template not found: {template_id}")

    simulated_nodes = []
    context = dict(initial_context or {})

    # Validate: publisher must have human_approval
    has_publisher = any(n.agent_id == "publisher" for n in tmpl.nodes if n.node_type == NodeType.AGENT)
    has_human = any(n.node_type == NodeType.HUMAN_APPROVAL for n in tmpl.nodes)
    validation_passed = not (has_publisher and not has_human)

    for i, node in enumerate(tmpl.nodes):
        simulated_nodes.append({
            "node_index": node.node_index,
            "node_type": node.node_type.value,
            "node_name": node.node_name,
            "status": "SIMULATED",
            "input_context": dict(context),
            "output_context": {"simulated": True, "node": node.node_name},
        })
        context[f"node_{i}_output"] = {"simulated": True}

    return {
        "is_dry_run": True,
        "template_id": template_id,
        "template_version": tmpl.version,
        "simulated_nodes": simulated_nodes,
        "overall_status": "SIMULATED",
        "final_context": context,
        "validation_passed": validation_passed,
        "has_human_approval": has_human,
    }


# ─── W17: React Flow Format ───

def to_react_flow(template_id: str) -> Dict[str, Any]:
    """Convert workflow template to React Flow node/edge format (DAG-aware)."""
    tmpl = _template_db.get(template_id)
    if not tmpl:
        raise ValueError(f"Template not found: {template_id}")

    dag = compile_dag(tmpl.nodes)

    # 按层级分配 x 坐标
    level_x: Dict[int, int] = {}
    for level_idx, level_nodes in enumerate(dag.levels):
        x = level_idx * 300
        for node_idx in level_nodes:
            level_x[node_idx] = x

    nodes = []
    for n in tmpl.nodes:
        x = level_x.get(n.node_index, n.node_index * 250)
        # 同层级节点在 y 方向分散
        level = next((i for i, lvl in enumerate(dag.levels) if n.node_index in lvl), 0)
        same_level = [idx for idx in dag.levels[level]] if level < len(dag.levels) else []
        y_offset = (same_level.index(n.node_index) * 120) if n.node_index in same_level else 0

        nodes.append({
            "id": f"node-{n.node_index}",
            "type": n.node_type.value.lower(),
            "position": {"x": x, "y": 100 + y_offset},
            "data": {
                "label": n.node_name,
                "agent_id": n.agent_id,
                "skill_id": n.skill_id,
                "human_config": n.human_config,
                "fail_strategy": n.fail_strategy.value,
                "depends_on": n.depends_on,
            },
        })

    edges = []
    edge_id = 0
    for src, targets in dag.adjacency.items():
        for tgt in targets:
            edges.append({
                "id": f"edge-{edge_id}",
                "source": f"node-{src}",
                "target": f"node-{tgt}",
                "type": "smoothstep",
            })
            edge_id += 1

    return {"nodes": nodes, "edges": edges}


# ─── Clear stores (for testing) ───

def _clear_stores():
    _template_db.clear()
    _template_version_history.clear()
    _execution_db.clear()
    _node_execution_db.clear()
