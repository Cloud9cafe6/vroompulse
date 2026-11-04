import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_read_root_dashboard():
    response = client.get("/")
    assert response.status_code == 200
    assert "VroomPulse" in response.text

def test_healthcheck_endpoint():
    response = client.get("/api/v1/healthcheck")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "service_name" in data[0]

def test_crash_reports_endpoint():
    response = client.get("/api/v1/crashes")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # Ensure it's sorted by impacted users descending
    if len(data) > 1:
        assert data[0]["impacted_users"] >= data[1]["impacted_users"]

def test_qa_checklist_endpoint():
    response = client.get("/api/v1/qa-checklist")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert any(item["task"] for item in data)

def test_toggle_qa_item():
    # Get current QA list
    response = client.get("/api/v1/qa-checklist")
    if response.status_code == 200 and response.json():
        item_id = response.json()[0]["id"]
        
        # Toggle the item
        toggle_response = client.post(f"/api/v1/qa-checklist/{item_id}/toggle")
        assert toggle_response.status_code == 200
        assert toggle_response.json()["status"] == "success"
        
        # Toggle it back
        client.post(f"/api/v1/qa-checklist/{item_id}/toggle")

def test_metrics_endpoint():
    response = client.get("/metrics")
    assert response.status_code == 200
    # Prometheus metrics are returned as plain text
    assert "http_requests_total" in response.text
