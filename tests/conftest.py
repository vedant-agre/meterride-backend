from collections.abc import Generator
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import create_access_token, get_password_hash
from app.database.base import Base
from app.database.database import get_db
from app.main import app
from app.models.driver import Driver, DriverStatus
from app.models.user import User, UserRole

# SQLite in-memory engine for fast, isolated tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db() -> Generator[Session, None, None]:
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db: Session) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def rider_data(db: Session) -> dict:
    user = User(
        name="Rider Alice",
        email="alice.rider@example.com",
        phone="+919000000001",
        password_hash=get_password_hash("Password123!"),
        role=UserRole.RIDER,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "role": user.role.value}
    )
    return {"user": user, "token": token, "headers": {"Authorization": f"Bearer {token}"}}


@pytest.fixture
def driver_data(db: Session) -> dict:
    user = User(
        name="Driver Bob",
        email="bob.driver@example.com",
        phone="+919000000002",
        password_hash=get_password_hash("Password123!"),
        role=UserRole.DRIVER,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    driver = Driver(
        user_id=user.id,
        license_number="DL-MH-12-20240001",
        status=DriverStatus.OFFLINE,
        rating_average=Decimal("5.00"),
        total_rides=0,
    )
    db.add(driver)
    db.commit()
    db.refresh(driver)

    token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "role": user.role.value}
    )
    return {
        "user": user,
        "driver": driver,
        "token": token,
        "headers": {"Authorization": f"Bearer {token}"},
    }


@pytest.fixture
def second_driver_data(db: Session) -> dict:
    user = User(
        name="Driver Charlie",
        email="charlie.driver@example.com",
        phone="+919000000003",
        password_hash=get_password_hash("Password123!"),
        role=UserRole.DRIVER,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    driver = Driver(
        user_id=user.id,
        license_number="DL-MH-12-20240002",
        status=DriverStatus.OFFLINE,
        rating_average=Decimal("5.00"),
        total_rides=0,
    )
    db.add(driver)
    db.commit()
    db.refresh(driver)

    token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "role": user.role.value}
    )
    return {
        "user": user,
        "driver": driver,
        "token": token,
        "headers": {"Authorization": f"Bearer {token}"},
    }


@pytest.fixture
def admin_data(db: Session) -> dict:
    user = User(
        name="Admin Dave",
        email="admin.dave@example.com",
        phone="+919000000004",
        password_hash=get_password_hash("Password123!"),
        role=UserRole.ADMIN,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "role": user.role.value}
    )
    return {"user": user, "token": token, "headers": {"Authorization": f"Bearer {token}"}}
