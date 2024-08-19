from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    POSTGRES_DB: str 
    POSTGRES_USER: str 
    POSTGRES_PASSWORD: str 
    POSTGRES_PORT: int 

    SQLALCHEMY_DATABASE_URL: str
    
    SECRET_KEY: str
    ALGORITHM: str

    MAIL_USERNAME: str = 'hw2024@meta.ua'
    MAIL_PASSWORD: str = '12345'
    MAIL_FROM: str = 'hw2024@meta.ua'
    MAIL_PORT: int = 465
    MAIL_SERVER: str = 'smtp.meta.ua' 
    TEMPLATE_FOLDER: Path = Path(__file__).parent.parent / 'templates'

    CLOUDINARY_NAME: str 
    CLOUDINARY_API_KEY: str
    CLOUDINARY_API_SECRET: str

    REDIS_URL: str
    redis_host: str = 'localhost'
    redis_port: int = 6379
    redis_password: str | None = None
   
  
    class Config:
        env_file = "../../env"
        env_file_encoding = "utf-8"
        from_attributes = True

settings = Settings()


print("Cloudinary Name:", settings.CLOUDINARY_NAME)
print("Cloudinary API Key:", settings.CLOUDINARY_API_KEY)
print("Cloudinary API Secret:", settings.CLOUDINARY_API_SECRET)