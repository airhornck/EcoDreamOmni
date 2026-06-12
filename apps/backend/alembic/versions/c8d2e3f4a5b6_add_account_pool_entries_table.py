"""add_account_pool_entries_table

Revision ID: c8d2e3f4a5b6
Revises: 56fffc66dda5
Create Date: 2026-05-31 23:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c8d2e3f4a5b6'
down_revision: Union[str, Sequence[str], None] = '56fffc66dda5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema — AccountPool persistent storage."""

    op.create_table(
        'account_pool_entries',
        sa.Column('id', sa.String(64), primary_key=True, comment='账号池条目ID'),
        sa.Column('platform', sa.String(16), nullable=False, comment='平台: xhs | douyin | wechat_channels'),
        sa.Column('account_id', sa.String(64), nullable=False, comment='平台账号ID'),
        sa.Column('nickname', sa.String(128), nullable=False, comment='显示昵称'),
        sa.Column('cookie_encrypted', sa.String(2048), nullable=False, comment='AES-256-GCM加密后的Cookie'),
        sa.Column('persona', sa.String(64), nullable=False, comment='关联PersonaID'),
        sa.Column('content_vertical', sa.String(64), nullable=False, comment='内容垂类'),
        sa.Column('lifecycle_phase', sa.String(32), nullable=False, comment='生命周期: cold_start | growth | mature | dormant'),
        sa.Column('fingerprint_profile', postgresql.JSONB(), server_default='{}', comment='浏览器指纹配置'),
        sa.Column('proxy_config', postgresql.JSONB(), nullable=True, comment='代理配置 {proxy_id, type, region}'),
        sa.Column('health_score', sa.Float(), nullable=False, server_default='100.0', comment='健康分 0-100'),
        sa.Column('posts_today', sa.Integer(), nullable=False, server_default='0', comment='今日发布数'),
        sa.Column('posts_week', sa.Integer(), nullable=False, server_default='0', comment='本周发布数'),
        sa.Column('posts_month', sa.Integer(), nullable=False, server_default='0', comment='本月发布数'),
        sa.Column('violation_count', sa.Integer(), nullable=False, server_default='0', comment='违规次数'),
        sa.Column('last_login_days', sa.Integer(), nullable=False, server_default='0', comment='距上次登录天数'),
        sa.Column('status', sa.String(32), nullable=False, server_default='active', comment='active | warming | blocked | expired'),
        sa.Column('anomaly_flags', postgresql.JSONB(), server_default='[]', comment='异常标记列表'),
        sa.Column('daily_quota', sa.Integer(), nullable=False, server_default='0', comment='每日配额'),
        sa.Column('last_post_reset', sa.String(16), nullable=True, comment='上次配额重置日期 ISO'),
        sa.Column('auto_engagement_fetch', sa.Boolean(), nullable=False, server_default='false', comment='自动抓取互动数据'),
        sa.Column('engagement_fetches_today', sa.Integer(), nullable=False, server_default='0', comment='今日抓取次数'),
        sa.Column('last_engagement_fetch_reset', sa.String(16), nullable=True, comment='上次抓取重置日期 ISO'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        comment='AccountPool — persistent account entries',
    )
    op.create_index('ix_ap_entries_platform', 'account_pool_entries', ['platform'])
    op.create_index('ix_ap_entries_status', 'account_pool_entries', ['status'])
    op.create_index('ix_ap_entries_lifecycle', 'account_pool_entries', ['lifecycle_phase'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_ap_entries_lifecycle', table_name='account_pool_entries')
    op.drop_index('ix_ap_entries_status', table_name='account_pool_entries')
    op.drop_index('ix_ap_entries_platform', table_name='account_pool_entries')
    op.drop_table('account_pool_entries')
