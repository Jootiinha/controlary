"""Authentication tests."""

import pytest
from fastapi import status


def test_register_user(client):
    """Test user registration."""
    response = client.post(
        "/api/auth/register",
        json={
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "password123",
            "full_name": "New User",
        },
    )

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["username"] == "newuser"
    assert data["email"] == "newuser@example.com"
    assert data["full_name"] == "New User"
    assert data["is_active"] is True
    assert "id" in data


def test_register_duplicate_username(client, registered_user):
    """Test registration with duplicate username."""
    response = client.post(
        "/api/auth/register",
        json={
            "username": "testuser",
            "email": "another@example.com",
            "password": "password123",
        },
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_register_duplicate_email(client, registered_user):
    """Test registration with duplicate email."""
    response = client.post(
        "/api/auth/register",
        json={
            "username": "anotheruser",
            "email": "test@example.com",
            "password": "password123",
        },
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_login_success(client, registered_user):
    """Test successful login."""
    response = client.post(
        "/api/auth/login",
        json={
            "username": "testuser",
            "password": "testpass123",
        },
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["username"] == "testuser"
    assert data["user"]["email"] == "test@example.com"


def test_login_wrong_password(client, registered_user):
    """Test login with wrong password."""
    response = client.post(
        "/api/auth/login",
        json={
            "username": "testuser",
            "password": "wrongpassword",
        },
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_login_nonexistent_user(client):
    """Test login with nonexistent user."""
    response = client.post(
        "/api/auth/login",
        json={
            "username": "nonexistent",
            "password": "password123",
        },
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_current_user(client, auth_headers):
    """Test getting current user info."""
    response = client.get(
        "/api/auth/me",
        headers=auth_headers,
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"


def test_get_current_user_without_token(client):
    """Test getting current user without token."""
    response = client.get("/api/auth/me")

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_get_current_user_invalid_token(client):
    """Test getting current user with invalid token."""
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": "Bearer invalid_token"},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_logout(client, auth_headers):
    """Test logout."""
    response = client.post(
        "/api/auth/logout",
        headers=auth_headers,
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["message"] == "Logged out successfully"


def test_change_password(client, auth_headers, test_db):
    """Test password change."""
    response = client.post(
        "/api/auth/change-password",
        params={
            "old_password": "testpass123",
            "new_password": "newpassword123",
        },
        headers=auth_headers,
    )

    assert response.status_code == status.HTTP_200_OK

    # Verify new password works
    response = client.post(
        "/api/auth/login",
        json={
            "username": "testuser",
            "password": "newpassword123",
        },
    )

    assert response.status_code == status.HTTP_200_OK


def test_change_password_wrong_old_password(client, auth_headers):
    """Test password change with wrong old password."""
    response = client.post(
        "/api/auth/change-password",
        params={
            "old_password": "wrongpassword",
            "new_password": "newpassword123",
        },
        headers=auth_headers,
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
