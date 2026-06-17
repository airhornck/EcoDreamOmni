"""SkillHub ORM integration — database access layer for skill definitions.

This module centralises all direct SQLAlchemy/database access for skill
management so that `skill_hub.py` remains an in-memory service layer.
"""

from datetime import datetime, timezone
from typing import Dict, List

from sqlalchemy import select

from src.models.skill_definition import SkillDefinitionORM


def _orm_to_dataclass(orm: SkillDefinitionORM):
    """Convert ORM instance to in-memory SkillDefinition dataclass."""
    # Delayed import avoids circular dependency with the service layer.
    from src.services.skill_hub import SkillDefinition

    return SkillDefinition(
        skill_id=orm.skill_id,  # type: ignore[arg-type]
        name=orm.name,  # type: ignore[arg-type]
        version=orm.version,  # type: ignore[arg-type]
        description=orm.description or "",  # type: ignore[arg-type]
        level=orm.level,  # type: ignore[arg-type]
        input_schema=orm.input_schema or {},  # type: ignore[arg-type]
        output_schema=orm.output_schema or {},  # type: ignore[arg-type]
        modality_support=orm.modality_support or {"text": True},  # type: ignore[arg-type]
        requires_llm=orm.requires_llm,  # type: ignore[arg-type]
        llm_model_preference=orm.llm_model_preference or "",  # type: ignore[arg-type]
        required_functions=orm.required_functions or [],  # type: ignore[arg-type]
        permissions=orm.permissions or {},  # type: ignore[arg-type]
        code=orm.code_path or "",  # type: ignore[arg-type]
        status=orm.status,  # type: ignore[arg-type]
        meta=orm.meta or {},  # type: ignore[arg-type]
    )


async def load_skills_from_orm(db_session) -> int:
    """Load all active skills from DB into in-memory registry.

    Called during startup or admin-triggered refresh.
    Returns count of loaded skills.
    """
    from src.services.skill_hub import register

    result = await db_session.execute(
        select(SkillDefinitionORM).where(SkillDefinitionORM.status == "active")
    )
    orm_skills = result.scalars().all()
    count = 0
    for orm in orm_skills:
        sd = _orm_to_dataclass(orm)
        register(sd)
        count += 1
    return count


async def save_skill_to_orm(db_session, skill_def) -> SkillDefinitionORM:
    """Persist a SkillDefinition to DB (upsert)."""
    result = await db_session.execute(
        select(SkillDefinitionORM).where(
            SkillDefinitionORM.skill_id == skill_def.skill_id,
            SkillDefinitionORM.version == skill_def.version,
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        existing.name = skill_def.name
        existing.description = skill_def.description
        existing.level = skill_def.level
        existing.input_schema = skill_def.input_schema
        existing.output_schema = skill_def.output_schema
        existing.modality_support = skill_def.modality_support
        existing.requires_llm = skill_def.requires_llm
        existing.llm_model_preference = skill_def.llm_model_preference
        existing.required_functions = skill_def.required_functions
        existing.permissions = skill_def.permissions
        existing.code_path = skill_def.code
        existing.status = skill_def.status
        existing.meta = skill_def.metadata
        existing.updated_at = datetime.now(timezone.utc)
        await db_session.flush()
        return existing
    else:
        orm = SkillDefinitionORM(
            skill_id=skill_def.skill_id,
            name=skill_def.name,
            description=skill_def.description,
            version=skill_def.version,
            level=skill_def.level,
            input_schema=skill_def.input_schema,
            output_schema=skill_def.output_schema,
            modality_support=skill_def.modality_support,
            requires_llm=skill_def.requires_llm,
            llm_model_preference=skill_def.llm_model_preference,
            required_functions=skill_def.required_functions,
            permissions=skill_def.permissions,
            code_path=skill_def.code,
            status=skill_def.status,
            meta=skill_def.metadata,
        )
        db_session.add(orm)
        await db_session.flush()
        return orm
