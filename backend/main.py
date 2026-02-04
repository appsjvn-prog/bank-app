from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from database import engine, SessionLocal
import models, schemas
from schemas import LoginRequest
from security import verify_password
from auth import create_access_token

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Banking API")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def root():
    return {"message": "Banking backend is running"}


@app.post("/users", response_model=schemas.AccountResponse)
def create_users(account: schemas.AccountCreate, db: Session = Depends(get_db)):
   
    if db.query(models.Account).filter(models.Account.email == account.email).first():
        raise HTTPException(
            status_code=400, detail="Account already exists with this email"
            )
    
    if db.query(models.Account).filter(models.Account.phone_number == account.phone_number).first():
        raise HTTPException(
            status_code=400,
            detail="Account already exists with this phone number"
        )
    
    if account.username:
        if db.query(models.Account).filter(
            models.Account.username == account.username
        ).first():
            raise HTTPException(
                status_code=400,
                detail="Username already taken"
            )


    
    hashed_password = pwd_context.hash(account.password)

    
    new_account = models.Account(
        first_name=account.first_name,
        last_name=account.last_name,
        email=account.email,
        phone_number=account.phone_number,
        username=account.username,
        permanent_address=account.permanent_address,
        password_hash=hashed_password
    )

    db.add(new_account)
    db.commit()
    db.refresh(new_account)
    return new_account


@app.get("/users", response_model=list[schemas.AccountResponse])
def get_users(db: Session = Depends(get_db)):
    return db.query(models.Account).filter(models.Account.is_active == True).all()


@app.delete("/users/{account_id}", response_model=schemas.AccountResponse)
def soft_delete_account(account_id: int, db: Session = Depends(get_db)):
    account = db.query(models.Account).filter(
        models.Account.id == account_id,
        models.Account.is_active == True
    ).first()

    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    account.is_active = False
    db.commit()
    db.refresh(account)
    return account

@app.post("/login")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.Account).filter(
        models.Account.email == data.email,
        models.Account.is_active == True
    ).first()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    access_token = create_access_token(
        data={"sub": str(user.id)}
    )

    return {
        "message": "Login successful",
        "user_id": user.id,
        "email": user.email,
        "access_token": access_token,
        "token_type": "bearer"
    }
