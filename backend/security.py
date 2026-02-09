
from passlib.context import CryptContext
import hashlib

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def mask_aadhaar(aadhaar: str) -> str:
    return "XXXX-XXXX-" + aadhaar[-4:]

def mask_pan(pan: str) -> str:
    return pan[:5] + "****"


def hash_value(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()
