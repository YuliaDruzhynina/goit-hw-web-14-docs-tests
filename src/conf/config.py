from pathlib import Path
from pydantic_settings import BaseSettings
#from typing import Optional

class Settings(BaseSettings):
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_PORT: int

    SQLALCHEMY_DATABASE_URL: str

    SECRET_KEY: str
    ALGORITHM: str

    MAIL_USERNAME: str = "poshta@example.ua"
    MAIL_PASSWORD: str = "mypassword"
    MAIL_FROM: str = "poshta@example.ua"

    MAIL_PORT: int = 465
    MAIL_SERVER: str = "smtp.meta.ua"
    TEMPLATE_FOLDER: Path = Path(__file__).parent.parent / "templates"

    CLOUDINARY_NAME: str
    CLOUDINARY_API_KEY: str
    CLOUDINARY_API_SECRET: str

    REDIS_URL: str
    # redis_port: int = 6379
    # redis_host: str = "localhost"
    # redis_password: str | None = None
    #redis_password: Optional[str] = None
    class Config:
        env_file = "../../.env"
        env_file_encoding = "utf-8"
        from_attributes = True
    
settings = Settings()


