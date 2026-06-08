"""Cards endpoints tests."""

from fastapi import status


def test_create_card(client, auth_headers):
    """Test creating a card."""
    response = client.post(
        "/api/cards/",
        headers=auth_headers,
        json={
            "name": "Visa Gold",
            "final_digits": "1234",
            "limit": 5000.00,
            "day_close": 10,
            "day_due": 20,
        },
    )

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == "Visa Gold"
    assert data["final_digits"] == "1234"
    assert data["limit"] == 5000.00
    assert data["day_close"] == 10
    assert data["day_due"] == 20
    assert data["is_active"] is True


def test_list_cards(client, auth_headers):
    """Test listing cards."""
    # Create some cards
    client.post(
        "/api/cards/",
        headers=auth_headers,
        json={"name": "Card 1", "limit": 3000.00},
    )
    client.post(
        "/api/cards/",
        headers=auth_headers,
        json={"name": "Card 2", "limit": 5000.00},
    )

    response = client.get("/api/cards/", headers=auth_headers)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2


def test_list_active_cards(client, auth_headers):
    """Test listing only active cards."""
    # Create an active card
    client.post(
        "/api/cards/",
        headers=auth_headers,
        json={"name": "Active Card"},
    )

    response = client.get("/api/cards/active", headers=auth_headers)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert all(card["is_active"] for card in data)


def test_get_card(client, auth_headers):
    """Test getting a card."""
    # Create a card
    create_response = client.post(
        "/api/cards/",
        headers=auth_headers,
        json={"name": "Mastercard", "limit": 4000.00},
    )
    card_id = create_response.json()["id"]

    # Get the card
    response = client.get(f"/api/cards/{card_id}", headers=auth_headers)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == card_id
    assert data["name"] == "Mastercard"


def test_update_card(client, auth_headers):
    """Test updating a card."""
    # Create a card
    create_response = client.post(
        "/api/cards/",
        headers=auth_headers,
        json={"name": "Old Name", "limit": 3000.00},
    )
    card_id = create_response.json()["id"]

    # Update it
    response = client.put(
        f"/api/cards/{card_id}",
        headers=auth_headers,
        json={"name": "New Name", "limit": 6000.00},
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == "New Name"
    assert data["limit"] == 6000.00


def test_delete_card(client, auth_headers):
    """Test deleting a card."""
    # Create a card
    create_response = client.post(
        "/api/cards/",
        headers=auth_headers,
        json={"name": "Card to delete"},
    )
    card_id = create_response.json()["id"]

    # Delete it
    response = client.delete(f"/api/cards/{card_id}", headers=auth_headers)

    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Verify deleted
    get_response = client.get(f"/api/cards/{card_id}", headers=auth_headers)
    assert get_response.status_code == status.HTTP_404_NOT_FOUND


def test_get_card_balance(client, auth_headers):
    """Test getting card balance."""
    # Create a card
    create_response = client.post(
        "/api/cards/",
        headers=auth_headers,
        json={"name": "Test Card", "limit": 5000.00},
    )
    card_id = create_response.json()["id"]

    # Get balance
    response = client.get(f"/api/cards/{card_id}/balance", headers=auth_headers)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["card_id"] == card_id
    assert "current_balance" in data
    assert "available_limit" in data
    assert data["available_limit"] == 5000.00  # No payments yet


def test_card_not_found(client, auth_headers):
    """Test getting nonexistent card."""
    response = client.get("/api/cards/nonexistent-id", headers=auth_headers)

    assert response.status_code == status.HTTP_404_NOT_FOUND
