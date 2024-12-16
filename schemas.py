from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, EmailStr

class ContactBase(BaseModel):
  first_name: str = Field(max_length=50)
  last_name: str = Field(max_length=50)
  email: str = Field(max_length=50)
  phone: str = Field(max_length=50)
  birthday: datetime | None

class ContactResponse(ContactBase):
  id: int

  model_config = ConfigDict(from_attributes=True)

class User(BaseModel):
  id: int
  username: str
  email: str
  avatar: str

  class Config:
    orm_mode = True
  
class UserCreate(BaseModel):
  username: str
  email: str
  password: str
  role: str = "user"

class Token(BaseModel):
  access_token: str
  token_type: str

class RequestEmail(BaseModel):
  email: EmailStr

class PasswordResetRequest(BaseModel):
  email: EmailStr

class PasswordReset(BaseModel):
  token: str
  new_password: str
