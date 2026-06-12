"""Agent-First v4.0 — Add agents table + task.agent_id.

Revision ID: g2h3i4j5k6l7
Revises: f1a2b3c4d5e6
Create Date: 2026-06-04 12:30:00.000000+00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "g2h3i4j5k6l7"
down_revision: Union[str, None] = "f1a2b3c4d5e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create agents table
    op.create_table(
        "agents",
        sa.Column("id", sa.String(64), primary_key=True, comment="Agent ID"),
        sa.Column("name", sa.String(128), nullable=False, comment="显示名称"),
        sa.Column("role", sa.String(64), nullable=False, comment="角色类型"),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("avatar_url", sa.String(512), nullable=True),
        sa.Column("skills", sa.JSON, server_default=sa.text("'[]'"), comment="能力标签"),
        sa.Column("supported_platforms", sa.JSON, server_default=sa.text("'[]'"), comment="支持平台"),
        sa.Column("supported_formats", sa.JSON, server_default=sa.text("'[]'"), comment="支持格式"),
        sa.Column("config", sa.JSON, server_default=sa.text("'{}'"), comment="Agent 配置"),
        sa.Column("success_rate", sa.Float, server_default=sa.text("0.92"), comment="成功率"),
        sa.Column("recent_tasks_1h", sa.Integer, server_default=sa.text("0"), comment="近1h任务数"),
        sa.Column("status", sa.String(32), nullable=False, server_default="ACTIVE"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), onupdate=sa.text("now()")),
        sa.Index("ix_agents_status", "status"),
        sa.Index("ix_agents_role", "role"),
        comment="Agent Registry — v4.0 Agent-First",
    )

    # 2. Add agent_id and agent_config_snapshot to tasks
    op.add_column(
        "tasks",
        sa.Column("agent_id", sa.String(64), nullable=True, index=True, comment="关联 Agent ID (v4.0)"),
    )
    op.add_column(
        "tasks",
        sa.Column("agent_config_snapshot", sa.JSON, server_default=sa.text("'{}'"), comment="Agent 配置快照"),
    )

    # 3. Make workflow_template_id nullable (backward compatibility)
    op.alter_column("tasks", "workflow_template_id", nullable=True)

    # 4. Seed default agents (10 platform+format specific agents + 1 generic fallback)
    op.execute("""
        INSERT INTO agents (id, name, role, description, skills, supported_platforms, supported_formats, status, config)
        VALUES
          ('content_forge_xhs_image', '小红书图文生成 Agent', 'content_generation',
           '专为小红书图文笔记优化的内容生成 Agent，内置图文排版、封面生成、标签优化能力',
           '["text_generate_skill","keyword_inject_skill","rag_retrieval_skill","cover_generate_skill"]',
           '["xiaohongshu"]', '["图文"]', 'ACTIVE',
           '{"default_workflow_template_id": "content_creation_note_image", "workflow_version": 1}'),
          ('content_forge_xhs_video', '小红书视频生成 Agent', 'content_generation',
           '专为小红书视频内容优化的生成 Agent，支持脚本生成、分镜规划、口播稿优化',
           '["text_generate_skill","video_script_skill","shot_planning_skill","keyword_inject_skill"]',
           '["xiaohongshu"]', '["视频"]', 'ACTIVE',
           '{"default_workflow_template_id": "content_creation_video_original", "workflow_version": 1}'),
          ('content_forge_xhs_text', '小红书长文生成 Agent', 'content_generation',
           '专为小红书长文/攻略类内容优化的生成 Agent，支持结构化长文、分章节输出',
           '["text_generate_skill","content_structural_analysis_skill","keyword_inject_skill","rag_retrieval_skill"]',
           '["xiaohongshu"]', '["仅文字"]', 'ACTIVE',
           '{"default_workflow_template_id": "content_creation_text_article", "workflow_version": 1}'),
          ('content_forge_douyin_video', '抖音视频生成 Agent', 'content_generation',
           '专为抖音短视频优化的生成 Agent，支持爆款脚本、黄金3秒钩子、口播优化',
           '["text_generate_skill","video_script_skill","hook_optimize_skill","voice_synthesis_skill"]',
           '["douyin"]', '["视频"]', 'ACTIVE',
           '{"default_workflow_template_id": "content_creation_video_original", "workflow_version": 1}'),
          ('content_forge_douyin_clone', '抖音视频复刻 Agent', 'content_generation',
           '专为抖音爆款视频复刻优化的 Agent，支持脚本克隆、风格迁移、口播克隆',
           '["text_generate_skill","video_clone_skill","style_transfer_skill","voice_clone_skill"]',
           '["douyin"]', '["视频复刻"]', 'ACTIVE',
           '{"default_workflow_template_id": "content_creation_video_clone", "workflow_version": 1}'),
          ('content_forge_wx_text', '视频号图文生成 Agent', 'content_generation',
           '专为微信视频号图文内容优化的生成 Agent，支持公众号风格排版、阅读体验优化',
           '["text_generate_skill","keyword_inject_skill","rag_retrieval_skill","readability_optimize_skill"]',
           '["wechat_channels"]', '["图文"]', 'ACTIVE',
           '{"default_workflow_template_id": "content_creation_text_article", "workflow_version": 1}'),
          ('content_forge_wx_video', '视频号视频生成 Agent', 'content_generation',
           '专为微信视频号视频内容优化的生成 Agent，支持竖屏视频脚本、直播切片',
           '["text_generate_skill","video_script_skill","live_clip_skill","keyword_inject_skill"]',
           '["wechat_channels"]', '["视频"]', 'ACTIVE',
           '{"default_workflow_template_id": "content_creation_video_original", "workflow_version": 1}'),
          ('content_forge_bili_video', '哔哩哔哩视频生成 Agent', 'content_generation',
           '专为 B 站长视频优化的生成 Agent，支持分P规划、弹幕优化、二次元风格适配',
           '["text_generate_skill","video_script_skill","part_planning_skill","danmaku_optimize_skill"]',
           '["bilibili"]', '["视频"]', 'ACTIVE',
           '{"default_workflow_template_id": "content_creation_video_original", "workflow_version": 1}'),
          ('content_forge_bili_clone', '哔哩哔哩视频复刻 Agent', 'content_generation',
           '专为 B 站爆款视频复刻优化的 Agent，支持 MMD/手书克隆、风格迁移',
           '["text_generate_skill","video_clone_skill","style_transfer_skill","subtitle_optimize_skill"]',
           '["bilibili"]', '["视频复刻"]', 'ACTIVE',
           '{"default_workflow_template_id": "content_creation_video_clone", "workflow_version": 1}'),
          ('content_forge_generic', '通用内容生成 Agent', 'content_generation',
           '支持多平台多格式的通用内容生成 Agent，当没有平台-specific Agent 时作为兜底',
           '["text_generate_skill","keyword_inject_skill","rag_retrieval_skill","content_rewrite_skill","platform_adapt_skill"]',
           '["xiaohongshu","douyin","wechat_channels","bilibili"]', '["图文","视频","仅文字","视频复刻"]', 'ACTIVE',
           '{"default_workflow_template_id": "content_creation_standard", "workflow_version": 1}')
        ON CONFLICT (id) DO NOTHING;
    """)

    # 5. Backfill agent_id for existing tasks using platform+format+template mapping
    op.execute("""
        UPDATE tasks t
        SET agent_id = m.agent_id
        FROM (
            SELECT * FROM (VALUES
                ('xiaohongshu', '图文', 'content_creation_note_image', 'content_forge_xhs_image'),
                ('xiaohongshu', '图文', 'content_creation_standard', 'content_forge_xhs_image'),
                ('xiaohongshu', '视频', 'content_creation_video_original', 'content_forge_xhs_video'),
                ('xiaohongshu', '视频', 'content_creation_standard', 'content_forge_xhs_video'),
                ('xiaohongshu', '仅文字', 'content_creation_text_article', 'content_forge_xhs_text'),
                ('douyin', '视频', 'content_creation_video_original', 'content_forge_douyin_video'),
                ('douyin', '视频', 'content_creation_standard', 'content_forge_douyin_video'),
                ('douyin', '视频复刻', 'content_creation_video_clone', 'content_forge_douyin_clone'),
                ('douyin', '视频复刻', 'content_creation_standard', 'content_forge_douyin_clone'),
                ('wechat_channels', '图文', 'content_creation_note_image', 'content_forge_wx_text'),
                ('wechat_channels', '图文', 'content_creation_text_article', 'content_forge_wx_text'),
                ('wechat_channels', '图文', 'content_creation_standard', 'content_forge_wx_text'),
                ('wechat_channels', '视频', 'content_creation_video_original', 'content_forge_wx_video'),
                ('wechat_channels', '视频', 'content_creation_standard', 'content_forge_wx_video'),
                ('bilibili', '视频', 'content_creation_video_original', 'content_forge_bili_video'),
                ('bilibili', '视频', 'content_creation_standard', 'content_forge_bili_video'),
                ('bilibili', '视频复刻', 'content_creation_video_clone', 'content_forge_bili_clone'),
                ('bilibili', '视频复刻', 'content_creation_standard', 'content_forge_bili_clone')
            ) AS v(platform, content_format, workflow_template_id, agent_id)
        ) m
        WHERE t.workflow_template_id = m.workflow_template_id
          AND t.platform = m.platform
          AND COALESCE(t.content_format, '图文') = m.content_format
          AND t.agent_id IS NULL;
    """)

    # Fallback: unmatched tasks get generic agent
    op.execute("""
        UPDATE tasks
        SET agent_id = 'content_forge_generic'
        WHERE agent_id IS NULL AND workflow_template_id IS NOT NULL;
    """)


def downgrade() -> None:
    op.drop_column("tasks", "agent_config_snapshot")
    op.drop_column("tasks", "agent_id")
    op.alter_column("tasks", "workflow_template_id", nullable=False)
    op.drop_table("agents")
