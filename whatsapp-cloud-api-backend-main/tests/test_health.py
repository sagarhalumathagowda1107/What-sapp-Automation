def test_health_check_endpoint(client):
    """Test GET /health returns expected structured status and sub-system health."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()

    assert data["status"] in ("healthy", "degraded")
    assert "timestamp_utc" in data
    assert "database" in data
    assert data["database"]["status"] == "healthy"
    assert "whatsapp_cloud_api" in data
    assert "scheduler" in data
    assert "storage" in data
