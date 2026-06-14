# InfraWatch - DevOps & Infrastructure Monitoring Platform

InfraWatch is a lightweight, production-grade DevOps and security monitoring system. It features a central **FastAPI backend with a beautiful dashboard** that runs in Docker, and a **python host agent** running directly on the Kali Linux host. This architecture allows you to monitor physical resource usage, services health, and authentication logs on your physical machine rather than within container boundaries.

---

## Key Features

1. **Host Resource Monitoring**: Gathers real-time CPU, Memory, Disk, and Network traffic data from the host.
2. **Service State Tracking**: Monitors systemd services (e.g., `ssh`, `docker`, `cron`) using `systemctl is-active`.
3. **Authentication Audit (Security)**: Reads `/var/log/auth.log` incrementally to identify invalid users, password failures, and auth breaches.
4. **Intelligent Alert Engine**: Evaluates thresholds and triggers warning/critical logs in database with built-in alert cooldowns (5-minute window) to prevent alert flooding.
5. **Modern Glassmorphic Dashboard**: A Dark-theme UI rendered using FastAPI and Jinja2 templates, incorporating:
   - Resource status progress indicators.
   - Dynamic service health state badges.
   - Historical line charts (Chart.js) depicting resource timelines.
   - Auto-refresh countdown.

---

## Directory Structure

```text
InfraWatch/
│
├── backend/
│   ├── app/
│   │   ├── main.py             # Entrypoint & DB initialization
│   │   ├── database.py         # SQLAlchemy engine & session config
│   │   ├── models.py           # Database models (metrics, alerts, services, failed_logins)
│   │   ├── schemas.py          # Pydantic validation schemas
│   │   ├── alert_engine.py     # Threshold logic & deduplication cooldowns
│   │   ├── routes/
│   │   │   ├── health.py       # API /health
│   │   │   ├── metrics.py      # API POST & GET /metrics
│   │   │   ├── alerts.py       # API GET /alerts
│   │   │   ├── services.py     # API GET /services
│   │   │   └── dashboard.py    # UI template rendering
│   │   └── templates/
│   │       └── dashboard.html  # Jinja2 dashboard UI
│   │
│   ├── requirements.txt        # Backend python requirements
│   ├── Dockerfile              # Docker image packaging instructions
│   └── tests/                  # PyTest suite directory
│
├── agent/
│   ├── monitor.py              # Main monitoring daemon process
│   ├── config.py               # Environment configuration loader
│   ├── service_monitor.py      # Service checking systemctl subprocesses
│   └── requirements.txt        # Agent dependencies
│
├── docker-compose.yml          # Container configuration
├── Jenkinsfile                 # CI/CD declarative pipeline
└── README.md                   # This instruction guide
```

---

## Ingest / Alert Rules

| Resource/Event | Condition | Alert Type | Severity |
| :--- | :--- | :--- | :--- |
| **CPU Usage** | $> 90\%$ | `CPU_LIMIT` | `CRITICAL` |
| **Memory Usage** | $> 85\%$ | `MEMORY_LIMIT` | `WARNING` |
| **Disk Usage** | $> 90\%$ | `DISK_LIMIT` | `CRITICAL` |
| **Services (`ssh`, `docker`, `cron`)** | `down` / `inactive` | `SERVICE_DOWN_<SVC>` | `CRITICAL` |
| **Auth Failures** | $> 5$ failures in 10 mins | `SECURITY_ALERT` | `SECURITY_ALERT` |

---

## Backend Deployment (Docker Compose)

The backend runs inside Docker. It exposes port `8000` and creates a persistent database volume `infrawatch_data`.

### Steps:
1. Navigate to the project root:
   ```bash
   cd InfraWatch
   ```
2. Build and run the backend service:
   ```bash
   docker compose up --build -d
   ```
3. Verify the server is running by visiting the API health check:
   `http://localhost:8000/health`
4. Access the gorgeous visual UI Dashboard:
   `http://localhost:8000/dashboard`

---

## Host Agent Installation (Kali Linux Host)

The agent must run on the physical host machine to inspect `/var/log/auth.log` and invoke `systemctl`.

### Requirements:
- Python 3.11+
- Pip package manager
- Sudo/root access (required for parsing auth logs and systemd state querying)

### Steps:
1. Set up a virtual environment and install agent dependencies:
   ```bash
   cd agent
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
2. Start the daemon with root privileges (to permit parsing `/var/log/auth.log`):
   ```bash
   sudo ../venv/bin/python monitor.py
   ```
   *Note: If you run without root/sudo, or on a non-Linux development OS (like Windows), the agent will fall back safely, allowing you to test metrics collection without crashing.*

---

## Environment Variables

### Backend Configuration
You can pass these environment variables inside `docker-compose.yml`:
* `DATABASE_URL`: SQLAlchemy connection URI. (Default: `sqlite:////app/data/infrawatch.db`)

### Agent Configuration
You can pass these environment variables to the agent process:
* `INFRAWATCH_BACKEND_URL`: URL to post metrics. (Default: `http://localhost:8000/metrics`)
* `INFRAWATCH_INTERVAL`: Sleep interval in seconds. (Default: `15`)
* `INFRAWATCH_SERVICES`: JSON list of services to monitor. (Default: `["ssh", "docker", "cron"]`)
* `INFRAWATCH_AUTH_LOG_PATH`: Path to auth log. (Default: `/var/log/auth.log`)
* `INFRAWATCH_SERVER_NAME`: Custom label for this node. (Default: Hostname)

---

## Running Automated Tests

We use PyTest for verification. To run all backend and alerting tests:

1. Setup local testing virtual environment:
   ```bash
   cd backend
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
2. Run the tests:
   ```bash
   PYTHONPATH=. pytest tests/
   ```
