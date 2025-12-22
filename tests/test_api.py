"""
Unit tests for the FastAPI endpoints.
"""
import pytest
from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base, get_db
from app.main import app

# Override the database dependency with an in‑memory SQLite database
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="module")
def client():
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c
    Base.metadata.drop_all(bind=engine)

def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "docs" in data
    assert "endpoints" in data

def test_post_data(client):
    payload = {
        "experiment_id": "test_api_exp",
        "date": "2025-12-22",
        "variants": [
            {"variant_id": "control", "impressions": 1000, "clicks": 50},
            {"variant_id": "variant", "impressions": 1000, "clicks": 70}
        ]
    }
    response = client.post("/data", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["detail"] == "Data stored successfully"

def test_post_data_validation_error(client):
    # Clicks exceed impressions
    payload = {
        "experiment_id": "test",
        "date": "2025-12-22",
        "variants": [
            {"variant_id": "control", "impressions": 100, "clicks": 200}
        ]
    }
    response = client.post("/data", json=payload)
    assert response.status_code == 422  # validation error

def test_get_allocation_no_data(client):
    response = client.get("/allocation", params={"experiment_id": "nonexistent"})
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()

def test_get_allocation_with_data(client):
    # First insert data
    payload = {
        "experiment_id": "alloc_test",
        "date": "2025-12-21",
        "variants": [
            {"variant_id": "A", "impressions": 1000, "clicks": 100},
            {"variant_id": "B", "impressions": 1000, "clicks": 200}
        ]
    }
    client.post("/data", json=payload)
    # Request allocation
    response = client.get("/allocation", params={"experiment_id": "alloc_test"})
    assert response.status_code == 200
    data = response.json()
    assert data["experiment_id"] == "alloc_test"
    assert data["date"] == (date.today() + date.resolution).isoformat()  # tomorrow
    assert len(data["allocations"]) == 2
    # B should have higher percentage
    alloc_map = {a["variant_id"]: a["percentage"] for a in data["allocations"]}
    assert alloc_map["B"] > alloc_map["A"]
    assert abs(alloc_map["A"] + alloc_map["B"] - 100.0) < 0.01

def test_get_allocation_with_custom_date(client):
    payload = {
        "experiment_id": "custom_date_exp",
        "date": "2025-12-21",
        "variants": [
            {"variant_id": "X", "impressions": 500, "clicks": 25},
            {"variant_id": "Y", "impressions": 500, "clicks": 75}
        ]
    }
    client.post("/data", json=payload)
    response = client.get("/allocation", params={
        "experiment_id": "custom_date_exp",
        "target_date": "2025-12-25"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["date"] == "2025-12-25"

def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

if __name__ == "__main__":
    pytest.main([__file__])