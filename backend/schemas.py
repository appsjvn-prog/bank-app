from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import date
import re

class AccountBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone_number: str
    permanent_address: str
    username: Optional[str] = None
    date_of_birth: date

    class Config:
        from_attributes = True

    @field_validator("phone_number")
    def phone_digits_only(cls, v):
        if not v.isdigit() or len(v) != 10:
            raise ValueError("Phone number must be 10 digits")
        return v

    @field_validator("date_of_birth")
    def check_age(cls, dob):
        today = date.today()
        age = today.year - dob.year
        if (today.month, today.day) < (dob.month, dob.day):
            age -= 1
        if age < 18:
            raise ValueError("Must be at least 18")
        return dob

class AccountCreate(AccountBase):
    password: str = Field(..., min_length=6)

class AccountUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    permanent_address: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = Field(None, min_length=6)

class AccountResponse(AccountBase):
    #id: int
    #is_active: bool
    #role: str
    kyc_status: Optional[str] = None
    aadhaar_masked: Optional[str] = None
    pan_masked: Optional[str] = None


class AdminAccountResponse(AccountBase):
    id: int
    is_active: bool
    role: str

    kyc_status: Optional[str] = None
    aadhaar_masked: Optional[str] = None
    pan_masked: Optional[str] = None

    failed_attempts: int
    is_blocked: bool


class KYCSubmit(BaseModel):
    aadhaar_number: str
    pan_number: str
    last_name: str

    @field_validator("pan_number", mode="after")
    def validate_pan(cls, pan: str, info):
        # last_name will now be available
        last_name = info.data.get("last_name")

        # Basic length check
        if len(pan) != 10:
            raise ValueError("PAN must be exactly 10 characters")

        # Pattern: first 3 letters, 1 type/status letter, 1 last name initial, 4 digits, 1 checksum letter
        pattern = r"^[A-Z]{3}[A-Z][A-Z][0-9]{4}[A-Z]$"
        if not re.match(pattern, pan):
            raise ValueError("PAN format is invalid")

        # 5th letter must match first letter of last name
        if last_name and pan[4] != last_name[0].upper():
            raise ValueError("PAN format does not match last name initial")

        return pan



