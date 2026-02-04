from sqlalchemy import Column, Integer, String, Boolean
from database import Base

class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False) 
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    phone_number = Column(String,unique=True, nullable=False)
    permanent_address = Column(String, nullable=False)

    password_hash = Column(String, nullable=False)  
    is_active = Column(Boolean, default=True)  
