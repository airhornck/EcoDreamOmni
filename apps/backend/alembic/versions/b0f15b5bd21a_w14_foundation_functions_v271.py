"""w14_foundation_functions_v271

Revision ID: b0f15b5bd21a
Revises: 95251adaaa3e
Create Date: 2026-05-19 22:32:56.176375

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# pgvector extension will be created manually by DBA; here we just use the type.
# If the extension is missing, run: CREATE EXTENSION IF NOT EXISTS vector;

# revision identifiers, used by Alembic.
revision: str = 'b0f15b5bd21a'
down_revision: Union[str, Sequence[str], None] = '95251adaaa3e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema — W14 Foundation Function层五大数据真源表."""

    # ── 1. AssetPool ──
    op.create_table(
        'assets',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('file_url', sa.Text(), nullable=False),
        sa.Column('thumbnail_url', sa.Text(), nullable=True),
        sa.Column('source_type', sa.String(20), nullable=False, server_default='OPERATOR_UPLOAD'),
        sa.Column('license_type', sa.String(20), nullable=False, server_default='OWNED'),
        sa.Column('license_status', sa.String(20), nullable=False, server_default='VALID'),
        sa.Column('copyright_holder', sa.String(255), nullable=True),
        sa.Column('copyright_year', sa.Integer(), nullable=True),
        sa.Column('usage_rights', postgresql.JSONB(), server_default='[]'),
        sa.Column('copyright_validated', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('license_ref', sa.Text(), nullable=True),
        sa.Column('stock_source', sa.String(50), nullable=True),
        sa.Column('stock_id', sa.String(100), nullable=True),
        sa.Column('license_expiry', sa.DateTime(timezone=True), nullable=True),
        sa.Column('ai_model', sa.String(100), nullable=True),
        sa.Column('ai_prompt', sa.Text(), nullable=True),
        sa.Column('ai_disclosure', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('ai_metadata', postgresql.JSONB(), nullable=True),
        sa.Column('category', sa.String(50), nullable=True),
        sa.Column('tags', postgresql.JSONB(), server_default='[]'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('series_id', sa.String(32), nullable=True, index=True),
        sa.Column('brand_knowledge_id', sa.String(32), nullable=True, index=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='ACTIVE'),
        sa.Column('meta_width', sa.Integer(), nullable=True),
        sa.Column('meta_height', sa.Integer(), nullable=True),
        sa.Column('meta_file_size', sa.Integer(), nullable=True),
        sa.Column('meta_mime_type', sa.String(50), nullable=True),
        sa.Column('meta_dominant_color', sa.String(20), nullable=True),
        sa.Column('uploaded_by', sa.String(100), nullable=True),
        sa.Column('tenant_id', sa.String(64), nullable=True, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        comment='AssetPool — PRD V3.1 §AssetPool',
    )
    op.create_index('ix_assets_tenant_status', 'assets', ['tenant_id', 'status'])
    op.create_index('ix_assets_source_category', 'assets', ['source_type', 'category'])

    # ── 2. BrandKnowledge ──
    op.create_table(
        'brand_knowledge_entries',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('entry_type', sa.String(50), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('product_id', sa.String(32), nullable=True, index=True),
        sa.Column('approval_number', sa.String(50), nullable=True, index=True),
        sa.Column('sku_code', sa.String(100), nullable=True),
        sa.Column('brand_name', sa.String(100), nullable=True, index=True),
        sa.Column('prohibited_claims', postgresql.JSONB(), server_default='[]'),
        sa.Column('required_disclaimers', postgresql.JSONB(), server_default='[]'),
        sa.Column('embedding', sa.Text(), nullable=True),  # Will be altered to VECTOR(1536) below
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('is_latest', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('parent_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('brand_knowledge_entries.id', ondelete='SET NULL'), nullable=True),
        sa.Column('asset_ids', postgresql.JSONB(), server_default='[]'),
        sa.Column('created_by', sa.String(100), nullable=False),
        sa.Column('updated_by', sa.String(100), nullable=True),
        sa.Column('change_reason', sa.Text(), nullable=True),
        sa.Column('tenant_id', sa.String(64), nullable=True, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        comment='BrandKnowledge — PRD V3.1 §BrandKnowledge',
    )
    op.create_index('ix_bk_tenant_type', 'brand_knowledge_entries', ['tenant_id', 'entry_type'])
    op.create_index('ix_bk_brand_latest', 'brand_knowledge_entries', ['brand_name', 'is_latest'])
    # Add pgvector extension and alter embedding column
    op.execute(sa.text("CREATE EXTENSION IF NOT EXISTS vector"))
    op.execute(sa.text("ALTER TABLE brand_knowledge_entries ALTER COLUMN embedding TYPE vector(1536) USING NULL"))

    # ── 3. VetDrugDB ──
    op.create_table(
        'vet_drug_entries',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('approval_number', sa.String(50), nullable=False, unique=True, index=True),
        sa.Column('product_name', sa.String(255), nullable=False, index=True),
        sa.Column('generic_name', sa.String(255), nullable=True),
        sa.Column('english_name', sa.String(255), nullable=True),
        sa.Column('manufacturer', sa.String(255), nullable=True),
        sa.Column('manufacturer_address', sa.Text(), nullable=True),
        sa.Column('ingredients', sa.Text(), nullable=True),
        sa.Column('specifications', sa.Text(), nullable=True),
        sa.Column('indications', sa.Text(), nullable=True),
        sa.Column('usage_dosage', sa.Text(), nullable=True),
        sa.Column('contraindications', sa.Text(), nullable=True),
        sa.Column('adverse_reactions', sa.Text(), nullable=True),
        sa.Column('precautions', sa.Text(), nullable=True),
        sa.Column('drug_interactions', sa.Text(), nullable=True),
        sa.Column('storage_conditions', sa.Text(), nullable=True),
        sa.Column('category', sa.String(50), nullable=True),
        sa.Column('drug_type', sa.String(50), nullable=True),
        sa.Column('issue_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expiry_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='ACTIVE'),
        sa.Column('applicable_species', postgresql.JSONB(), server_default='[]'),
        sa.Column('target_diseases', postgresql.JSONB(), server_default='[]'),
        sa.Column('tags', postgresql.JSONB(), server_default='[]'),
        sa.Column('brand_knowledge_id', sa.String(32), nullable=True, index=True),
        sa.Column('created_by', sa.String(100), nullable=True),
        sa.Column('updated_by', sa.String(100), nullable=True),
        sa.Column('data_source', sa.String(50), nullable=True, server_default='manual'),
        sa.Column('tenant_id', sa.String(64), nullable=True, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        comment='VetDrugDB — PRD V3.1 §VetDrugDB',
    )
    op.create_index('ix_vd_tenant_status', 'vet_drug_entries', ['tenant_id', 'status'])
    op.create_index('ix_vd_expiry', 'vet_drug_entries', ['expiry_date', 'status'])

    # ── 4. TimelineLibrary ──
    op.create_table(
        'timeline_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('start_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('recurring', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('cron_expression', sa.String(100), nullable=True),
        sa.Column('year', sa.Integer(), nullable=True),
        sa.Column('brand_knowledge_ids', postgresql.JSONB(), server_default='[]'),
        sa.Column('product_ids', postgresql.JSONB(), server_default='[]'),
        sa.Column('prohibited_claims', postgresql.JSONB(), server_default='[]'),
        sa.Column('is_commercial', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('status', sa.String(20), nullable=False, server_default='ACTIVE'),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('color_code', sa.String(20), nullable=True),
        sa.Column('created_by', sa.String(100), nullable=True),
        sa.Column('tenant_id', sa.String(64), nullable=True, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        comment='TimelineLibrary — PRD V3.1 §TimelineLibrary',
    )
    op.create_index('ix_te_tenant_dates', 'timeline_events', ['tenant_id', 'start_date', 'end_date'])
    op.create_index('ix_te_type_dates', 'timeline_events', ['event_type', 'start_date'])

    # ── 5. PlatformRule ──
    op.create_table(
        'platform_rules',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('platform', sa.String(20), nullable=False, server_default='xiaohongshu'),
        sa.Column('layer', sa.String(10), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('condition_json', postgresql.JSONB(), nullable=False),
        sa.Column('action', sa.String(20), nullable=False, server_default='warn'),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('effective_from', sa.DateTime(timezone=True), nullable=False),
        sa.Column('effective_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('applicable_lifecycle', postgresql.JSONB(), server_default='[]'),
        sa.Column('created_by', sa.String(100), nullable=False),
        sa.Column('updated_by', sa.String(100), nullable=True),
        sa.Column('tenant_id', sa.String(64), nullable=True, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        comment='PlatformRule — PRD V3.1 §PlatformRule',
    )
    op.create_index('ix_pr_platform_layer', 'platform_rules', ['platform', 'layer'])
    op.create_index('ix_pr_platform_enabled', 'platform_rules', ['platform', 'enabled'])

    op.create_table(
        'platform_rule_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('rule_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('platform_rules.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('platform', sa.String(20), nullable=False),
        sa.Column('layer', sa.String(10), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('condition_json', postgresql.JSONB(), nullable=False),
        sa.Column('action', sa.String(20), nullable=False),
        sa.Column('priority', sa.Integer(), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('effective_from', sa.DateTime(timezone=True), nullable=False),
        sa.Column('change_reason', sa.Text(), nullable=True),
        sa.Column('changed_by', sa.String(100), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        comment='PlatformRule版本历史',
    )
    op.create_index('ix_prh_rule_version', 'platform_rule_history', ['rule_id', 'version'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_prh_rule_version', table_name='platform_rule_history')
    op.drop_table('platform_rule_history')
    op.drop_index('ix_pr_platform_enabled', table_name='platform_rules')
    op.drop_index('ix_pr_platform_layer', table_name='platform_rules')
    op.drop_table('platform_rules')
    op.drop_index('ix_te_type_dates', table_name='timeline_events')
    op.drop_index('ix_te_tenant_dates', table_name='timeline_events')
    op.drop_table('timeline_events')
    op.drop_index('ix_vd_expiry', table_name='vet_drug_entries')
    op.drop_index('ix_vd_tenant_status', table_name='vet_drug_entries')
    op.drop_table('vet_drug_entries')
    op.drop_index('ix_bk_brand_latest', table_name='brand_knowledge_entries')
    op.drop_index('ix_bk_tenant_type', table_name='brand_knowledge_entries')
    op.drop_table('brand_knowledge_entries')
    op.drop_index('ix_assets_source_category', table_name='assets')
    op.drop_index('ix_assets_tenant_status', table_name='assets')
    op.drop_table('assets')
