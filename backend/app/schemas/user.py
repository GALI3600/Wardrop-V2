from uuid import UUID

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: UUID
    email: str
    notify_email: bool
    notify_push: bool

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TrackRequest(BaseModel):
    product_id: UUID
    target_price: float | None = None
    notify_on_any_drop: bool = True


class NotificationPreferences(BaseModel):
    notify_email: bool
    notify_push: bool
    push_subscription: dict | None = None
