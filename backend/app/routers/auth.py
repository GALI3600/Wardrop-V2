import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.schemas.user import Token, UserCreate, UserLogin, UserOut
from app.services.auth import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/register", response_model=Token, status_code=201)
def register(data: UserCreate, db: Session = Depends(get_db)):
    existing = db.execute(
        select(User).where(User.email == data.email)
    ).scalar_one_or_none()

    if existing:
        logger.warning("Registration attempt with existing email: %s", data.email)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    user = User(
        email=data.email,
        password_hash=hash_password(data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    logger.info("New user registered: %s (id: %s)", user.email, user.id)
    token = create_access_token(user.id)
    return Token(access_token=token)


@router.post("/login", response_model=Token)
def login(data: UserLogin, db: Session = Depends(get_db)):
    user = db.execute(
        select(User).where(User.email == data.email)
    ).scalar_one_or_none()

    if not user or not verify_password(data.password, user.password_hash):
        logger.warning("Failed login attempt for email: %s", data.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    logger.info("User logged in: %s", data.email)
    token = create_access_token(user.id)
    return Token(access_token=token)


@router.get("/me", response_model=UserOut)
def get_me(user: User = Depends(get_current_user)):
    return user
