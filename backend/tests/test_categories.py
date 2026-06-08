"""Categories endpoints tests."""

from fastapi import status


def test_create_category(client, auth_headers):
    """Test creating a category."""
    response = client.post(
        "/api/categories/",
        headers=auth_headers,
        json={
            "name": "Food",
            "color": "#FF5733",
            "icon": "🍔",
            "description": "Food and groceries",
        },
    )

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == "Food"
    assert data["color"] == "#FF5733"
    assert data["icon"] == "🍔"
    assert data["description"] == "Food and groceries"


def test_list_categories(client, auth_headers):
    """Test listing categories."""
    # Create some categories
    client.post(
        "/api/categories/",
        headers=auth_headers,
        json={"name": "Food", "color": "#FF5733"},
    )
    client.post(
        "/api/categories/",
        headers=auth_headers,
        json={"name": "Transport", "color": "#0080FF"},
    )

    response = client.get("/api/categories/", headers=auth_headers)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2


def test_list_all_categories(client, auth_headers):
    """Test listing all categories without pagination."""
    client.post(
        "/api/categories/",
        headers=auth_headers,
        json={"name": "Category A"},
    )

    response = client.get("/api/categories/all", headers=auth_headers)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_get_category(client, auth_headers):
    """Test getting a category."""
    # Create a category
    create_response = client.post(
        "/api/categories/",
        headers=auth_headers,
        json={"name": "Entertainment", "color": "#FF00FF"},
    )
    category_id = create_response.json()["id"]

    # Get the category
    response = client.get(f"/api/categories/{category_id}", headers=auth_headers)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == category_id
    assert data["name"] == "Entertainment"
    assert data["color"] == "#FF00FF"


def test_update_category(client, auth_headers):
    """Test updating a category."""
    # Create a category
    create_response = client.post(
        "/api/categories/",
        headers=auth_headers,
        json={"name": "Old Name", "color": "#000000"},
    )
    category_id = create_response.json()["id"]

    # Update it
    response = client.put(
        f"/api/categories/{category_id}",
        headers=auth_headers,
        json={"name": "New Name", "color": "#FFFFFF"},
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == "New Name"
    assert data["color"] == "#FFFFFF"


def test_delete_category(client, auth_headers):
    """Test deleting a category."""
    # Create a category
    create_response = client.post(
        "/api/categories/",
        headers=auth_headers,
        json={"name": "Temp Category"},
    )
    category_id = create_response.json()["id"]

    # Delete it
    response = client.delete(f"/api/categories/{category_id}", headers=auth_headers)

    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Verify deleted
    get_response = client.get(f"/api/categories/{category_id}", headers=auth_headers)
    assert get_response.status_code == status.HTTP_404_NOT_FOUND


def test_category_default_color(client, auth_headers):
    """Test that category gets default color."""
    response = client.post(
        "/api/categories/",
        headers=auth_headers,
        json={"name": "Default Color"},
    )

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["color"] == "#000000"
