from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

# Import ORM Base for autogenerate support
from src.core.database import Base
from src.models.orm_user import UserORM  # noqa: F401
from src.models.asset_pool_orm import AssetORM  # noqa: F401
from src.models.brand_knowledge_orm import BrandKnowledgeEntryORM  # noqa: F401
from src.models.vet_drug_orm import VetDrugEntryORM  # noqa: F401
from src.models.timeline_library_orm import TimelineEventORM  # noqa: F401
from src.models.platform_rule_orm import PlatformRuleORM, PlatformRuleHistoryORM  # noqa: F401
from src.models.task_orm import TaskORM  # noqa: F401
from src.models.note_engagement_orm import NoteEngagementORM  # noqa: F401
from src.models.publish_task_orm import PublishTaskORM  # noqa: F401
from src.models.platform_schema_orm import PlatformSchemaORM, PlatformContentFormatORM  # noqa: F401
from src.models.checkpoint_orm import CheckpointORM  # noqa: F401
from src.models.agent_orm import AgentORM  # noqa: F401
from src.models.copilot_orm import CopilotContextSessionORM, AICoverGenerationJobORM, CopilotActionLogORM  # noqa: F401

# this is the Alembic Config object
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
