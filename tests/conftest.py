import asyncio
#from unittest.mock import Mock
import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker#, AsyncSession

from main import app
from src.entity.models import Base, User
from src.database.db import get_db
from src.services.auth import auth_service

SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool
)

TestingSessionLocal = async_sessionmaker(autocommit=False, autoflush=False, expire_on_commit=False, bind=engine)
client = TestClient(app)
test_user = {"username": "test_user-1", "email": "test_email-1@gmail.com", "password": "12345678"}


@pytest.fixture(scope="module", autouse=True)
def init_models_wrap():
    async def init_models():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        async with TestingSessionLocal() as session:
            hash_password = auth_service.get_password_hash(test_user["password"])
            current_user = User(username=test_user["username"], email=test_user["email"], password=hash_password,
                                confirmed=True, role="admin")
            session.add(current_user)
            await session.commit()

    asyncio.run(init_models())


# @pytest.fixture(scope="module")
# def session():
#     # Create the database

#     Base.metadata.drop_all(bind=engine)
#     Base.metadata.create_all(bind=engine)

#     db = TestingSessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()


@pytest.fixture(scope="module")
def client():
    # Dependency override

    async def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        except ValueError as err:
            print(f"Error during DB session: {err}")
            await session.rollback()
        finally:
            await session.close()

    app.dependency_overrides[get_db] = override_get_db

    yield TestClient(app)


@pytest_asyncio.fixture()
async def get_token():
    token = await auth_service.create_access_token(data={"sub": test_user["email"]})
    return token