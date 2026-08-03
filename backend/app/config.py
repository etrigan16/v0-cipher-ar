from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/aukalabs"
    # Required — no default. The backend must not boot with a known secret.
    secret_key: str
    # Required — Resend API key for transactional emails.
    resend_api_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440

    model_config = {"env_file": ".env"}


settings = Settings()
