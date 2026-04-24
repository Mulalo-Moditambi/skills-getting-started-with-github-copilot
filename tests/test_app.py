import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Add src directory to path so `from app import app, activities` works
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app, activities


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Restore the in-memory activities state before each test."""
    original_activities = {
        name: {
            **activity,
            "participants": activity["participants"].copy(),
        }
        for name, activity in activities.items()
    }
    yield
    activities.clear()
    activities.update(original_activities)


def test_get_activities_returns_available_activities(client):
    # Arrange
    expected_activity = "Chess Club"

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert expected_activity in data
    assert "participants" in data[expected_activity]


def test_signup_reflects_immediately_in_activity_list(client):
    # Arrange
    activity_name = "Chess Club"
    email = "testuser@mergington.edu"

    # Act
    signup_response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )
    activities_response = client.get("/activities")

    # Assert
    assert signup_response.status_code == 200
    assert email in activities_response.json()[activity_name]["participants"]


def test_duplicate_signup_returns_400(client):
    # Arrange
    activity_name = "Chess Club"
    email = "michael@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 400
    assert "already signed up" in response.json()["detail"]


def test_unregister_successfully_removes_participant(client):
    # Arrange
    activity_name = "Chess Club"
    email = "tempuser@mergington.edu"
    client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Act
    response = client.delete(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )
    activities_response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert email not in activities_response.json()[activity_name]["participants"]


def test_unregister_not_signed_up_returns_400(client):
    # Arrange
    activity_name = "Chess Club"
    email = "notregistered@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 400
    assert "not signed up" in response.json()["detail"]
