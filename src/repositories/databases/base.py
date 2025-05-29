# src/repositories/databases/base.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_DB_URL: str
    EXTRA_DB_URL: str

    class Config:
        env_file = ".env"

settings = Settings()

# Локальная БД (пользовательские данные)
app_engine = create_engine(
    settings.APP_DB_URL,
    pool_size=10,
    max_overflow=20
)

# Удаленная БД (новостные данные)
extra_engine = create_engine(
    settings.EXTRA_DB_URL,
    pool_size=5,
    max_overflow=10,
    connect_args={"sslmode": "require"}
)

BaseLocal = declarative_base(bind=app_engine)
BaseRemote = declarative_base(bind=extra_engine)
