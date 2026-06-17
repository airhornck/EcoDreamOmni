"""Update xiaohongshu image agent config snapshot.

Revision ID: i4j5k6l7m8n9
Revises: 15669e238e9d
Create Date: 2026-06-14 12:00:00.000000+00:00
"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "i4j5k6l7m8n9"
down_revision: Union[str, None] = "15669e238e9d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Inject platform format snapshot and safety injection config for xhs image agent."""
    op.execute("""
        UPDATE agents
        SET config = '{
            "default_workflow_template_id": "content_creation_note_image",
            "workflow_version": 2,
            "platform_format_snapshot": {
                "platform_id": "xiaohongshu",
                "format_name": "图文",
                "title_constraints": {
                    "max_length": 20,
                    "recommended": "15-20字",
                    "recommended_patterns": ["数字+痛点", "场景+解决方案", "对比+结论"]
                },
                "body_constraints": {
                    "max_length": 1000,
                    "recommended": "300-800字",
                    "max_paragraphs": 15,
                    "max_emojis": 20,
                    "line_break_style": "loose"
                },
                "tag_constraints": {
                    "max_count": 10,
                    "max_length_per_tag": 20
                },
                "cover_constraints": {
                    "aspect_ratio": "3:4",
                    "min_width": 720,
                    "min_height": 960,
                    "recommended_per_post": "6-9",
                    "max_images_per_post": 18
                }
            },
            "safety_injection": {
                "pre_check_agents": ["vetdrug-validate"],
                "post_check_agents": ["compliance-guard"],
                "rule_layers": ["l1_static", "l2_keyword"],
                "required_disclaimers": ["本品不能替代药品"]
            }
        }'::jsonb
        WHERE id = 'content_forge_xhs_image';
    """)


def downgrade() -> None:
    """Restore the previous minimal config for xhs image agent."""
    op.execute("""
        UPDATE agents
        SET config = '{
            "default_workflow_template_id": "content_creation_note_image",
            "workflow_version": 1
        }'::jsonb
        WHERE id = 'content_forge_xhs_image';
    """)
