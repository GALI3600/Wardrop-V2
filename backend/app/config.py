from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://wardrop:wardrop@localhost:5432/wardrop"
    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 28800  # 20 days

    llm_provider: str = "groq"

    anthropic_api_key: str = ""
    anthropic_model: str = "claude-haiku-4-5-20251001"

    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"

    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"

    vapid_private_key: str = ""
    vapid_public_key: str = ""
    vapid_email: str = ""

    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""

    model_config = {"env_file": ".env", "env_prefix": "WARDROP_"}


settings = Settings()
