import uuid
from datetime import datetime
from decimal import Decimal
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import Base, get_db
from app.main import app

# Patch scheduler globally so TestClient lifespan doesn't fail
_scheduler_start = patch("app.main.start_scheduler")
_scheduler_stop = patch("app.main.stop_scheduler")
_scheduler_start.start()
_scheduler_stop.start()
from app.models.price_history import PriceHistory, UserProduct
from app.models.product import Product, ProductGroup
from app.models.user import User
from app.services.auth import hash_password, create_access_token

# In-memory SQLite for tests
engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


@pytest.fixture(autouse=True)
def db():
    """Create fresh tables for each test."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db):
    """FastAPI test client with DB override."""
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def sample_user(db):
    """Create a sample user in the DB."""
    user = User(
        id=uuid.uuid4(),
        email="test@example.com",
        password_hash=hash_password("password123"),
        notify_email=True,
        notify_push=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def auth_headers(sample_user):
    """Return auth headers for the sample user."""
    token = create_access_token(sample_user.id)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sample_product(db):
    """Create a sample product in the DB."""
    product = Product(
        id=uuid.uuid4(),
        url="https://www.amazon.com.br/dp/B0TEST12345",
        marketplace="amazon",
        name="Produto Teste",
        current_price=Decimal("199.90"),
        currency="BRL",
        seller="Loja Teste",
        image_url="https://example.com/img.jpg",
        last_scraped_at=datetime.utcnow(),
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@pytest.fixture
def sample_price_history(db, sample_product):
    """Create sample price history entries."""
    entries = []
    prices = [Decimal("249.90"), Decimal("229.90"), Decimal("199.90")]
    for i, price in enumerate(prices):
        entry = PriceHistory(
            product_id=sample_product.id,
            price=price,
            seller="Loja Teste",
            available=True,
            scraped_at=datetime(2025, 1, 1 + i),
        )
        db.add(entry)
        entries.append(entry)
    db.commit()
    return entries


@pytest.fixture
def tracked_product(db, sample_user, sample_product):
    """Create a user-product tracking relationship."""
    up = UserProduct(
        user_id=sample_user.id,
        product_id=sample_product.id,
        target_price=Decimal("150.00"),
        notify_on_any_drop=True,
    )
    db.add(up)
    db.commit()
    return up
