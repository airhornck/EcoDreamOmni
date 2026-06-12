from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    APP_NAME: str = "EcoDreamOmni"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/ecodream"
    REDIS_URL: str = "redis://localhost:6379/0"

    JWT_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24 * 30  # 30 days

    # === LLM Models ===
    DEFAULT_LLM_MODEL: str = "deepseek-chat"
    DEEPSEEK_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    KIMI_API_KEY: str = ""
    REDNOTE_COOKIE: str = ""

    # === Image Generation ===
    QWEN_IMAGE_API_KEY: str = ""
    QWEN_IMAGE_MODEL: str = "wanx-v1"

    UPLOAD_DIR: str = "uploads"

    # === Proxy Configuration (for account IP isolation) ===
    # HTTP proxy — used for xhs publisher requests
    PROXY_HTTP_HOST: str = ""
    PROXY_HTTP_PORT: int = 0
    PROXY_HTTP_USER: str = ""
    PROXY_HTTP_PASS: str = ""
    # SOCKS5 proxy — alternative protocol
    PROXY_SOCKS5_HOST: str = ""
    PROXY_SOCKS5_PORT: int = 0
    PROXY_SOCKS5_USER: str = ""
    PROXY_SOCKS5_PASS: str = ""
    PROXY_ROTATION_TYPE: str = "rotating"  # static | session | rotating

    # === OSS (Aliyun Object Storage) ===
    # When all OSS_* vars are set, file uploads go to OSS instead of local disk.
    # When unset, falls back to local filesystem (backward compatible).
    OSS_ACCESS_KEY_ID: str = ""
    OSS_ACCESS_KEY_SECRET: str = ""
    OSS_BUCKET: str = ""
    OSS_ENDPOINT: str = ""          # e.g. oss-cn-hangzhou.aliyuncs.com
    OSS_REGION: str = ""            # e.g. cn-hangzhou
    OSS_CDN_DOMAIN: str = ""        # e.g. cdn.yourdomain.com (optional)

    # Stock photo APIs
    UNSPLASH_API_KEY: str = ""
    UNSPLASH_API_URL: str = "https://api.unsplash.com"

    # LLM Hub encryption master key (must be 32+ bytes in production)
    LLM_API_KEY_MASTER_KEY: str = ""

settings = Settings()
