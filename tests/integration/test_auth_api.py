import pytest
from httpx import AsyncClient
from main import app
from database.db import override_get_db
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Base
from services.auth import create_email_token

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def get_test_db():
  try:
    db = TestingSessionLocal()
    yield db
  finally:
    db.close()

app.dependency_overrides[override_get_db] = get_test_db

@pytest.fixture
async def async_client():
  async with AsyncClient(app=app, base_url="http://test") as client:
    yield client


@pytest.mark.asyncio
async def test_register_user(async_client: AsyncClient):
  payload = {
    "email": "testuser@example.com",
    "username": "testuser",
    "password": "securepassword"
  }
  response = await async_client.post("/auth/register", json=payload)
  assert response.status_code == 201
  assert response.json()["email"] == payload["email"]

  response = await async_client.post("/auth/register", json=payload)
  assert response.status_code == 409
  assert response.json()["detail"] == "Користувач з таким email вже існує"


@pytest.mark.asyncio
async def test_login_user(async_client: AsyncClient):
  register_payload = {
    "email": "testlogin@example.com",
    "username": "testlogin",
    "password": "password123"
  }
  await async_client.post("/auth/register", json=register_payload)

  login_payload = {
    "username": "testlogin",
    "password": "password123"
  }
  response = await async_client.post("/auth/login", data=login_payload)
  assert response.status_code == 200
  assert "access_token" in response.json()

  login_payload["password"] = "wrongpassword"
  response = await async_client.post("/auth/login", data=login_payload)
  assert response.status_code == 401
  assert response.json()["detail"] == "Неправильний логін або пароль"


@pytest.mark.asyncio
async def test_confirm_email(async_client: AsyncClient):
  register_payload = {
      "email": "testuser@example.com",
      "username": "testuser",
      "password": "securepassword"
  }
  response = await async_client.post("/auth/register", json=register_payload)
  assert response.status_code == 201

  email_token_data = {"sub": "testuser@example.com"}
  token = create_email_token(email_token_data)

  response = await async_client.get(f"/auth/confirmed_email/{token}")
  assert response.status_code == 200
  assert response.json()["message"] == "Електронну пошту підтверджено"


@pytest.mark.asyncio
async def test_request_email(async_client: AsyncClient):
  register_payload = {
    "email": "testrequest@example.com",
    "username": "testrequest",
    "password": "password123"
  }
  await async_client.post("/auth/register", json=register_payload)

  request_email_payload = {"email": "testrequest@example.com"}
  response = await async_client.post("/auth/request_email", json=request_email_payload)
  assert response.status_code == 200
  assert response.json()["message"] == "Перевірте свою електронну пошту для підтвердження"
