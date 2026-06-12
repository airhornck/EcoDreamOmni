"""Add skill_definitions table — P8-5.

Revision ID: f1a2b3c4d5e6
Revises: 120d8c25393c
Create Date: 2026-06-03 08:30:00.000000+00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "f1a2b3c4d5e6"
down_revision: Union[str, None] = "120d8c25393c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "skill_definitions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", sa.String(64), nullable=False, index=True, server_default="system"),
        sa.Column("skill_id", sa.String(128), nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("version", sa.String(32), nullable=False, server_default="1.0.0"),
        sa.Column("level", sa.String(10), nullable=False, server_default="L2"),
        sa.Column("input_schema", sa.JSON, server_default=sa.text("'{}'")),
        sa.Column("output_schema", sa.JSON, server_default=sa.text("'{}'")),
        sa.Column("modality_support", sa.JSON, server_default=sa.text("'{}'")),
        sa.Column("requires_llm", sa.Boolean, server_default=sa.text("false")),
        sa.Column("llm_model_preference", sa.String(64), server_default=""),
        sa.Column("required_functions", sa.JSON, server_default=sa.text("'[]'")),
        sa.Column("permissions", sa.JSON, server_default=sa.text("'{}'")),
        sa.Column("code_path", sa.String(500), nullable=True),
        sa.Column("meta", sa.JSON, server_default=sa.text("'{}'")),
        sa.Column("status", sa.String(32), server_default="active"),
        sa.Column("success_rate_7d", sa.Integer, server_default=sa.text("0")),
        sa.Column("avg_latency_ms", sa.Integer, server_default=sa.text("0")),
        sa.Column("avg_token_cost", sa.Integer, server_default=sa.text("0")),
        sa.Column("human_intervention_rate", sa.Integer, server_default=sa.text("0")),
        sa.Column("created_by", sa.String(255), nullable=False, server_default="system"),
        sa.Column("updated_by", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), onupdate=sa.text("now()")),
        sa.Index("ix_sd_tenant_status", "tenant_id", "status"),
        sa.Index("ix_sd_skill_id", "skill_id", "version"),
        comment="SkillDefinition — PRD v4.0 §4.2",
    )


def downgrade() -> None:
    op.drop_table("skill_definitions")
