from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional

class AccountBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone_number: str
    permanent_address: str
    username: str | None = None

    class Config:
        from_attributes = True

    @field_validator("phone_number")
    def phone_digits_only(cls, v):
        if not v.isdigit():
            raise ValueError("Phone number must contain only digits")
        
        if len(v) != 10:
            raise ValueError("Phone number must be exactly 10 digits")
        
        return v

class AccountCreate(AccountBase):
    password: str = Field(..., min_length=6,max_length=72)

class AccountUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    phone_number: str | None = None
    permanent_address: str | None = None
    username: str | None = None
    password: str | None = Field(None, min_length=6, max_length=72)


class AccountResponse(AccountBase):
    id: int
    is_active: bool
    role: str


