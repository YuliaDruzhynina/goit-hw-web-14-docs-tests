# import unittest
from unittest.mock import Mock
import pytest
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
    # Мокаем клиент запросов в starlette
    monkeypatch.setattr("starlette.requests.Request.client", Mock(host="127.0.0.1"))


def test_signup(client, monkeypatch):
    mock_send_email = Mock()
    monkeypatch.setattr("src.services.send_email.send_email", mock_send_email)
    response = client.post("/auth/signup", json=user_data)
    print("Response Text:", response.text)  # Debugging response body

    assert response.status_code == 201, response.text

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
