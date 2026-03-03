import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.schemas.user import NotificationPreferences, UserOut
from app.services.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/preferences", response_model=NotificationPreferences)
def get_preferences(user: User = Depends(get_current_user)):
    return NotificationPreferences(
        notify_email=user.notify_email,
        notify_push=user.notify_push,
        push_subscription=user.push_subscription,
    )


@router.put("/preferences", response_model=UserOut)
def update_preferences(
    prefs: NotificationPreferences,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user.notify_email = prefs.notify_email
    user.notify_push = prefs.notify_push
    if prefs.push_subscription is not None:
        user.push_subscription = prefs.push_subscription
    db.commit()
    db.refresh(user)
    logger.info(
        "User %s updated notification preferences: email=%s, push=%s",
        user.id, prefs.notify_email, prefs.notify_push,
    )
    return user
