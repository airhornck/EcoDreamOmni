import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request

logger = logging.getLogger(__name__)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.api import (
    auth, admin, dashboard, platform_account, account_pool, content_forge,
    compliance, publisher, proxy, pool_predictor, skill_hub, agent_orchestra, websocket,
    trend_scout, methodology, data_analyst, platform_rules, persona_pool,
    skill_smith, pipeline, harness, ip_reputation, pool_predictor_explore,
    content_insight, platform_adapters, matrix_ops, tenants, orchestrator,
    api_platform, audit, metrics, agent_hub, agent_watch, agent_metrics,
    agent_cockpit, llm_hub, cron_hub, prompt_registry, workflow_engine,
    task_hub, human_in_loop, review_publish, asset_pool, comment_hub, content_series, copilot, conversation,
    workflows, image_forge, persona_story, brand_knowledge, timeline, vetdrug, playground,
    agents,
    prohibited_words, platform_schemas,
    platform_content_type_styles, content_templates,
    strategy_elements, strategy_sets,
    meta_orchestrator,
    comment_hub_v2,
    mcp_gateway,
    agent_fleet,
    agent_watch_ws,
)
from src.core.database import engine, AsyncSessionLocal
from src.core.middleware import RequestIDMiddleware, StructuredLoggingMiddleware
from src.core.tenant_middleware import TenantContextMiddleware
from src.core.telemetry import init_tracing, instrument_fastapi, instrument_celery, instrument_redis
from src.models.orm_user import UserORM

# Initialize OpenTelemetry
tracer = init_tracing()
instrument_celery()
instrument_redis()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables if they don't exist
    from src.models.llm_hub_orm import LLMModelORM, LLMScopeConfigORM, LLMUsageLogORM, LLMPricingORM
    from src.models.persona_story_orm import PersonaStoryORM, StoryNodeORM
    from src.models.brand_knowledge_orm import BrandKnowledgeEntryORM
    from src.models.timeline_library_orm import TimelineEventORM
    from src.models.vet_drug_orm import VetDrugEntryORM
    from src.models.asset_pool_orm import AssetORM as AssetPoolEntryORM
    from src.models.platform_rule_orm import PlatformRuleORM
    from src.models.platform_rule_attribution_orm import ContentRuleAttributionORM
    from src.models.task_orm import TaskORM
    from src.models.prohibited_word_orm import ProhibitedWordORM, ContentGuidelineORM
    from src.models.account_pool_orm import AccountPoolEntryORM
    from src.models.proxy_config_orm import ProxyConfigORM
    from sqlalchemy import text, select
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(UserORM.__table__.create, checkfirst=True)
        await conn.run_sync(LLMModelORM.__table__.create, checkfirst=True)
        await conn.run_sync(LLMScopeConfigORM.__table__.create, checkfirst=True)
        await conn.run_sync(LLMUsageLogORM.__table__.create, checkfirst=True)
        await conn.run_sync(LLMPricingORM.__table__.create, checkfirst=True)
        await conn.run_sync(PersonaStoryORM.__table__.create, checkfirst=True)
        await conn.run_sync(StoryNodeORM.__table__.create, checkfirst=True)
        await conn.run_sync(BrandKnowledgeEntryORM.__table__.create, checkfirst=True)
        await conn.run_sync(TimelineEventORM.__table__.create, checkfirst=True)
        # Migrate: add cron_job_id column if missing (Timeline↔CronHub binding)
        await conn.execute(text("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = 'timeline_events' AND column_name = 'cron_job_id'
                ) THEN
                    ALTER TABLE timeline_events ADD COLUMN cron_job_id VARCHAR(64);
                END IF;
            END $$;
        """))
        await conn.run_sync(VetDrugEntryORM.__table__.create, checkfirst=True)
        await conn.run_sync(AssetPoolEntryORM.__table__.create, checkfirst=True)
        await conn.run_sync(PlatformRuleORM.__table__.create, checkfirst=True)
        await conn.run_sync(ContentRuleAttributionORM.__table__.create, checkfirst=True)
        await conn.run_sync(TaskORM.__table__.create, checkfirst=True)
        # Migrate: add missing publish audit columns if needed
        await conn.execute(text("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = 'tasks' AND column_name = 'published_url'
                ) THEN
                    ALTER TABLE tasks ADD COLUMN published_url VARCHAR(512);
                END IF;
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = 'tasks' AND column_name = 'platform_post_id'
                ) THEN
                    ALTER TABLE tasks ADD COLUMN platform_post_id VARCHAR(128);
                END IF;
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = 'tasks' AND column_name = 'published_at'
                ) THEN
                    ALTER TABLE tasks ADD COLUMN published_at TIMESTAMP WITH TIME ZONE;
                END IF;
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = 'tasks' AND column_name = 'publish_error'
                ) THEN
                    ALTER TABLE tasks ADD COLUMN publish_error TEXT;
                END IF;
            END $$;
        """))
        await conn.run_sync(ProhibitedWordORM.__table__.create, checkfirst=True)
        await conn.run_sync(ContentGuidelineORM.__table__.create, checkfirst=True)
        await conn.run_sync(AccountPoolEntryORM.__table__.create, checkfirst=True)
        await conn.run_sync(ProxyConfigORM.__table__.create, checkfirst=True)

        # v4.0 Phase 1: Create new ORM tables
        from src.models.platform_content_type_style import PlatformContentTypeStyleORM
        from src.models.content_template import ContentTemplateORM
        from src.models.agent_orm import AgentORM
        await conn.run_sync(PlatformContentTypeStyleORM.__table__.create, checkfirst=True)
        await conn.run_sync(ContentTemplateORM.__table__.create, checkfirst=True)
        await conn.run_sync(AgentORM.__table__.create, checkfirst=True)

        # v4.0 Phase 1: Ensure task agent columns exist (for environments not using alembic)
        await conn.execute(text("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = 'tasks' AND column_name = 'agent_id'
                ) THEN
                    ALTER TABLE tasks ADD COLUMN agent_id VARCHAR(64);
                    CREATE INDEX ix_tasks_agent ON tasks(agent_id);
                END IF;
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = 'tasks' AND column_name = 'agent_config_snapshot'
                ) THEN
                    ALTER TABLE tasks ADD COLUMN agent_config_snapshot JSONB DEFAULT '{}';
                END IF;
            END $$;
        """))

    # v4.0 Phase 1: Seed default agents
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.ext.asyncio import AsyncSession
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with AsyncSessionLocal() as db:
        from src.services.agent_function import seed_default_agents
        seeded = await seed_default_agents(db)
        if seeded:
            logger.info("Seeded %d default agents", seeded)

    # Seed default data for content forge dropdowns
    async with AsyncSessionLocal() as db:
        from src.core.config import settings
        # 1. Seed LLM models
        from src.services import llm_hub as lhs
        from src.models.llm_hub_orm import LLMModelORM
        result = await db.execute(select(LLMModelORM))
        if not result.scalars().all():
            default_models = [
                {"provider": "deepseek", "model_name": settings.DEFAULT_LLM_MODEL or "deepseek-chat", "env_key": "DEEPSEEK_API_KEY", "endpoint_url": "https://api.deepseek.com/chat/completions"},
                {"provider": "openai", "model_name": "gpt-4o-mini", "env_key": "OPENAI_API_KEY", "endpoint_url": "https://api.openai.com/v1/chat/completions"},
                {"provider": "anthropic", "model_name": "claude-3-5-sonnet", "env_key": "ANTHROPIC_API_KEY", "endpoint_url": "https://api.anthropic.com/v1/messages"},
                {"provider": "kimi", "model_name": "kimi-v1", "env_key": "KIMI_API_KEY", "endpoint_url": "https://api.moonshot.cn/v1/chat/completions"},
            ]
            for m in default_models:
                api_key = getattr(settings, m["env_key"], "") or "sk-demo-key"
                await lhs.register_model(db=db, provider=m["provider"], model_name=m["model_name"], api_key=api_key, endpoint_url=m["endpoint_url"], status="active")

        # 2. Seed PersonaStories
        from src.services import persona_story_service as pss
        from src.models.persona_story_orm import PersonaStoryORM
        result = await db.execute(select(PersonaStoryORM))
        if not result.scalars().all():
            story = await pss.create_story(
                db=db, persona_id="p1", name="毛孩子的第一次体检",
                description="记录带宠物第一次去医院体检的完整心路历程",
                emotion_curve_template="gradual_growth", status="active"
            )
            await db.commit()
            await db.refresh(story)
            nodes = [
                {"theme": "出发前的紧张", "emotion_tone": "low", "key_event": "收拾宠物包，毛孩子似乎察觉到异样"},
                {"theme": "医院里的好奇", "emotion_tone": "medium", "key_event": "宠物对医院环境感到好奇，四处张望"},
                {"theme": "检查时的乖巧", "emotion_tone": "high", "key_event": "医生检查时宠物异常配合，获得表扬"},
                {"theme": "拿到健康报告", "emotion_tone": "burst", "key_event": "报告显示一切正常，心中的石头落地"},
            ]
            for i, n in enumerate(nodes):
                await pss.create_node(
                    db=db, story_id=str(story.id), sequence_index=i,
                    theme=n["theme"], emotion_tone=n["emotion_tone"],
                    key_event=n["key_event"]
                )
            await db.commit()

            story2 = await pss.create_story(
                db=db, persona_id="p3", name="换粮大作战",
                description="从平价粮换到高端粮的七天过渡记录",
                emotion_curve_template="gradual_growth", status="active"
            )
            await db.commit()
            await db.refresh(story2)
            nodes2 = [
                {"theme": "第一天混粮", "emotion_tone": "low", "key_event": "新旧粮比例 3:7，宠物有点挑食"},
                {"theme": "第三天适应", "emotion_tone": "medium", "key_event": "比例调到 1:1，开始接受新粮"},
                {"theme": "第七天成功", "emotion_tone": "burst", "key_event": "完全换成新粮，毛发明显变亮"},
            ]
            for i, n in enumerate(nodes2):
                await pss.create_node(
                    db=db, story_id=str(story2.id), sequence_index=i,
                    theme=n["theme"], emotion_tone=n["emotion_tone"],
                    key_event=n["key_event"]
                )
            await db.commit()

    # 3. Load workflow engine presets
    from src.services import workflow_engine as we
    we.load_presets()

    # 4. Warm TaskHub cache from DB
    from src.models.task_orm import TaskORM
    from src.services import task_hub as th
    async with AsyncSessionLocal() as db:
        count = await th.load_tasks_into_cache(db)
        if count:
            print(f"[startup] TaskHub cache warmed with {count} tasks")

    # 5. Load proxy configs from DB (P1 Fix: persistence across restarts)
    from src.services.proxy_service import load_proxies_from_db, persist_proxy_to_db
    async with AsyncSessionLocal() as db:
        proxy_loaded = await load_proxies_from_db(db)
        if proxy_loaded:
            logger.info("Loaded %d proxy configs from DB", proxy_loaded)

    # 6. Load account pool from DB (P0 Fix: persistence across restarts)
    from src.models.account_pool import load_pool_from_db
    async with AsyncSessionLocal() as db:
        loaded_count = await load_pool_from_db(db)
        if loaded_count:
            logger.info("Loaded %d account pool entries from DB", loaded_count)

    # 7. Seed proxy configs from environment variables (if DB is empty)
    from src.core.config import settings
    from src.services import proxy_service as ps
    if not ps.list_proxies():
        proxy_id_http = ""
        proxy_id_socks5 = ""

        if settings.PROXY_HTTP_HOST and settings.PROXY_HTTP_PORT:
            proxy_http = ps.create_proxy(
                name="住宅轮换代理-HTTP",
                provider="custom",
                protocol="http",
                host=settings.PROXY_HTTP_HOST,
                port=settings.PROXY_HTTP_PORT,
                username=settings.PROXY_HTTP_USER,
                password=settings.PROXY_HTTP_PASS,
                region="default",
                rotation_type=settings.PROXY_ROTATION_TYPE,
            )
            proxy_id_http = proxy_http.id
            logger.info("Auto-created HTTP proxy: %s:%s", settings.PROXY_HTTP_HOST, settings.PROXY_HTTP_PORT)
            async with AsyncSessionLocal() as db:
                await persist_proxy_to_db(db, proxy_http)

        if settings.PROXY_SOCKS5_HOST and settings.PROXY_SOCKS5_PORT:
            proxy_socks5 = ps.create_proxy(
                name="住宅轮换代理-SOCKS5",
                provider="custom",
                protocol="socks5",
                host=settings.PROXY_SOCKS5_HOST,
                port=settings.PROXY_SOCKS5_PORT,
                username=settings.PROXY_SOCKS5_USER,
                password=settings.PROXY_SOCKS5_PASS,
                region="default",
                rotation_type=settings.PROXY_ROTATION_TYPE,
            )
            proxy_id_socks5 = proxy_socks5.id
            logger.info("Auto-created SOCKS5 proxy: %s:%s", settings.PROXY_SOCKS5_HOST, settings.PROXY_SOCKS5_PORT)
            async with AsyncSessionLocal() as db:
                await persist_proxy_to_db(db, proxy_socks5)

        # Seed account pool (if empty after loading)
        from src.services import account_pool_service as aps
        accounts = aps.list_accounts()
        if not accounts:
            xhs_cookie = settings.REDNOTE_COOKIE or "demo_cookie"
            if not settings.REDNOTE_COOKIE:
                logger.warning("REDNOTE_COOKIE not set; seeding account with demo_cookie (publishing will fail)")

            aps.create_account(
                platform="xiaohongshu", account_id="xhs_demo_001", nickname="小红的猫",
                cookie=xhs_cookie, persona="p1", content_vertical="宠物健康",
                lifecycle_phase="warmup",
                proxy_config={"proxy_id": proxy_id_http, "type": "http", "region": "default"} if proxy_id_http else None,
            )
            aps.create_account(
                platform="douyin", account_id="dy_demo_001", nickname="抖音铲屎官",
                cookie="demo_cookie", persona="p3", content_vertical="宠物日常",
                lifecycle_phase="active",
            )
            aps.create_account(
                platform="wechat_channels", account_id="wc_demo_001", nickname="视频号萌宠",
                cookie="demo_cookie", persona="p1", content_vertical="宠物科普",
                lifecycle_phase="active",
            )

            from src.models.account_pool import sync_pool_to_db
            async with AsyncSessionLocal() as db:
                await sync_pool_to_db(db)
                logger.info("Seeded and saved %d account pool entries to DB", len(aps.list_accounts()))

    yield
    # Shutdown: nothing special


app = FastAPI(
    title="EcoDreamOmni API",
    description="宠物健康素人号矩阵AI平台 API",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# Instrument FastAPI with OpenTelemetry
instrument_fastapi(app)

# ─── Middleware (ordered: outer -> inner) ───
app.add_middleware(RequestIDMiddleware)
app.add_middleware(StructuredLoggingMiddleware)
app.add_middleware(TenantContextMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Exception handlers with `code` extension (detailed design §3.2) ───

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    body = {"detail": exc.detail}
    if exc.status_code == 409:
        body["code"] = "CONFLICT"
    elif exc.status_code == 403:
        body["code"] = "FORBIDDEN"
    elif exc.status_code == 401:
        body["code"] = "UNAUTHORIZED"
    elif exc.status_code == 404:
        body["code"] = "NOT_FOUND"
    elif exc.status_code == 422:
        body["code"] = "VALIDATION_ERROR"
    else:
        body["code"] = f"HTTP_{exc.status_code}"
    return JSONResponse(status_code=exc.status_code, content=body)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    body = {
        "detail": exc.errors(),
        "code": "VALIDATION_ERROR",
    }
    return JSONResponse(status_code=422, content=body)


# Register routers
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(dashboard.router)
app.include_router(platform_account.router)
app.include_router(account_pool.router)
app.include_router(content_forge.router)
app.include_router(compliance.router)
app.include_router(publisher.router)
app.include_router(publisher.platform_router)
app.include_router(proxy.router)
app.include_router(pool_predictor.router)
app.include_router(skill_hub.router, prefix="/skills", tags=["skills"])
app.include_router(skill_hub.agent_binding_router, prefix="/agent-skills", tags=["agent-skills"])
app.include_router(agent_orchestra.router, tags=["agent-orchestra"])
app.include_router(websocket.router)
app.include_router(trend_scout.router)
app.include_router(methodology.router)
app.include_router(data_analyst.router)
app.include_router(platform_rules.router)
app.include_router(platform_schemas.router)
app.include_router(persona_pool.router)
app.include_router(skill_smith.router)
app.include_router(pipeline.router)
app.include_router(harness.router)
app.include_router(ip_reputation.router)
app.include_router(pool_predictor_explore.router)
app.include_router(content_insight.router)
app.include_router(platform_adapters.router)
app.include_router(matrix_ops.router)
app.include_router(tenants.router)
app.include_router(orchestrator.router)
app.include_router(api_platform.router)
app.include_router(audit.router)
app.include_router(metrics.router)
app.include_router(agent_hub.router)
app.include_router(agent_watch.router)
app.include_router(agent_metrics.router)
app.include_router(agent_cockpit.router)
app.include_router(llm_hub.router)
app.include_router(cron_hub.router)
app.include_router(prompt_registry.router)
app.include_router(workflow_engine.router)
app.include_router(task_hub.router)
app.include_router(agents.router)
app.include_router(human_in_loop.router)
app.include_router(review_publish.router)
app.include_router(copilot.router)
app.include_router(copilot.generate_cover_router)
app.include_router(conversation.router)
app.include_router(asset_pool.router)
app.include_router(comment_hub.router)
app.include_router(content_series.router)
app.include_router(workflows.router)
app.include_router(image_forge.router)
app.include_router(persona_story.router)
app.include_router(brand_knowledge.router)
app.include_router(timeline.router)
app.include_router(vetdrug.router)
app.include_router(playground.router)
app.include_router(prohibited_words.router)
app.include_router(platform_content_type_styles.router)
app.include_router(content_templates.router)
app.include_router(strategy_elements.router)
app.include_router(strategy_sets.router)
app.include_router(meta_orchestrator.router)
app.include_router(comment_hub_v2.router)
app.include_router(mcp_gateway.router)
app.include_router(agent_fleet.router)
app.include_router(agent_watch_ws.router)

# Static file serving for uploads (local storage mode — Phase 1)
# In Phase 2 (OSS migration), this mount will be removed and files served via CDN.
from pathlib import Path
from src.core.file_upload import UPLOAD_DIR

Path(UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")


@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "0.1.0"}


@app.get("/")
async def root():
    return {"message": "EcoDreamOmni API is running"}


