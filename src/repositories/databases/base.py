# src/repositories/databases/base.py
import os

import dataclasses

import psycopg2
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from pydantic_settings import BaseSettings

# class Settings(BaseSettings):
#     APP_DB_URL: str
#     EXTRA_DB_URL: str
#
#     class Config:
#         env_file = ".env"
#
# settings = Settings()


@dataclasses.dataclass
class DatabaseSettings():
    USERNAME: str
    PASSWORD: str
    HOST: str
    PORT: str
    DATABASE: str

def load_database_settings() -> DatabaseSettings:
    return DatabaseSettings(
        os.getenv("EXTRA_DB_USER"),
        os.getenv("EXTRA_DB_PASSWORD"),
        os.getenv("EXTRA_DB_HOST"),
        os.getenv("EXTRA_DB_PORT"),
        os.getenv("EXTRA_DB_NANE"),
    )

def ps_connection(db: DatabaseSettings):
    """
    Create a connection to the PostgreSQL Control-database by psycopg2
    :return:
    """

    return psycopg2.connect(
        database=db.DATABASE,
        user=db.USERNAME,
        password=db.PASSWORD,
        host=db.HOST,
        port=db.PORT
    )

