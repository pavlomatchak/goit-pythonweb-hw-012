from pydantic import ConfigDict, EmailStr
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os

load_dotenv()
class Config:
  DB_URL = os.environ.get("DB_URL")
  JWT_SECRET = os.environ.get("JWT_SECRET")
  JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM")
  JWT_EXPIRATION_SECONDS = int(os.environ.get("JWT_EXPIRATION_SECONDS"))

config = Config

class Settings(BaseSettings):
  MAIL_USERNAME: EmailStr = os.environ.get("MAIL_USERNAME")
  MAIL_PASSWORD: str = os.environ.get("MAIL_PASSWORD")
  MAIL_FROM: EmailStr = os.environ.get("MAIL_FROM")
  MAIL_PORT: int = int(os.environ.get("MAIL_PORT"))
  MAIL_SERVER: str = os.environ.get("MAIL_SERVER")
  MAIL_FROM_NAME: str = os.environ.get("MAIL_FROM_NAME")
  MAIL_STARTTLS: bool = os.environ.get("MAIL_STARTTLS")
  MAIL_SSL_TLS: bool = os.environ.get("MAIL_SSL_TLS")
  USE_CREDENTIALS: bool = os.environ.get("USE_CREDENTIALS")
  VALIDATE_CERTS: bool = os.environ.get("VALIDATE_CERTS")

  model_config = ConfigDict(
    extra="ignore", env_file=".env", env_file_encoding="utf-8", case_sensitive=True
  )

settings = Settings()
