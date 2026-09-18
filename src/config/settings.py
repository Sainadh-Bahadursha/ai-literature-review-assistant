from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Literature Review Assistant"
    app_version: str = "0.1.0"
    debug: bool = True

    database_url: str = ""

    llm_api_key: str = ""

    jwt_secret_key: str = ""

    vector_db_path: str = "./data/chroma"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()