import pytest
from httpx import AsyncClient
from fastapi import status

@pytest.mark.asyncio
async def test_create_contact(async_client: AsyncClient, test_user):
  contact_payload = {
    "first_name": "John",
    "last_name": "Doe",
    "email": "johndoe@example.com",
    "phone": "1234567890",
    "birthday": "1990-01-01",
    "address": "123 Test Street",
  }
  headers = {"Authorization": f"Bearer {test_user['access_token']}"}

  response = await async_client.post("/contacts/", json=contact_payload, headers=headers)
  assert response.status_code == status.HTTP_201_CREATED
  assert response.json()["first_name"] == "John"
  assert response.json()["email"] == "johndoe@example.com"


@pytest.mark.asyncio
async def test_read_contacts(async_client: AsyncClient, test_user):
  headers = {"Authorization": f"Bearer {test_user['access_token']}"}
  response = await async_client.get("/contacts/?first_name=John", headers=headers)
  assert response.status_code == status.HTTP_200_OK
  assert isinstance(response.json(), list)
  assert len(response.json()) > 0
  assert response.json()[0]["first_name"] == "John"


@pytest.mark.asyncio
async def test_read_contact_by_id(async_client: AsyncClient, test_user, test_contact):
  headers = {"Authorization": f"Bearer {test_user['access_token']}"}
  response = await async_client.get(f"/contacts/{test_contact['id']}", headers=headers)
  assert response.status_code == status.HTTP_200_OK
  assert response.json()["id"] == test_contact["id"]
  assert response.json()["first_name"] == test_contact["first_name"]


@pytest.mark.asyncio
async def test_update_contact(async_client: AsyncClient, test_user, test_contact):
  updated_payload = {
    "first_name": "Jane",
    "last_name": "Doe",
    "email": "janedoe@example.com",
    "phone": "0987654321",
    "birthday": "1995-01-01",
    "address": "456 Test Lane",
  }
  headers = {"Authorization": f"Bearer {test_user['access_token']}"}

  response = await async_client.put(f"/contacts/{test_contact['id']}", json=updated_payload, headers=headers)
  assert response.status_code == status.HTTP_200_OK
  assert response.json()["first_name"] == "Jane"
  assert response.json()["email"] == "janedoe@example.com"


@pytest.mark.asyncio
async def test_remove_contact(async_client: AsyncClient, test_user, test_contact):
  headers = {"Authorization": f"Bearer {test_user['access_token']}"}

  response = await async_client.delete(f"/contacts/{test_contact['id']}", headers=headers)
  assert response.status_code == status.HTTP_200_OK
  assert response.json()["id"] == test_contact["id"]

  response = await async_client.get(f"/contacts/{test_contact['id']}", headers=headers)
  assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_upcoming_birthdays(async_client: AsyncClient, test_user):
  headers = {"Authorization": f"Bearer {test_user['access_token']}"}

  response = await async_client.get("/contacts/birthdays/", headers=headers)
  assert response.status_code == status.HTTP_200_OK
  assert isinstance(response.json(), list)
  if response.json():
    assert "birthday" in response.json()[0]


@pytest.fixture
async def test_user(async_client: AsyncClient):
  user_payload = {
    "email": "testuser@example.com",
    "username": "testuser",
    "password": "securepassword"
  }
  await async_client.post("/auth/register", json=user_payload)
  response = await async_client.post(
    "/auth/login", data={"username": "testuser", "password": "securepassword"}
  )
  return response.json()


@pytest.fixture
async def test_contact(async_client: AsyncClient, test_user):
  contact_payload = {
    "first_name": "John",
    "last_name": "Doe",
    "email": "johndoe@example.com",
    "phone": "1234567890",
    "birthday": "1990-01-01",
    "address": "123 Test Street",
  }
  headers = {"Authorization": f"Bearer {test_user['access_token']}"}
  response = await async_client.post("/contacts/", json=contact_payload, headers=headers)
  return response.json()
