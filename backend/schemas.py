from pydantic import BaseModel, EmailStr, Field, field_validator



class AccountBase(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    email: EmailStr
    phone_number: str = Field(..., min_length=10, max_length=10)
    permanent_address: str = Field(..., min_length=5, max_length=200)
    username: str | None = None 

    class Config:
        from_attributes = True

    @field_validator("phone_number")
    def phone_must_be_digits(cls, v):
        if not v.isdigit():
            raise ValueError("Phone number must contain only digits")
        return v

class AccountCreate(AccountBase):
    password: str = Field(..., min_length=6)  # user provides password

class AccountResponse(AccountBase):
    id: int
    is_active: bool

class LoginRequest(BaseModel):
    email: EmailStr
    password: str