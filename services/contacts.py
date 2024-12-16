from sqlalchemy.ext.asyncio import AsyncSession

from repository.contacts import ContactRepository
from schemas import ContactBase
from database.models import User

class ContactService:
  def __init__(self, db: AsyncSession):
    self.contact_repository = ContactRepository(db)

  async def create_contact(self, body: ContactBase, user: User):
    return await self.contact_repository.create_contact(body, user)

  async def get_contacts(self, skip: int, limit: int, user: User):
    return await self.contact_repository.get_contacts(skip, limit, user)

  async def get_contact(self, contact_id: int, user: User):
    return await self.contact_repository.get_contact_by_id(contact_id, user)

  async def update_contact(self, contact_id: int, body: ContactBase, user: User):
    return await self.contact_repository.update_contact(contact_id, body, user)

  async def remove_contact(self, contact_id: int, user: User):
    return await self.contact_repository.remove_contact(contact_id, user)

  async def search_contacts(
    self, skip: int, limit: int, first_name: str | None, last_name: str | None, email: str | None, user: User
  ):
    return await self.contact_repository.search_contacts(skip, limit, first_name, last_name, email, user)
  
  async def get_upcoming_birthdays(self, user: User):
    return await self.contact_repository.get_upcoming_birthdays(user)

