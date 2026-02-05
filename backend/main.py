from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from database import engine, SessionLocal
import models, schemas
from security import verify_password, hash_password
from auth import create_access_token, get_current_user, admin_required

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Banking API")

# ---------------- DATABASE SESSION ----------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------------- ROOT ----------------
@app.get("/")
def root():
    return {"message": "Banking backend is running"}

# ---------------- USER CREATE ----------------
@app.post("/users", response_model=schemas.AccountResponse)
def create_user(account: schemas.AccountCreate, db: Session = Depends(get_db)):

    hashed_password = hash_password(account.password)

    new_user = models.Account(
        first_name=account.first_name,
        last_name=account.last_name,
        email=account.email,
        phone_number=account.phone_number,
        username=account.username,
        permanent_address=account.permanent_address,
        password_hash=hashed_password
    )

    db.add(new_user)

    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        if "email" in str(e.orig):
            raise HTTPException(status_code=400, detail="Email already exists")
        if "phone_number" in str(e.orig):
            raise HTTPException(status_code=400, detail="Phone number already exists")
        raise HTTPException(status_code=400, detail="User already exists")

    db.refresh(new_user)
    return new_user

# ---------------- LOGIN ----------------
@app.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.query(models.Account).filter(
        models.Account.email == form_data.username,
        models.Account.is_active == True
    ).first()

    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": str(user.id)})

    return {"access_token": token, "token_type": "bearer"}

# ---------------- USER SELF ----------------
@app.get("/users/me", response_model=schemas.AccountResponse)
def get_me(current_user: models.Account = Depends(get_current_user)):
    return current_user

@app.put("/users/me", response_model=schemas.AccountResponse)
def update_me(
    data: schemas.AccountUpdate,
    db: Session = Depends(get_db),
    current_user: models.Account = Depends(get_current_user)
):
    # Reload current_user from the same session
    user = db.query(models.Account).filter(models.Account.id == current_user.id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    for field, value in data.dict(exclude_unset=True).items():
        if field == "password":
            user.password_hash = hash_password(value)
        else:
            setattr(user, field, value)

    db.commit()
    db.refresh(user)
    return user

# ---------------- ADMIN ----------------
@app.get("/admin/users", response_model=list[schemas.AccountResponse])
def admin_get_users(
    db: Session = Depends(get_db),
    admin: models.Account = Depends(admin_required)
):
    return db.query(models.Account).all()

@app.put("/admin/users/{user_id}", response_model=schemas.AccountResponse)
def admin_update_user(
    user_id: int,
    data: schemas.AccountUpdate,
    db: Session = Depends(get_db),
    admin: models.Account = Depends(admin_required)
):
    user = db.query(models.Account).filter(models.Account.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    for field, value in data.dict(exclude_unset=True).items():
        if field == "password":
            user.password_hash = hash_password(value)
        else:
            setattr(user, field, value)

    db.commit()
    db.refresh(user)
    return user

@app.delete("/admin/users/{user_id}")
def admin_delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: models.Account = Depends(admin_required)
):
    user = db.query(models.Account).filter(models.Account.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = False
    db.commit()
    return {"message": "User deactivated"}
