import logging
from datetime import datetime, timedelta
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.db.database import get_db
from app.models.user import User

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(user_id: UUID) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        user_id = payload.get("sub")
        if user_id is None:
            logger.warning("Token missing 'sub' claim")
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        logger.warning("Invalid JWT token provided")
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.execute(
        select(User).where(User.id == UUID(user_id))
    ).scalar_one_or_none()

    if user is None:
        logger.warning("Token references non-existent user: %s", user_id)
        raise HTTPException(status_code=401, detail="User not found")

    return user


def get_optional_user(
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User | None:
    """Returns user if authenticated, None otherwise. Does not raise."""
    if token is None:
        return None
    try:
        return get_current_user(token=token, db=db)
    except HTTPException:
        return None
