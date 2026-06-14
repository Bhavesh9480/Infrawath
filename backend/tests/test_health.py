def test_health_endpoint(client):
    """
    Test that the health endpoint returns 200 OK and reports healthy status.
    """
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
