import os
import socket
import json

# Backend API endpoint to POST metrics to
BACKEND_URL = os.getenv("INFRAWATCH_BACKEND_URL", "http://localhost:8000/metrics")

# Ingestion interval in seconds (default: 15)
INTERVAL = int(os.getenv("INFRAWATCH_INTERVAL", "15"))

# Monitored systemd services (configured as JSON list or comma-separated string)
services_raw = os.getenv("INFRAWATCH_SERVICES", '["ssh", "docker", "cron"]')
try:
    SERVICES = json.loads(services_raw)
except json.JSONDecodeError:
    SERVICES = [s.strip() for s in services_raw.split(",") if s.strip()]

# File path to the Linux authentication log
AUTH_LOG_PATH = os.getenv("INFRAWATCH_AUTH_LOG_PATH", "/var/log/auth.log")

# Host identity to report to the backend
SERVER_NAME = os.getenv("INFRAWATCH_SERVER_NAME", socket.gethostname())
