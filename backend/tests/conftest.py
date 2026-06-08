"""Pytest configuration and fixtures."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app import create_app
from app.database import Base, init_db, SessionLocal
import config


@pytest.fixture(scope="session")
def test_engine():
    """Create test database engine."""
    database_url = "sqlite:///:memory:"
    engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False},
        poolclass=None,
    )

    # Enable foreign keys and WAL
    from sqlalchemy import event

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_db(test_engine):
    """Create test database session."""
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine,
    )

    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def app_with_db(test_db):
    """Create FastAPI test app with test database."""
    app = create_app(testing=True)

    # Override database dependency
    from app.database import get_db

    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    yield app
    app.dependency_overrides.clear()


@pytest.fixture
def client(app_with_db):
    """Create test client."""
    return TestClient(app_with_db)


@pytest.fixture
def registered_user(test_db):
    """Create a registered test user."""
    from app.services.auth_service import AuthService

    user = AuthService.register_user(
        test_db,
        username="testuser",
        email="test@example.com",
        password="testpass123",
        full_name="Test User",
    )
    return user


@pytest.fixture
def auth_headers(client, registered_user):
    """Get authorization headers for authenticated requests."""
    response = client.post(
        "/api/auth/login",
        json={
            "username": "testuser",
            "password": "testpass123",
        },
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
