import json
from aioredis import Redis
from datetime import datetime, timedelta, UTC
from typing import Optional

from fastapi import Depends, HTTPException, status
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from database.db import get_db
from schemas import User
from conf.config import config
from services.users import UserService
from main import app

class Hash:
  """Hashes and verifies passwords using bcrypt."""
  pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

  def verify_password(self, plain_password, hashed_password):
    """
    Verifies a plain text password against a hashed password.

    Args:
      plain_password (str): The plain text password to verify.
      hashed_password (str): The hashed password to compare against.

    Returns:
      bool: True if the passwords match, False otherwise.
    """
    return self.pwd_context.verify(plain_password, hashed_password)

  def get_password_hash(self, password: str):
    """
    Hashes a plain text password using bcrypt.

    Args:
      password (str): The plain text password to hash.

    Returns:
      str: The hashed password.
    """
    return self.pwd_context.hash(password)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

async def create_access_token(data: dict, expires_delta: Optional[int] = None):
  """
  Creates a JWT access token for a user.

  Args:
    data (dict): A dictionary containing user data to be encoded in the token.
    expires_delta (Optional[int]): The number of seconds until the token expires.

  Returns:
    str: The encoded JWT access token.
  """
  to_encode = data.copy()
  if expires_delta:
    expire = datetime.now(UTC) + timedelta(seconds=expires_delta)
  else:
    expire = datetime.now(UTC) + timedelta(seconds=config.JWT_EXPIRATION_SECONDS)
  to_encode.update({"exp": expire})
  encoded_jwt = jwt.encode(
    to_encode, config.JWT_SECRET, algorithm=config.JWT_ALGORITHM
  )
  return encoded_jwt

async def get_current_user(
  token: str = Depends(oauth2_scheme),
  db: AsyncSession = Depends(get_db),
  redis: Redis = Depends(lambda: app.state.redis),
):
  """
  Retrieves the current user, using Redis caching to reduce database queries.

  Args:
    token (str): The JWT token from the `Authorization` header.
    db (AsyncSession): The database session for querying the user if not cached.
    redis (Redis): Redis instance for caching the user.

  Returns:
    User: The user object retrieved from the cache or database.

  Raises:
    HTTPException: If token is invalid or user does not exist.
  """
  credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
  )

  try:
    payload = jwt.decode(token, config.JWT_SECRET, algorithms=[config.JWT_ALGORITHM])
    username = payload.get("sub")
    if username is None:
      raise credentials_exception
  except JWTError:
    raise credentials_exception

  cached_user = await redis.get(f"user:{username}")
  if cached_user:
    return User(**json.loads(cached_user))

  user_service = UserService(db)
  user = await user_service.get_user_by_username(username)

  if user is None:
    raise credentials_exception

  await redis.set(
    f"user:{username}",
    json.dumps(user.dict()),
    ex=3600,
  )

  return user

def create_email_token(data: dict):
  """
  Creates a JWT token for email verification.

  Args:
    data (dict): A dictionary containing user data to be encoded in the token.

  Returns:
    str: The encoded JWT email verification token.

  Raises:
    Exception: If an unexpected error occurs during token creation.
  """
  to_encode = data.copy()
  expire = datetime.now(UTC) + timedelta(days=7)
  to_encode.update({"iat": datetime.now(UTC), "exp": expire})
  token = jwt.encode(to_encode, config.JWT_SECRET, algorithm=config.JWT_ALGORITHM)
  return token

async def get_email_from_token(token: str):
  """
  Retrieves the email address from a JWT email verification token.

  Args:
    token (str): The JWT email verification token.

  Returns:
    str: The email address extracted from the token, or None if the token is invalid.

  Raises:
    HTTPException: If the token is invalid.
  """
  try:
    payload = jwt.decode(
      token, config.JWT_SECRET, algorithms=[config.JWT_ALGORITHM]
    )
    email = payload["sub"]
    return email
  except JWTError as e:
    raise HTTPException(
      status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
      detail="Неправильний токен для перевірки електронної пошти",
    )
  
def create_password_reset_token(data: dict):
  """
  Creates a JWT token for password reset.

  Args:
    data: A dictionary containing the user's email.

  Returns:
    A JWT token string.
  """
  to_encode = data.copy()
  expire = datetime.utcnow() + timedelta(hours=1)
  to_encode.update({"iat": datetime.utcnow(), "exp": expire})
  return jwt.encode(to_encode, config.JWT_SECRET, algorithm=config.JWT_ALGORITHM)

def verify_password_reset_token(token: str):
  """
  Verifies a JWT token for password reset.

  Args:
    token: The JWT token to be verified.

  Returns:
    The decoded payload of the token.

  Raises:
    HTTPException: If the token is expired or invalid.
  """
  try:
    payload = jwt.decode(token, config.JWT_SECRET, algorithms=[config.JWT_ALGORITHM])
    return payload
  except jwt.ExpiredSignatureError:
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Термін дії токена закінчився")
  except jwt.JWTError:
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Хибний токен")
