from datetime import datetime

from sqlalchemy import Column, Integer, String, Boolean, func, Enum
from sqlalchemy.orm import relationship, mapped_column, Mapped, DeclarativeBase
from sqlalchemy.sql.schema import ForeignKey
from sqlalchemy.sql.sqltypes import DateTime
import enum

class Role(str, enum.Enum):
  user = "user"
  admin = "admin"

class Base(DeclarativeBase):
    pass

class Contact(Base):
  __tablename__ = "contacts"
  id: Mapped[int] = mapped_column(Integer, primary_key=True)
  first_name: Mapped[str] = mapped_column(String(50), nullable=False)
  last_name: Mapped[str] = mapped_column(String(50), nullable=False)
  email: Mapped[str] = mapped_column(String(50), nullable=False)
  phone: Mapped[str] = mapped_column(String(50), nullable=False)
  birthday: Mapped[datetime] = mapped_column(
    "birthday", DateTime, default=func.now()
  )
  user_id = Column(
    "user_id", ForeignKey("users.id", ondelete="CASCADE"), default=None
  )
  user = relationship("User", backref="contacts")

class User(Base):
  __tablename__ = "users"
  id = Column(Integer, primary_key=True)
  username = Column(String, unique=True)
  email = Column(String, unique=True)
  hashed_password = Column(String)
  created_at = Column(DateTime, default=func.now())
  avatar = Column(String(255), nullable=True)
  confirmed = Column(Boolean, default=False)
  avatar = Column(String(255), nullable=True)
  role = Column(Enum(Role), default=Role.user)
