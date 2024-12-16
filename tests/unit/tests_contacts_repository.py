from unittest.mock import AsyncMock

from database.models import Contact, User
from repository.contacts import ContactRepository

class TestContactRepository:
  def setUp(self):
    self.session = AsyncMock()
    self.user = User(id=1)
    self.repository = ContactRepository(self.session)

  def create_mock_contact(self, **kwargs):
    return Contact(id=1, user=self.user, **kwargs)
  
  async def test_get_contacts(self):
    contacts = [self.create_mock_contact(), self.create_mock_contact()]
    self.session.execute.return_value = AsyncMock()
    self.session.execute.return_value.scalars.return_value.all.return_value = contacts

    returned_contacts = await self.repository.get_contacts(skip=0, limit=10, user=self.user)

    self.session.execute.assert_called_once()
    assert len(returned_contacts) == 2

  async def test_get_contact_by_id_existing(self):
    contact = self.create_mock_contact()
    self.session.execute.return_value = AsyncMock()
    self.session.execute.return_value.scalar_one_or_none.return_value = contact

    returned_contact = await self.repository.get_contact_by_id(1, self.user)

    self.session.execute.assert_called_once()
    assert returned_contact is contact
  
  async def test_get_contact_by_id_not_found(self):
    self.session.execute.return_value = AsyncMock()
    self.session.execute.return_value.scalar_one_or_none.return_value = None

    returned_contact = await self.repository.get_contact_by_id(1, self.user)

    self.session.execute.assert_called_once()
    assert returned_contact is None
