from unittest.mock import AsyncMock

from database.models import User
from schemas import UserCreate
from repository.users import UserRepository


class TestUserRepository:
  def setUp(self):
    self.session = AsyncMock()
    self.repository = UserRepository(self.session)

  def create_mock_user(self, **kwargs):
    return User(id=1, **kwargs)

  async def test_get_user_by_id_existing(self):
    user = self.create_mock_user()
    self.session.execute.return_value = AsyncMock()
    self.session.execute.return_value.scalar_one_or_none.return_value = user

    result = await self.repository.get_user_by_id(1)
    assert result == user

  async def test_get_user_by_id_not_found(self):
    self.session.execute.return_value = AsyncMock()
    self.session.execute.return_value.scalar_one_or_none.return_value = None

    result = await self.repository.get_user_by_id(1)
    assert result is None

  async def test_create_user(self):
    user_data = UserCreate(username="testuser", email="test@example.com", password="password123")
    self.session.add.called = AsyncMock()
    self.session.commit.called = AsyncMock()
    self.session.refresh.called = AsyncMock()
    self.session.execute.return_value = AsyncMock()
    self.session.execute.return_value.scalar_one_or_none.return_value = self.create_mock_user(**user_data.dict())

    user = await self.repository.create_user(user_data)

    self.session.add.assert_called_once()
    self.session.commit.assert_called_once()
    self.session.refresh.assert_called_once()
    assert user.username == user_data.username
    assert user.email == user_data.email

  async def test_confirmed_email(self):
    user = self.create_mock_user(email="test@example.com", confirmed=False)
    self.session.execute.return_value = AsyncMock()
    self.session.execute.return_value.scalar_one_or_none.return_value = user
    self.session.commit.called = AsyncMock()

    await self.repository.confirmed_email("test@example.com")

    self.session.execute.assert_called_once()
    self.session.commit.assert_called_once()
    assert user.confirmed
