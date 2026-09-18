from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Literature Review Assistant"
    app_version: str = "0.1.0"

    # Application environment
    environment: str = "development"
    debug: bool = True

    # Database
    database_url: str = ""

    # LLM
    llm_api_key: str = ""

    # Logging
    log_level: str = "DEBUG"
    log_file_enabled: bool = True

    # Better Stack
    betterstack_enabled: bool = False
    betterstack_source_token: str = ""
    betterstack_ingesting_host: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()