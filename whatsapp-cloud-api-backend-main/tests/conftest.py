import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Set test environment
os.environ["DATABASE_URL"] = "sqlite:///./test_reports.db"
os.environ["STORAGE_DIR"] = "storage/test_reports"
os.environ["META_APP_SECRET"] = "test_meta_app_secret_12345"
os.environ["WEBHOOK_VERIFY_TOKEN"] = "test_verify_token_secure"
os.environ["WHATSAPP_PHONE_NUMBER_ID"] = "123456789012345"
os.environ["WHATSAPP_ACCESS_TOKEN"] = "EAAGtest_access_token_secure"

from app.main import app
from app.core.database import Base, get_db
from app.core.config import settings

# Test SQLite Engine
TEST_DATABASE_URL = "sqlite:///./test_reports.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    os.makedirs(settings.STORAGE_DIR, exist_ok=True)
    yield
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("test_reports.db"):
        try:
            os.remove("test_reports.db")
        except Exception:
            pass


@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
