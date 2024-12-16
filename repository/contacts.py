from typing import List

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta

from database.models import Contact, User
from schemas import ContactBase

class ContactRepository:
  def __init__(self, session: AsyncSession):
    """
    Initialize a ContactsRepository.

    Args:
      session: An AsyncSession object connected to the database.
    """
    self.db = session

  async def get_contacts(self, skip: int, limit: int, user: User) -> List[Contact]:
    """
    Get a list of Contacts owned by `user` with pagination.

    Args:
      skip: The number of Contacts to skip.
      limit: The maximum number of Contacts to return.
      user: The owner of the Contacts to retrieve.

    Returns:
      A list of Contacts.
    """
    stmt = select(Contact).filter_by(user=user).offset(skip).limit(limit)
    contacts = await self.db.execute(stmt)
    return contacts.scalars().all()

  async def get_contact_by_id(self, contact_id: int, user: User) -> Contact | None:
    """
    Get a Contact by its id.

    Args:
      contact_id: The id of the Contact to retrieve.
      user: The owner of the Contact to retrieve.

    Returns:
      The Contact with the specified id, or None if no such Contact exists.
    """
    stmt = select(Contact).filter_by(id=contact_id, user=user)
    contact = await self.db.execute(stmt)
    return contact.scalar_one_or_none()

  async def create_contact(self, body: ContactBase, user: User) -> Contact:
    """
    Create a new Contact with the given attributes.

    Args:
      body: A ContactModel with the attributes to assign to the Contact.
      user: The User who owns the Contact.

    Returns:
      A Contact with the assigned attributes.
    """
    if body.birthday and body.birthday.tzinfo:
      body.birthday = body.birthday.replace(tzinfo=None)
    contact = Contact(
      **body.model_dump(exclude_unset=True),
      user=user
    )
    self.db.add(contact)
    await self.db.commit()
    await self.db.refresh(contact)
    return await self.get_contact_by_id(contact.id, user)

  async def remove_contact(self, contact_id: int, user: User) -> Contact | None:
    """
    Delete a Contact by its id.

    Args:
      contact_id: The id of the Contact to delete.
      user: The owner of the Contact to delete.

    Returns:
      The deleted Contact, or None if no Contact with the given id exists.
    """
    contact = await self.get_contact_by_id(contact_id, user)
    if contact:
      await self.db.delete(contact)
      await self.db.commit()
    return contact

  async def update_contact(
    self, contact_id: int, body: ContactBase, user: User) -> Contact | None:
    """
    Update a Contact with the given attributes.

    Args:
      contact_id: The id of the Contact to update.
      body: A ContactUpdate with the attributes to assign to the Contact.
      user: The User who owns the Contact.

    Returns:
      The updated Contact, or None if no Contact with the given id exists.
    """
    if body.birthday and body.birthday.tzinfo:
      body.birthday = body.birthday.replace(tzinfo=None)
    contact = await self.get_contact_by_id(contact_id, user)
    if contact:
      for key, value in body.dict(exclude_unset=True).items():
        setattr(contact, key, value)

      await self.db.commit()
      await self.db.refresh(contact)

    return contact

  async def search_contacts(
      self, skip: int, limit: int, first_name: str | None, last_name: str | None, email: str | None,  user: User,
  ) -> List[Contact]:
    """
    Search Contact with the given attributes.

    Args:
      skip: The number of Contacts to skip.
      limit: The maximum number of Contacts to return.
      first_name: The first name of the Contact.
      last_name: The last name of the Contact.
      email: The email of the Contact.
      user: The User who owns the Contact.

    Returns:
      The Contact that fits search query or None if no such Contact exists.
    """
    stmt = select(Contact).filter_by(user=user).offset(skip).limit(limit)

    if first_name or last_name or email:
      filters = []
      if first_name:
        filters.append(Contact.first_name.ilike(f"%{first_name}%"))
      if last_name:
        filters.append(Contact.last_name.ilike(f"%{last_name}%"))
      if email:
        filters.append(Contact.email.ilike(f"%{email}%"))
      stmt = stmt.filter(or_(*filters))

    results = await self.db.execute(stmt)
    return results.scalars().all()
  
  async def get_upcoming_birthdays(self, user: User) -> List[Contact]:
    """
    Retrieves contacts with birthdays within the next week.

    Args:
      user: The user whose contacts to check.

    Returns:
      A list of contacts with upcoming birthdays.
    """
    today = datetime.utcnow()
    next_week = today + timedelta(days=7)

    stmt = select(Contact).filter(
      and_(
        Contact.user == user,
        Contact.birthday >= today.replace(hour=0, minute=0, second=0, microsecond=0),
        Contact.birthday <= next_week.replace(hour=23, minute=59, second=59, microsecond=999999),
      )
    )

    results = await self.db.execute(stmt)
    return results.scalars().all()

