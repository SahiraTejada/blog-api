from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Blog Application"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str =