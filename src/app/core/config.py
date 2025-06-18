from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ## ==================================
    #       Extra DB with news
    ## ==================================
    EXTRA_DB_HOST: str
    EXTRA_DB_PORT: int
    EXTRA_DB_NANE: str
    EXTRA_DB_USER: str
    EXTRA_DB_PASSWORD: str

    ## ==================================
    #       App DB for local use
    ## ==================================
    APP_DB_HOST: str
    APP_DB_PORT: str
    APP_DB_NANE: str
    APP_DB_USER: str
    APP_DB_PASSWORD: str

    ## ==================================
    #       App
    ## ==================================
    API_V1_STR: str
    PROJECT_NAME: str

    class Config:
        env_file = ".env"

settings = Settings()
