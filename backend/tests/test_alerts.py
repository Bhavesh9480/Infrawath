import datetime

def test_alert_generation_thresholds(client):
    """
    Test alert generation triggers when thresholds (CPU, RAM, Disk) are exceeded.
    """
    # 1. Test CPU exceeding 90% (Critical)
    payload = {
        "server_name": "test-kali",
        "cpu_percent": 95.0,  # exceeds 90%
        "memory_percent": 50.0,
        "disk_percent": 50.0,
        "bytes_sent": 1000,
        "bytes_recv": 2000,
        "services": [{"service_name": "ssh", "status": "active"}],
        "failed_logins": []
    }
    resp = client.post("/metrics", json=payload)
    assert resp.status_code == 201

    # Check that a CPU alert was created
    alerts_resp = client.get("/alerts")
    alerts = alerts_resp.json()
    assert len(alerts) == 1
    assert alerts[0]["alert_type"] == "CPU_LIMIT"
    assert alerts[0]["severity"] == "CRITICAL"
    assert "95.0%" in alerts[0]["message"]

    # Clear DB state between checks is not strictly required since we check individual rules,
    # but let's test Memory exceeding 85% (Warning) in a new post
    payload["cpu_percent"] = 50.0
    payload["memory_percent"] = 88.0  # exceeds 85%
    resp = client.post("/metrics", json=payload)
    assert resp.status_code == 201

    alerts = client.get("/alerts").json()
    # Should have CPU alert + Memory alert = 2 alerts
    assert len(alerts) == 2
    mem_alert = [a for a in alerts if a["alert_type"] == "MEMORY_LIMIT"][0]
    assert mem_alert["severity"] == "WARNING"
    assert "88.0%" in mem_alert["message"]

    # 3. Test Disk exceeding 90% (Critical)
    payload["memory_percent"] = 50.0
    payload["disk_percent"] = 92.0  # exceeds 90%
    resp = client.post("/metrics", json=payload)
    assert resp.status_code == 201

    alerts = client.get("/alerts").json()
    assert len(alerts) == 3
    disk_alert = [a for a in alerts if a["alert_type"] == "DISK_LIMIT"][0]
    assert disk_alert["severity"] == "CRITICAL"
    assert "92.0%" in disk_alert["message"]


def test_service_down_alert(client):
    """
    Test alert triggers when a monitored service goes down.
    """
    payload = {
        "server_name": "test-kali",
        "cpu_percent": 50.0,
        "memory_percent": 50.0,
        "disk_percent": 50.0,
        "bytes_sent": 1000,
        "bytes_recv": 2000,
        "services": [
            {"service_name": "ssh", "status": "down"},  # down
            {"service_name": "cron", "status": "active"}
        ],
        "failed_logins": []
    }
    client.post("/metrics", json=payload)

    alerts = client.get("/alerts").json()
    assert len(alerts) == 1
    assert alerts[0]["alert_type"] == "SERVICE_DOWN_SSH"
    assert alerts[0]["severity"] == "CRITICAL"
    assert "ssh" in alerts[0]["message"]


def test_security_alert_failed_logins(client):
    """
    Test that more than 5 failed logins within 10 minutes generates a security alert.
    """
    # Create 6 failed login occurrences
    failed_logins = []
    base_time = datetime.datetime.utcnow()
    for i in range(6):
        failed_logins.append({
            "timestamp": (base_time - datetime.timedelta(seconds=i*10)).isoformat(),
            "message": f"Failed password for root from 192.168.1.5 port 5432{i} ssh2"
        })

    payload = {
        "server_name": "test-kali",
        "cpu_percent": 50.0,
        "memory_percent": 50.0,
        "disk_percent": 50.0,
        "bytes_sent": 1000,
        "bytes_recv": 2000,
        "services": [{"service_name": "ssh", "status": "active"}],
        "failed_logins": failed_logins
    }

    client.post("/metrics", json=payload)

    alerts = client.get("/alerts").json()
    security_alerts = [a for a in alerts if a["alert_type"] == "SECURITY_ALERT"]
    assert len(security_alerts) == 1
    assert security_alerts[0]["severity"] == "SECURITY_ALERT"
    assert "failed logins" in security_alerts[0]["message"]


def test_alert_deduplication_cooldown(client):
    """
    Test that alert rules do not flood the database during the 5-minute cooldown.
    """
    payload = {
        "server_name": "test-kali",
        "cpu_percent": 99.0,  # exceeds 90%
        "memory_percent": 50.0,
        "disk_percent": 50.0,
        "bytes_sent": 1000,
        "bytes_recv": 2000,
        "services": [],
        "failed_logins": []
    }

    # Post multiple times in short succession
    client.post("/metrics", json=payload)
    client.post("/metrics", json=payload)
    client.post("/metrics", json=payload)

    alerts = client.get("/alerts").json()
    # Should only contain 1 alert because of the 5-minute cooldown deduplication!
    assert len(alerts) == 1
