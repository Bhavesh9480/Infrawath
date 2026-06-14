# Containerization & CI/CD Pipeline Setup Guide

This document describes how to containerize the **InfraWatch** platform and manage its continuous integration and deployment (CI/CD) pipeline using a Jenkins container.

---

## 1. Containerization Architecture

InfraWatch runs as a split-architecture application:
1. **InfraWatch Backend**: Runs inside a Docker container using a lightweight `python:3.11-slim` base image. It exposes port `8000` for API endpoints and UI visualization.
2. **SQLite Database**: Persisted on a named Docker volume (`infrawatch_data`) to prevent data loss when the backend container is updated or rebuilt.
3. **Monitoring Agent**: Runs directly on the host Kali Linux operating system. This is crucial because it needs local access to system performance APIs (`psutil`), systemd state managers (`systemctl`), and security log files (`/var/log/auth.log`).

```text
Host Machine (Kali Linux)
│
├── Monitoring Agent (Direct on host OS)
│
├── Docker Engine
│   │
│   ├── Jenkins Container (Port 8080)
│   │   └── Triggers builds and executes pipeline stages
│   │
│   └── InfraWatch Container (Port 8000)
│       ├── FastAPI App
│       └── SQLite DB (Persistent via Named Volume)
```

---

## 2. Docker-outside-of-Docker (DooD)

To manage the deployment of our backend container through a Jenkins container, we use the **Docker-outside-of-Docker (DooD)** pattern. 

Instead of running a Docker daemon *inside* the Jenkins container (which requires privileged flags and degrades performance), we mount the host's Docker socket `/var/run/docker.sock` into the Jenkins container. 

This enables the Jenkins container to send build and run instructions directly to the host's Docker daemon. As a result, containers created by the Jenkins pipeline will run on the host system alongside the Jenkins container.

### Jenkins Customization (`jenkins/Dockerfile`)
Since the standard Jenkins LTS image does not contain Python 3 (required for running backend test suites) or the Docker CLI tools (required for building images), we use a custom Dockerfile to pre-install these dependencies:
* **Docker CLI & Docker Compose Plugin**: Interacts with the mounted socket.
* **Python 3 & Virtualenv**: Prepares the workspace and runs `pytest`.

---

## 3. Step-by-Step Setup Guide

Follow these steps to deploy Jenkins and execute the pipeline:

### Step 1: Start the Jenkins Container
Spin up the Jenkins server using the dedicated Compose file from the root directory:
```bash
docker compose -f docker-compose-jenkins.yml up -d --build
```
This builds our customized Jenkins image and launches the server.

### Step 2: Retrieve the Unlock Password
Wait 15-30 seconds for Jenkins to initialize. Fetch the auto-generated administrator password from the container logs:
```bash
docker logs jenkins-server
```
Look for a long alphanumeric string under the line:
`Please use the following password to proceed with installation:`

### Step 3: Complete Setup Wizard
1. Open your browser and navigate to `http://localhost:8080`.
2. Paste the administrator password to unlock Jenkins.
3. Choose **"Install suggested plugins"** and wait for completion.
4. Create your admin user credentials and finish the setup.

### Step 4: Create the CI/CD Pipeline Job
1. From the Jenkins home page, click **New Item**.
2. Enter the name `InfraWatch-Pipeline`, select **Pipeline**, and click **OK**.
3. Under the **Pipeline** configuration section:
   - Select **Definition**: *Pipeline script from SCM*.
   - Select **SCM**: *Git*.
   - Enter your repository URL (e.g. your local directory path or remote Git URL).
   - Verify the **Branch Specifier** is correct (e.g., `*/main` or `*/master`).
   - Ensure **Script Path** is set to `Jenkinsfile`.
4. Click **Save**.

### Step 5: Run the Pipeline
1. Click **Build Now** in the left sidebar.
2. Jenkins will checkout the code, install dependencies in a virtual environment, run PyTest, compile the new Docker image, stop the outdated backend container, and deploy the new one.
3. Once the build is green, check the live dashboard at:
   `http://localhost:8000/dashboard`

---

## 4. Pipeline Execution Lifecycle

The pipeline is defined in [Jenkinsfile](file:///d:/Infrawatch/Jenkinsfile) and follows this sequence:

1. **Git Checkout**: Pulls the latest commits.
2. **Install Dependencies**: Creates a virtual environment and installs package managers to sandbox testing libraries.
3. **Run PyTest**: Executes the unit and integration tests. If any tests fail, the pipeline halts immediately, preventing faulty code from going to production.
4. **Build Docker Image**: Builds the backend image: `docker compose build`.
5. **Stop Old Container**: Safely brings down the active deployment: `docker compose down`.
6. **Deploy New Container**: Spins up the freshly built container in detached mode: `docker compose up -d`.
