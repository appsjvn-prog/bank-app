from fastapi import FastAPI, Depends, HTTPException, Form, UploadFile, File
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import os

from database import engine, SessionLocal
import models, schemas
from security import (
    verify_password,
    hash_password,
    mask_aadhaar,
    mask_pan,
    hash_value,
)
from auth import create_access_token, get_current_user, admin_required

# APP INIT

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Banking API")


# DATABASE SESSION


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ROOT

@app.get("/")
def root():
    return {"message": "Banking backend is running"}

# USER REGISTRATION
# 

@app.post("/users", response_model=schemas.AccountResponse)
def create_user(
    account: schemas.AccountCreate,
    db: Session = Depends(get_db),
):
    hashed_password = hash_password(account.password)

    new_user = models.Account(
        first_name=account.first_name,
        last_name=account.last_name,
        email=account.email,
        phone_number=account.phone_number,
        permanent_address=account.permanent_address,
        username=account.username,
        date_of_birth=account.date_of_birth,
        password_hash=hashed_password,
        is_active=True,
        role="user",
        kyc_status="not_submitted",
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


# LOGIN


@app.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = (
        db.query(models.Account)
        .filter(
            models.Account.email == form_data.username,
            models.Account.is_active == True,
        )
        .first()
    )

    # 1️⃣ User not found
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # 2️⃣ Blocked check FIRST
    if user.is_blocked:
        raise HTTPException(
            status_code=403,
            detail="Account is blocked. Contact admin."
        )

    # 3️⃣ Wrong password
    if not verify_password(form_data.password, user.password_hash):
        user.failed_attempts += 1

        if user.failed_attempts >= 3:
            user.is_blocked = True

        db.commit()
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # 4️⃣ Successful login
    user.failed_attempts = 0
    db.commit()

    token = create_access_token({"sub": str(user.id)})

    return {
        "access_token": token,
        "token_type": "bearer",
    }

# USER SELF

@app.get("/users/me", response_model=schemas.AccountResponse)
def get_me(
    current_user: models.Account = Depends(get_current_user),
):
    return current_user


@app.put("/users/me", response_model=schemas.AccountResponse)
def update_me(
    data: schemas.AccountUpdate,
    db: Session = Depends(get_db),
    current_user: models.Account = Depends(get_current_user),
):
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

# ADMIN – VIEW ALL USERS

@app.get("/admin/users", response_model=list[schemas.AdminAccountResponse])
def admin_get_all_users(
    db: Session = Depends(get_db),
    admin: models.Account = Depends(admin_required),
):
    return db.query(models.Account).all()



# ADMIN – SOFT DELETE USER

@app.delete("/admin/users/{user_id}")
def admin_soft_delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: models.Account = Depends(admin_required),
):
    user = db.query(models.Account).filter(models.Account.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = False
    db.commit()

    return {"message": "User deactivated successfully"}


# KYC SUBMISSION

@app.post("/kyc/submit")
def submit_kyc(
    aadhaar_number: str = Form(..., min_length=12, max_length=12),
    pan_number: str = Form(..., min_length=10, max_length=10),
    document: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.Account = Depends(get_current_user),
):
    # IMPORTANT: reattach user to SAME session
    user = db.query(models.Account).filter(models.Account.id == current_user.id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.kyc_status == "approved":
        raise HTTPException(status_code=400, detail="KYC already approved")

    # Hash + Mask (NO RAW STORAGE)
    user.aadhaar_hash = hash_value(aadhaar_number)
    user.aadhaar_masked = mask_aadhaar(aadhaar_number)

    user.pan_hash = hash_value(pan_number)
    user.pan_masked = mask_pan(pan_number)

    # Save document
    os.makedirs("uploads/kyc", exist_ok=True)
    file_path = f"uploads/kyc/{user.id}_{document.filename}"

    with open(file_path, "wb") as f:
        f.write(document.file.read())

    user.kyc_document_path = file_path
    user.kyc_status = "pending"

    db.commit()

    return {
        "message": "KYC submitted successfully",
        "kyc_status": user.kyc_status,
    }

# -------------------------------------------------
# ADMIN – UPDATE KYC STATUS
# -------------------------------------------------

@app.put("/admin/kyc/{user_id}")
def admin_update_kyc_status(
    user_id: int,
    status: str,
    db: Session = Depends(get_db),
    admin: models.Account = Depends(admin_required),
):
    if status not in ["approved", "rejected"]:
        raise HTTPException(status_code=400, detail="Invalid KYC status")

    user = db.query(models.Account).filter(models.Account.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.kyc_status != "pending":
        raise HTTPException(
            status_code=400,
            detail="KYC not submitted or already processed"
        )

    if not user.kyc_document_path:
        raise HTTPException(
            status_code=400,
            detail="No KYC document uploaded"
        )

    user.kyc_status = status
    db.commit()

    return {"message": f"KYC status updated to {status}"}

@app.put("/admin/users/{user_id}/unblock")
def admin_unblock_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: models.Account = Depends(admin_required),
):
    user = db.query(models.Account).filter(models.Account.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.is_blocked:
        raise HTTPException(
            status_code=400,
            detail="User is not blocked"
        )

    user.is_blocked = False
    user.failed_attempts = 0
    db.commit()

    return {"message": "User unblocked successfully"}


