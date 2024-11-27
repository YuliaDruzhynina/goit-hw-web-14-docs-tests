# pytest tests/test_routes_auth.py -v
from unittest.mock import Mock
import pytest
from fastapi import status
from sqlalchemy import select
from src.entity.models import User
from src.conf import messages
from tests.conftest import TestingSessionLocal


user_data = {
    "username": "test_user",
    "email": "test_email@gmail.com",
    "password": "12345678",
}


@pytest.fixture(autouse=True)
def mock_request_client(monkeypatch):
    # Mocking the request client in Starlette
    monkeypatch.setattr("starlette.requests.Request.client", Mock(host="127.0.0.1"))


def test_signup(client, monkeypatch):  # client передается как фикстура
    mock_send_email = Mock()
    monkeypatch.setattr("src.services.send_email.send_email", mock_send_email)
    response = client.post("/auth/signup", json=user_data)
    print("Response Text:", response.text)  # Debugging response body

    assert response.status_code == 201, response.text
    data = response.json()
    assert data["username"] == user_data["username"]
    assert data["email"] == user_data["email"]
    assert "password" not in data
    assert "avatar" in data


def test_repeat_signup(client, monkeypatch):
    mock_send_email = Mock()
    monkeypatch.setattr("src.services.send_email.send_email", mock_send_email)
    response = client.post("/auth/signup", json=user_data)
    assert response.status_code == 409, response.text
    data = response.json()
    assert data["detail"] == messages.ACCOUNT_EXIST  # == "Account already exists"


def test_not_confirmed_login(client):
    response = client.post(
        "/auth/login",
        data={
            "username": user_data.get("email"),
            "password": user_data.get("password"),
        },
    )
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == "Email not confirmed"


@pytest.mark.asyncio
async def test_login(client):
    async with TestingSessionLocal() as session:
        current_user = await session.execute(
            select(User).where(User.email == user_data.get("email"))
        )
        current_user = current_user.scalar_one_or_none()
        if current_user:
            current_user.confirmed = True
            await session.commit()

    response = client.post(
        "auth/login",
        data={
            "username": user_data.get("email"),
            "password": user_data.get("password"),
        },
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert "token_type" in data


def test_invalid_password_login(client):
    response = client.post(
        "/auth/login", data={"username": user_data.get("email"), "password": "password"}
    )
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == "Invalid password"


def test_invalid_email_login(client):
    response = client.post(
        "/auth/login", data={"username": "email", "password": user_data.get("password")}
    )
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == "Invalid email"


def test_validation_error_login(client):
    response = client.post("/auth/login", data={"password": user_data.get("password")})
    assert response.status_code == 422, response.text
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_protected_route_with_valid_token(
    client, get_token
):  # The client is passed as a fixture from the fixture conftest.py
    token = get_token  # Get the token from the fixture conftest.py
    response = client.get("/auth/secret", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    response_json = response.json()
    assert "owner" in response_json
    assert response_json["owner"] == "test_email-1@gmail.com"


async def test_secret_route_without_token(client):
    response = client.get("/auth/secret")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "detail" in response.json()
