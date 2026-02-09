from sqlalchemy import Column, Integer, String, Boolean, Date
from database import Base

class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    date_of_birth = Column(Date, nullable=False)
    phone_number = Column(String, unique=True, nullable=False)
    permanent_address = Column(String, nullable=False)

    password_hash = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    role = Column(String, default="user")  

    # KYC fields
    aadhaar_hash = Column(String(255), nullable=True)
    aadhaar_masked = Column(String(20), nullable=True)
    pan_hash = Column(String(255), nullable=True)
    pan_masked = Column(String(20), nullable=True)
    kyc_status = Column(String(20), default="not_submitted")

    kyc_document_path = Column(String(255), nullable=True)

    failed_attempts = Column(Integer, default=0)
    is_blocked = Column(Boolean, default=False)

    failed_attempts = Column(Integer, default=0, nullable=False)
    is_blocked = Column(Boolean, default=False, nullable=False)


