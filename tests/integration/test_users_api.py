import pytest
from fastapi import status
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_user_me(async_client: AsyncClient, test_user):
  headers = {"Authorization": f"Bearer {test_user['access_token']}"}
  response = await async_client.get("/users/me", headers=headers)

  assert response.status_code == status.HTTP_200_OK
  assert response.json()["id"] == test_user["id"]
  assert response.json()["email"] == test_user["email"]


@pytest.mark.asyncio
async def test_get_user_me_rate_limit(async_client: AsyncClient, test_user):
  headers = {"Authorization": f"Bearer {test_user['access_token']}"}

  for _ in range(10):
    response = await async_client.get("/users/me", headers=headers)
    assert response.status_code == status.HTTP_200_OK

  response = await async_client.get("/users/me", headers=headers)
  assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
  assert "rate limit exceeded" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_update_avatar_valid(async_client: AsyncClient, test_user, mocker):
  headers = {"Authorization": f"Bearer {test_user['access_token']}"}

  mock_upload = mocker.patch("cloudinary.uploader.upload")
  mock_upload.return_value = {"secure_url": "http://example.com/avatar.jpg"}

  with open("tests/assets/avatar.png", "rb") as file:
    response = await async_client.put(
      "/users/avatar",
      headers=headers,
      files={"file": ("avatar.png", file, "image/png")},
    )

  assert response.status_code == status.HTTP_200_OK
  assert response.json()["avatar_url"] == "http://example.com/avatar.jpg"
