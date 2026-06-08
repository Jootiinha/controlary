"""Accounts endpoints tests."""

import pytest
from fastapi import status


def test_create_account(client, auth_headers):
    """Test creating an account."""
    response = client.post(
        "/api/accounts/",
        headers=auth_headers,
        json={
            "name": "My Checking Account",
            "description": "Main checking account",
            "initial_balance": 1000.00,
        },
    )

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == "My Checking Account"
    assert data["description"] == "Main checking account"
    assert data["initial_balance"] == 1000.00
    assert data["is_active"] is True
    assert "id" in data


def test_list_accounts(client, auth_headers):
    """Test listing accounts."""
    # Create an account first
    client.post(
        "/api/accounts/",
        headers=auth_headers,
        json={"name": "Account 1", "initial_balance": 500.00},
    )

    response = client.get("/api/accounts/", headers=auth_headers)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["name"] == "Account 1"
    assert "current_balance" in data[0]


def test_get_account(client, auth_headers):
    """Test getting a single account."""
    # Create account
    create_response = client.post(
        "/api/accounts/",
        headers=auth_headers,
        json={"name": "Test Account", "initial_balance": 750.00},
    )
    account_id = create_response.json()["id"]

    # Get account
    response = client.get(f"/api/accounts/{account_id}", headers=auth_headers)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == account_id
    assert data["name"] == "Test Account"
    assert data["current_balance"] == 750.00


def test_update_account(client, auth_headers):
    """Test updating an account."""
    # Create account
    create_response = client.post(
        "/api/accounts/",
        headers=auth_headers,
        json={"name": "Old Name"},
    )
    account_id = create_response.json()["id"]

    # Update account
    response = client.put(
        f"/api/accounts/{account_id}",
        headers=auth_headers,
        json={"name": "New Name", "description": "Updated description"},
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == "New Name"
    assert data["description"] == "Updated description"


def test_delete_account(client, auth_headers):
    """Test deleting an account."""
    # Create account
    create_response = client.post(
        "/api/accounts/",
        headers=auth_headers,
        json={"name": "Account to Delete"},
    )
    account_id = create_response.json()["id"]

    # Delete account
    response = client.delete(f"/api/accounts/{account_id}", headers=auth_headers)

    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Verify it's deleted
    get_response = client.get(f"/api/accounts/{account_id}", headers=auth_headers)
    assert get_response.status_code == status.HTTP_404_NOT_FOUND


def test_get_account_balance(client, auth_headers):
    """Test getting account balance."""
    # Create account
    create_response = client.post(
        "/api/accounts/",
        headers=auth_headers,
        json={"name": "Balance Test", "initial_balance": 1000.00},
    )
    account_id = create_response.json()["id"]

    # Get balance
    response = client.get(f"/api/accounts/{account_id}/balance", headers=auth_headers)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["account_id"] == account_id
    assert data["balance"] == 1000.00


def test_get_total_balance(client, auth_headers):
    """Test getting total balance across all accounts."""
    # Create multiple accounts
    client.post(
        "/api/accounts/",
        headers=auth_headers,
        json={"name": "Account A", "initial_balance": 500.00},
    )
    client.post(
        "/api/accounts/",
        headers=auth_headers,
        json={"name": "Account B", "initial_balance": 750.00},
    )

    response = client.get("/api/accounts/accounts/total-balance", headers=auth_headers)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total_balance"] == 1250.00


def test_account_not_found(client, auth_headers):
    """Test getting nonexistent account."""
    response = client.get("/api/accounts/nonexistent-id", headers=auth_headers)

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_create_account_without_auth(client):
    """Test creating account without authentication."""
    response = client.post(
        "/api/accounts/",
        json={"name": "Test Account"},
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
