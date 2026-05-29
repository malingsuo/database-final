import os
try:
    from pydantic_settings import BaseSettings
except Exception:
    class BaseSettings:
        def __init__(self, **kwargs):
            for key, value in self.__class__.__dict__.items():
                if key.isupper():
                    setattr(self, key, os.getenv(key, kwargs.get(key, value)))


class Settings(BaseSettings):
    DATABASE_URL: str = (
        f"postgresql+psycopg2://"
        f"{os.getenv('DB_USER', 'postgres')}:"
        f"{os.getenv('DB_PASSWORD', 'postgres')}@"
        f"{os.getenv('DB_HOST', 'localhost')}:"
        f"{os.getenv('DB_PORT', '5432')}/"
        f"{os.getenv('DB_NAME', 'dbfinal')}"
    )
    SECRET_KEY: str = "change-me"
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "console"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
