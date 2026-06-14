def test_post_and_get_metrics(client):
    """
    Test that posting valid metrics succeeds and they can be retrieved via GET.
    """
    payload = {
        "server_name": "test-kali",
        "cpu_percent": 45.5,
        "memory_percent": 62.1,
        "disk_percent": 70.2,
        "bytes_sent": 5000000,
        "bytes_recv": 9000000,
        "services": [
            {"service_name": "ssh", "status": "active"},
            {"service_name": "docker", "status": "active"}
        ],
        "failed_logins": []
    }

    # Post metrics
    post_resp = client.post("/metrics", json=payload)
    assert post_resp.status_code == 201
    assert post_resp.json()["status"] == "success"

    # Get metrics
    get_resp = client.get("/metrics?limit=5")
    assert get_resp.status_code == 200
    metrics = get_resp.json()
    assert len(metrics) == 1
    
    m = metrics[0]
    assert m["server_name"] == "test-kali"
    assert m["cpu_percent"] == 45.5
    assert m["memory_percent"] == 62.1
    assert m["disk_percent"] == 70.2
    assert m["bytes_sent"] == 5000000
    assert m["bytes_recv"] == 9000000
    assert "timestamp" in m
