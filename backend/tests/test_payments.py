"""Payments endpoints tests."""

import pytest
from fastapi import status
from datetime import datetime


@pytest.fixture
def test_account(client, auth_headers):
    """Create a test account."""
    response = client.post(
        "/api/accounts/",
        headers=auth_headers,
        json={"name": "Test Account", "initial_balance": 1000.00},
    )
    return response.json()


@pytest.fixture
def test_card(client, auth_headers):
    """Create a test card."""
    response = client.post(
        "/api/cards/",
        headers=auth_headers,
        json={"name": "Test Card", "limit": 5000.00},
    )
    return response.json()


@pytest.fixture
def test_category(client, auth_headers):
    """Create a test category."""
    response = client.post(
        "/api/categories/",
        headers=auth_headers,
        json={"name": "Food", "color": "#FF5733"},
    )
    return response.json()


def test_create_payment_to_account(client, auth_headers, test_account, test_category):
    """Test creating a payment to an account."""
    response = client.post(
        "/api/payments/",
        headers=auth_headers,
        json={
            "description": "Grocery shopping",
            "amount": 50.00,
            "account_id": test_account["id"],
            "category_id": test_category["id"],
            "data": datetime.now().isoformat(),
        },
    )

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["description"] == "Grocery shopping"
    assert data["amount"] == 50.00
    assert data["account_id"] == test_account["id"]
    assert data["card_id"] is None
    assert data["is_paid"] is False


def test_create_payment_to_card(client, auth_headers, test_card, test_category):
    """Test creating a payment to a card."""
    response = client.post(
        "/api/payments/",
        headers=auth_headers,
        json={
            "description": "Restaurant",
            "amount": 75.00,
            "card_id": test_card["id"],
            "category_id": test_category["id"],
            "data": datetime.now().isoformat(),
        },
    )

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["card_id"] == test_card["id"]
    assert data["account_id"] is None


def test_create_payment_invalid_destination(client, auth_headers, test_account, test_card, test_category):
    """Test creating a payment without specifying destination fails."""
    response = client.post(
        "/api/payments/",
        headers=auth_headers,
        json={
            "description": "Invalid payment",
            "amount": 50.00,
            "category_id": test_category["id"],
            "data": datetime.now().isoformat(),
        },
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_create_payment_both_destinations(client, auth_headers, test_account, test_card, test_category):
    """Test creating a payment with both account and card fails."""
    response = client.post(
        "/api/payments/",
        headers=auth_headers,
        json={
            "description": "Invalid payment",
            "amount": 50.00,
            "account_id": test_account["id"],
            "card_id": test_card["id"],
            "category_id": test_category["id"],
            "data": datetime.now().isoformat(),
        },
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_list_payments(client, auth_headers, test_account, test_category):
    """Test listing payments."""
    # Create a payment
    client.post(
        "/api/payments/",
        headers=auth_headers,
        json={
            "description": "Test payment",
            "amount": 100.00,
            "account_id": test_account["id"],
            "category_id": test_category["id"],
            "data": datetime.now().isoformat(),
        },
    )

    response = client.get("/api/payments/", headers=auth_headers)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_list_unpaid_payments(client, auth_headers, test_account, test_category):
    """Test listing only unpaid payments."""
    # Create an unpaid payment
    client.post(
        "/api/payments/",
        headers=auth_headers,
        json={
            "description": "Unpaid",
            "amount": 50.00,
            "account_id": test_account["id"],
            "category_id": test_category["id"],
            "data": datetime.now().isoformat(),
        },
    )

    response = client.get("/api/payments/?is_paid=false", headers=auth_headers)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert all(not p["is_paid"] for p in data)


def test_mark_payment_paid(client, auth_headers, test_account, test_category):
    """Test marking a payment as paid."""
    # Create a payment
    create_response = client.post(
        "/api/payments/",
        headers=auth_headers,
        json={
            "description": "Test",
            "amount": 50.00,
            "account_id": test_account["id"],
            "category_id": test_category["id"],
            "data": datetime.now().isoformat(),
        },
    )
    payment_id = create_response.json()["id"]

    # Mark as paid
    response = client.patch(
        f"/api/payments/{payment_id}/mark-paid",
        headers=auth_headers,
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["is_paid"] is True


def test_mark_payment_unpaid(client, auth_headers, test_account, test_category):
    """Test marking a payment as unpaid."""
    # Create a payment
    create_response = client.post(
        "/api/payments/",
        headers=auth_headers,
        json={
            "description": "Test",
            "amount": 50.00,
            "account_id": test_account["id"],
            "category_id": test_category["id"],
            "data": datetime.now().isoformat(),
        },
    )
    payment_id = create_response.json()["id"]

    # Mark as paid
    client.patch(f"/api/payments/{payment_id}/mark-paid", headers=auth_headers)

    # Mark as unpaid
    response = client.patch(
        f"/api/payments/{payment_id}/mark-unpaid",
        headers=auth_headers,
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["is_paid"] is False


def test_delete_payment(client, auth_headers, test_account, test_category):
    """Test deleting a payment."""
    # Create a payment
    create_response = client.post(
        "/api/payments/",
        headers=auth_headers,
        json={
            "description": "To delete",
            "amount": 50.00,
            "account_id": test_account["id"],
            "category_id": test_category["id"],
            "data": datetime.now().isoformat(),
        },
    )
    payment_id = create_response.json()["id"]

    # Delete
    response = client.delete(f"/api/payments/{payment_id}", headers=auth_headers)

    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Verify deleted
    get_response = client.get(f"/api/payments/{payment_id}", headers=auth_headers)
    assert get_response.status_code == status.HTTP_404_NOT_FOUND
