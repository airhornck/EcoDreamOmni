"""migrate_content_templates_to_strategy_elements

Revision ID: 8eae2f4c39a9
Revises: bfbe979f6f73
Create Date: 2026-06-06 08:09:04.322567

"""
from typing import Sequence, Union
import uuid
import json
from datetime import datetime, timezone

from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm import Session

# revision identifiers, used by Alembic.
revision: str = '8eae2f4c39a9'
down_revision: Union[str, Sequence[str], None] = 'bfbe979f6f73'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _se_id() -> str:
    return f"se_{uuid.uuid4().hex[:16]}"


def _ss_id() -> str:
    return f"ss_{uuid.uuid4().hex[:16]}"


def upgrade() -> None:
    """Migrate ContentTemplate records into StrategyElements + StrategySets.

    Each ContentTemplate is decomposed into:
      - 1 structure_framework element (from extracted_structure)
      - 1 hook_pattern element (if hook exists)
      - 1 body_structure element (if body exists)
      - 1 cta_pattern element (if CTA exists)
      - 1 custom_fragment element (from prompt_template)
      - 1 strategy_set referencing all of the above
    """
    bind = op.get_bind()
    session = Session(bind=bind)

    # Fetch all active content_templates
    rows = session.execute(
        sa.text("""
            SELECT template_id, tenant_id, source_platform_id, source,
                   extracted_structure, prompt_template, variables,
                   engagement_benchmark, created_by, created_at, updated_at,
                   platform_content_type_style_id
            FROM content_templates
            WHERE status = 'active'
        """)
    ).fetchall()

    for row in rows:
        template_id = row.template_id
        tenant_id = row.tenant_id
        platform = row.source_platform_id or "xhs"
        source = row.source
        created_by = row.created_by
        created_at = row.created_at or _now()
        updated_at = row.updated_at or _now()
        extracted = row.extracted_structure or {}
        prompt_tmpl = row.prompt_template or ""
        variables = row.variables or []
        engagement = row.engagement_benchmark or {}
        style_id = row.platform_content_type_style_id

        element_refs = []
        priority = 10

        # 1. structure_framework
        structure = extracted.get("structure") or extracted.get("structure_framework")
        if structure:
            se_id = _se_id()
            session.execute(
                sa.text("""
                    INSERT INTO strategy_elements (
                        element_id, tenant_id, element_type, name, description, content,
                        render_template, variables, source, source_content_id,
                        platform, content_format, usage_count, avg_engagement,
                        effectiveness_score, status, created_by, created_at, updated_at
                    ) VALUES (
                        :eid, :tenant_id, 'structure_framework', :name, :desc, :content,
                        :render_tmpl, :vars, :source, :source_id,
                        :platform, :fmt, 0, :engagement,
                        :score, 'active', :created_by, :created_at, :updated_at
                    )
                """),
                {
                    "eid": se_id,
                    "tenant_id": tenant_id,
                    "name": f"结构框架 ({template_id})",
                    "desc": f"从模板 {template_id} 提取的结构框架",
                    "content": {"structure": structure},
                    "render_tmpl": "【结构框架】\n{{ structure | default('') }}\n",
                    "vars": "[]",
                    "source": source,
                    "source_id": template_id,
                    "platform": platform,
                    "fmt": None,
                    "engagement": json.dumps(engagement) if engagement else "{}",
                    "score": 0.7,
                    "created_by": created_by,
                    "created_at": created_at,
                    "updated_at": updated_at,
                },
            )
            element_refs.append({
                "element_id": se_id,
                "priority": priority,
                "override_variables": {},
            })
            priority -= 1

        # 2. hook_pattern
        hook = extracted.get("hook_pattern") or extracted.get("hook")
        if hook:
            se_id = _se_id()
            session.execute(
                sa.text("""
                    INSERT INTO strategy_elements (
                        element_id, tenant_id, element_type, name, description, content,
                        render_template, variables, source, source_content_id,
                        platform, content_format, usage_count, avg_engagement,
                        effectiveness_score, status, created_by, created_at, updated_at
                    ) VALUES (
                        :eid, :tenant_id, 'hook_pattern', :name, :desc, :content,
                        :render_tmpl, :vars, :source, :source_id,
                        :platform, :fmt, 0, :engagement,
                        :score, 'active', :created_by, :created_at, :updated_at
                    )
                """),
                {
                    "eid": se_id,
                    "tenant_id": tenant_id,
                    "name": f"Hook模式 ({template_id})",
                    "desc": f"从模板 {template_id} 提取的 Hook 模式",
                    "content": {"hook": hook},
                    "render_tmpl": "【开头 Hook】\n{{ hook | default('') }}\n",
                    "vars": "[]",
                    "source": source,
                    "source_id": template_id,
                    "platform": platform,
                    "fmt": None,
                    "engagement": json.dumps(engagement) if engagement else "{}",
                    "score": 0.7,
                    "created_by": created_by,
                    "created_at": created_at,
                    "updated_at": updated_at,
                },
            )
            element_refs.append({
                "element_id": se_id,
                "priority": priority,
                "override_variables": {},
            })
            priority -= 1

        # 3. body_structure
        body = extracted.get("body_structure") or extracted.get("body")
        if body:
            se_id = _se_id()
            session.execute(
                sa.text("""
                    INSERT INTO strategy_elements (
                        element_id, tenant_id, element_type, name, description, content,
                        render_template, variables, source, source_content_id,
                        platform, content_format, usage_count, avg_engagement,
                        effectiveness_score, status, created_by, created_at, updated_at
                    ) VALUES (
                        :eid, :tenant_id, 'body_structure', :name, :desc, :content,
                        :render_tmpl, :vars, :source, :source_id,
                        :platform, :fmt, 0, :engagement,
                        :score, 'active', :created_by, :created_at, :updated_at
                    )
                """),
                {
                    "eid": se_id,
                    "tenant_id": tenant_id,
                    "name": f"正文结构 ({template_id})",
                    "desc": f"从模板 {template_id} 提取的正文结构",
                    "content": {"body": body},
                    "render_tmpl": "【正文结构】\n{{ body | default('') }}\n",
                    "vars": "[]",
                    "source": source,
                    "source_id": template_id,
                    "platform": platform,
                    "fmt": None,
                    "engagement": json.dumps(engagement) if engagement else "{}",
                    "score": 0.7,
                    "created_by": created_by,
                    "created_at": created_at,
                    "updated_at": updated_at,
                },
            )
            element_refs.append({
                "element_id": se_id,
                "priority": priority,
                "override_variables": {},
            })
            priority -= 1

        # 4. cta_pattern
        cta = extracted.get("cta_pattern") or extracted.get("cta")
        if cta:
            se_id = _se_id()
            session.execute(
                sa.text("""
                    INSERT INTO strategy_elements (
                        element_id, tenant_id, element_type, name, description, content,
                        render_template, variables, source, source_content_id,
                        platform, content_format, usage_count, avg_engagement,
                        effectiveness_score, status, created_by, created_at, updated_at
                    ) VALUES (
                        :eid, :tenant_id, 'cta_pattern', :name, :desc, :content,
                        :render_tmpl, :vars, :source, :source_id,
                        :platform, :fmt, 0, :engagement,
                        :score, 'active', :created_by, :created_at, :updated_at
                    )
                """),
                {
                    "eid": se_id,
                    "tenant_id": tenant_id,
                    "name": f"CTA模式 ({template_id})",
                    "desc": f"从模板 {template_id} 提取的 CTA 模式",
                    "content": {"cta": cta},
                    "render_tmpl": "【CTA】\n{{ cta | default('') }}\n",
                    "vars": "[]",
                    "source": source,
                    "source_id": template_id,
                    "platform": platform,
                    "fmt": None,
                    "engagement": json.dumps(engagement) if engagement else "{}",
                    "score": 0.7,
                    "created_by": created_by,
                    "created_at": created_at,
                    "updated_at": updated_at,
                },
            )
            element_refs.append({
                "element_id": se_id,
                "priority": priority,
                "override_variables": {},
            })
            priority -= 1

        # 5. custom_fragment from prompt_template
        if prompt_tmpl:
            se_id = _se_id()
            session.execute(
                sa.text("""
                    INSERT INTO strategy_elements (
                        element_id, tenant_id, element_type, name, description, content,
                        render_template, variables, source, source_content_id,
                        platform, content_format, usage_count, avg_engagement,
                        effectiveness_score, status, created_by, created_at, updated_at
                    ) VALUES (
                        :eid, :tenant_id, 'custom_fragment', :name, :desc, :content,
                        :render_tmpl, :vars, :source, :source_id,
                        :platform, :fmt, 0, :engagement,
                        :score, 'active', :created_by, :created_at, :updated_at
                    )
                """),
                {
                    "eid": se_id,
                    "tenant_id": tenant_id,
                    "name": f"自定义片段 ({template_id})",
                    "desc": f"从模板 {template_id} 迁移的 Prompt 模板片段",
                    "content": {"template": prompt_tmpl},
                    "render_tmpl": prompt_tmpl,
                    "vars": json.dumps(variables) if variables else "[]",
                    "source": source,
                    "source_id": template_id,
                    "platform": platform,
                    "fmt": None,
                    "engagement": json.dumps(engagement) if engagement else "{}",
                    "score": 0.5,
                    "created_by": created_by,
                    "created_at": created_at,
                    "updated_at": updated_at,
                },
            )
            element_refs.append({
                "element_id": se_id,
                "priority": priority,
                "override_variables": {},
            })
            priority -= 1

        # 6. Create StrategySet
        if element_refs:
            ss_id = _ss_id()
            session.execute(
                sa.text("""
                    INSERT INTO strategy_sets (
                        set_id, tenant_id, name, description, element_refs,
                        default_variables, source, source_content_id,
                        platform, content_format, usage_count, avg_engagement,
                        status, created_by, created_at, updated_at
                    ) VALUES (
                        :sid, :tenant_id, :name, :desc, :refs,
                        :vars, :source, :source_id,
                        :platform, :fmt, 0, :engagement,
                        'active', :created_by, :created_at, :updated_at
                    )
                """),
                {
                    "sid": ss_id,
                    "tenant_id": tenant_id,
                    "name": f"模板迁移: {template_id}",
                    "desc": f"从 ContentTemplate {template_id} 自动迁移生成的策略组合",
                    "refs": json.dumps(element_refs) if element_refs else "[]",
                    "vars": "{}",
                    "source": "system" if source == "manual" else source,
                    "source_id": template_id,
                    "platform": platform,
                    "fmt": None,
                    "engagement": json.dumps(engagement) if engagement else "{}",
                    "created_by": created_by,
                    "created_at": created_at,
                    "updated_at": updated_at,
                },
            )

    # Mark migrated content_templates as deprecated
    session.execute(
        sa.text("UPDATE content_templates SET status = 'deprecated' WHERE status = 'active'")
    )

    session.commit()


def downgrade() -> None:
    """Downgrade is not supported for data migrations."""
    pass
