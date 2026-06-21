import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import sqlite3
from pathlib import Path

import pytest

from app import create_app
from config import Config
from utils.messages import ApiMessages

class TestConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False


@pytest.fixture
def app(tmp_path):
    TestConfig.DATABASE_URL = str(tmp_path / "test.db")
    app = create_app(TestConfig)
    yield app


@pytest.fixture
def client(app):
    return app.test_client()

def test_register_creates_user_and_logs_in(client):
    response = client.post(
        "/register",
        json={
            "name": "Teste User",
            "email": "teste@example.com",
            "password": "senha123",
            "whatsapp_phone": "11999999999",
        },
    )

    assert response.status_code == 201
    assert response.get_json()["message"] == ApiMessages.AUTH_REGISTER_SUCCESS


def test_login_with_valid_credentials(client):
    client.post(
        "/register",
        json={"name": "Login User", "email": "login@example.com", "password": "senha123"},
    )
    client.get("/logout")
    response = client.post(
        "/login",
        json={"email": "login@example.com", "password": "senha123"},
    )

    assert response.status_code == 200
    assert response.get_json()["message"] == ApiMessages.AUTH_LOGIN_SUCCESS

def test_first_user_is_admin(app, client):
    # First user
    client.post(
        "/register",
        json={"name": "Admin User", "email": "admin@example.com", "password": "senha123"},
    )
    
    # Must logout because /register redirects if already logged in
    client.get("/logout")
    
    # Second user
    client.post(
        "/register",
        json={"name": "Normal User", "email": "normal@example.com", "password": "senha123"},
    )

    with app.app_context():
        from models.user import User
        admin = User.get_by_email("admin@example.com")
        normal = User.get_by_email("normal@example.com")
        assert admin.is_admin is True
        assert normal.is_admin is False
