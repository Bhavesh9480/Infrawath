def test_get_services_latest_status(client):
    """
    Test that GET /services returns only the latest status for each service name.
    """
    # 1. Post initial services statuses
    payload1 = {
        "server_name": "test-kali",
        "cpu_percent": 50.0,
        "memory_percent": 50.0,
        "disk_percent": 50.0,
        "bytes_sent": 1000,
        "bytes_recv": 2000,
        "services": [
            {"service_name": "ssh", "status": "active"},
            {"service_name": "docker", "status": "down"}
        ],
        "failed_logins": []
    }
    client.post("/metrics", json=payload1)

    # Verify first state
    resp1 = client.get("/services")
    assert resp1.status_code == 200
    services1 = resp1.json()
    assert len(services1) == 2
    
    ssh_svc1 = [s for s in services1 if s["service_name"] == "ssh"][0]
    docker_svc1 = [s for s in services1 if s["service_name"] == "docker"][0]
    assert ssh_svc1["status"] == "active"
    assert docker_svc1["status"] == "down"

    # 2. Post updated services statuses (docker becomes active, ssh becomes down)
    payload2 = {
        "server_name": "test-kali",
        "cpu_percent": 50.0,
        "memory_percent": 50.0,
        "disk_percent": 50.0,
        "bytes_sent": 1000,
        "bytes_recv": 2000,
        "services": [
            {"service_name": "ssh", "status": "down"},
            {"service_name": "docker", "status": "active"}
        ],
        "failed_logins": []
    }
    client.post("/metrics", json=payload2)

    # Verify updated state: should still only have 2 unique records, representing the latest reports
    resp2 = client.get("/services")
    assert resp2.status_code == 200
    services2 = resp2.json()
    assert len(services2) == 2
    
    ssh_svc2 = [s for s in services2 if s["service_name"] == "ssh"][0]
    docker_svc2 = [s for s in services2 if s["service_name"] == "docker"][0]
    assert ssh_svc2["status"] == "down"
    assert docker_svc2["status"] == "active"
