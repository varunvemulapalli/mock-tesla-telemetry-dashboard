import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "name" in response.json()


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_list_devices():
    response = client.get("/api/devices")
    assert response.status_code == 200
    assert "devices" in response.json()
    assert "total" in response.json()


def test_get_device():
    devices_response = client.get("/api/devices")
    devices = devices_response.json()["devices"]
    
    if devices:
        device_id = devices[0]["device_id"]
        response = client.get(f"/api/devices/{device_id}")
        assert response.status_code == 200
        assert response.json()["device_id"] == device_id

