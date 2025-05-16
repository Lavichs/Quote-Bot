from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    TG_BOT_TOKEN: str
    DB_HOST: str
    DB_PORT: str
    DB_USER: str
    DB_PASS: str
    DB_NAME: str

    @property
    def DATABASE_URL(self) -> str:
        # DSN
        # postgresql+asyncpg://postgres:postgres@localhost:5432/db
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
