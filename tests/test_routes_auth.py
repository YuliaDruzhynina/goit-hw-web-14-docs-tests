#import unittest
from unittest.mock import Mock

import pytest
from sqlalchemy import select

from src.entity.models import User
from tests.conftest import TestingSessionLocal

from src.conf import messages

user_data = {"username": "test_user", "email": "test_email@gmail.com", "password": "12345678"}


def test_signup(client, monkeypatch):
    mock_send_email = Mock()
    monkeypatch.setattr("src.services.send_email.send_email", mock_send_email)
    monkeypatch.setattr("starlette.requests.Request.client", Mock(host="127.0.0.1"))
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
    monkeypatch.setattr("starlette.requests.Request.client", Mock(host="127.0.0.1"))
    response = client.post("/auth/signup", json=user_data)
    assert response.status_code == 409, response.text
    data = response.json()
    assert data["detail"] == messages.ACCOUNT_EXIST