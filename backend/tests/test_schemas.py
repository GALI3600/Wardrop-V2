import uuid
from datetime import datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.schemas.product import (
    GroupComparisonOut,
    ParsedProduct,
    ParseRequest,
    PriceHistoryOut,
    ProductGroupOut,
    ProductHistoryOut,
    ProductOut,
)
from app.schemas.user import (
    NotificationPreferences,
    Token,
    TrackRequest,
    UserCreate,
    UserLogin,
    UserOut,
)


# --- User Schemas ---


class TestUserCreate:
    def test_valid_user(self):
        user = UserCreate(email="test@example.com", password="secret123")
        assert user.email == "test@example.com"
        assert user.password == "secret123"

    def test_invalid_email_rejected(self):
        with pytest.raises(ValidationError):
            UserCreate(email="not-an-email", password="secret123")

    def test_missing_password_rejected(self):
        with pytest.raises(ValidationError):
            UserCreate(email="test@example.com")

    def test_missing_email_rejected(self):
        with pytest.raises(ValidationError):
            UserCreate(password="secret123")


class TestUserLogin:
    def test_valid_login(self):
        login = UserLogin(email="test@example.com", password="pass")
        assert login.email == "test@example.com"

    def test_invalid_email_rejected(self):
        with pytest.raises(ValidationError):
            UserLogin(email="bad", password="pass")


class TestUserOut:
    def test_valid_output(self):
        uid = uuid.uuid4()
        user = UserOut(id=uid, email="a@b.com", notify_email=True, notify_push=False)
        assert user.id == uid
        assert user.notify_push is False

    def test_missing_fields_rejected(self):
        with pytest.raises(ValidationError):
            UserOut(id=uuid.uuid4(), email="a@b.com")


class TestToken:
    def test_default_token_type(self):
        token = Token(access_token="abc123")
        assert token.token_type == "bearer"

    def test_custom_token_type(self):
        token = Token(access_token="abc123", token_type="custom")
        assert token.token_type == "custom"


class TestTrackRequest:
    def test_defaults(self):
        pid = uuid.uuid4()
        req = TrackRequest(product_id=pid)
        assert req.target_price is None
        assert req.notify_on_any_drop is True

    def test_with_target_price(self):
        pid = uuid.uuid4()
        req = TrackRequest(product_id=pid, target_price=99.90, notify_on_any_drop=False)
        assert req.target_price == 99.90
        assert req.notify_on_any_drop is False

    def test_invalid_product_id_rejected(self):
        with pytest.raises(ValidationError):
            TrackRequest(product_id="not-a-uuid")


class TestNotificationPreferences:
    def test_valid_preferences(self):
        prefs = NotificationPreferences(notify_email=True, notify_push=False)
        assert prefs.push_subscription is None

    def test_with_push_subscription(self):
        sub = {"endpoint": "https://push.example.com", "keys": {"p256dh": "x", "auth": "y"}}
        prefs = NotificationPreferences(notify_email=True, notify_push=True, push_subscription=sub)
        assert prefs.push_subscription["endpoint"] == "https://push.example.com"


# --- Product Schemas ---


class TestParseRequest:
    def test_valid_request(self):
        req = ParseRequest(html="<div>Hello</div>", url="https://example.com/product")
        assert req.html == "<div>Hello</div>"

    def test_missing_html_rejected(self):
        with pytest.raises(ValidationError):
            ParseRequest(url="https://example.com")

    def test_missing_url_rejected(self):
        with pytest.raises(ValidationError):
            ParseRequest(html="<div>Hello</div>")


class TestParsedProduct:
    def test_required_fields_only(self):
        p = ParsedProduct(name="iPhone 15", price=Decimal("4999.00"))
        assert p.currency == "BRL"
        assert p.available is True
        assert p.seller is None
        assert p.ean is None

    def test_all_fields(self):
        p = ParsedProduct(
            name="iPhone 15",
            price=Decimal("4999.00"),
            currency="USD",
            seller="Apple Store",
            image_url="https://img.com/iphone.jpg",
            marketplace="amazon",
            available=False,
            ean="7891234567890",
        )
        assert p.marketplace == "amazon"
        assert p.available is False

    def test_missing_name_rejected(self):
        with pytest.raises(ValidationError):
            ParsedProduct(price=Decimal("100.00"))

    def test_missing_price_rejected(self):
        with pytest.raises(ValidationError):
            ParsedProduct(name="iPhone 15")


class TestProductOut:
    def test_valid_output(self):
        uid = uuid.uuid4()
        now = datetime.utcnow()
        p = ProductOut(
            id=uid,
            url="https://amazon.com.br/dp/B0TEST",
            marketplace="amazon",
            name="iPhone 15",
            image_url=None,
            current_price=Decimal("4999.00"),
            currency="BRL",
            seller=None,
            ean=None,
            group_id=None,
            last_scraped_at=None,
            created_at=now,
        )
        assert p.id == uid
        assert p.current_price == Decimal("4999.00")

    def test_nullable_fields_accept_none(self):
        uid = uuid.uuid4()
        now = datetime.utcnow()
        p = ProductOut(
            id=uid,
            url="https://example.com",
            marketplace=None,
            name=None,
            image_url=None,
            current_price=None,
            currency="BRL",
            seller=None,
            ean=None,
            group_id=None,
            last_scraped_at=None,
            created_at=now,
        )
        assert p.name is None
        assert p.current_price is None


class TestPriceHistoryOut:
    def test_valid_history(self):
        now = datetime.utcnow()
        h = PriceHistoryOut(price=Decimal("199.90"), seller="Loja", available=True, scraped_at=now)
        assert h.price == Decimal("199.90")

    def test_missing_fields_rejected(self):
        with pytest.raises(ValidationError):
            PriceHistoryOut(price=Decimal("199.90"))


class TestProductGroupOut:
    def test_valid_group(self):
        gid = uuid.uuid4()
        pid = uuid.uuid4()
        now = datetime.utcnow()
        group = ProductGroupOut(
            id=gid,
            canonical_name="iPhone 15",
            ean="7891234567890",
            products=[
                ProductOut(
                    id=pid,
                    url="https://example.com",
                    marketplace="amazon",
                    name="iPhone 15",
                    image_url=None,
                    current_price=Decimal("4999.00"),
                    currency="BRL",
                    seller=None,
                    ean="7891234567890",
                    group_id=gid,
                    last_scraped_at=None,
                    created_at=now,
                )
            ],
        )
        assert len(group.products) == 1

    def test_empty_products_list(self):
        gid = uuid.uuid4()
        group = ProductGroupOut(id=gid, canonical_name="Test", ean=None, products=[])
        assert group.products == []


class TestProductHistoryOut:
    def test_valid_output(self):
        pid = uuid.uuid4()
        now = datetime.utcnow()
        product = ProductOut(
            id=pid,
            url="https://example.com",
            marketplace="amazon",
            name="Test",
            image_url=None,
            current_price=Decimal("100.00"),
            currency="BRL",
            seller=None,
            ean=None,
            group_id=None,
            last_scraped_at=None,
            created_at=now,
        )
        history = ProductHistoryOut(product=product, history=[])
        assert history.product.id == pid
        assert history.history == []
