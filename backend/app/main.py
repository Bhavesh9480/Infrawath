import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from backend.app.database import engine, Base
from backend.app.routes import health, metrics, alerts, services, dashboard

# Setup logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("infrawatch")

# Automatically construct SQLite database tables on application initialization
try:
    logger.info("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized successfully.")
except Exception as e:
    logger.critical(f"Failed to initialize database tables: {str(e)}")

app = FastAPI(
    title="InfraWatch API",
    description="DevOps & Infrastructure Monitoring platform",
    version="1.0.0"
)

# Enable CORS for local development environments
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register route modules
app.include_router(health.router)
app.include_router(metrics.router)
app.include_router(alerts.router)
app.include_router(services.router)
app.include_router(dashboard.router)

@app.get("/", include_in_schema=False)
def root_redirect():
    """
    Redirect the root URL path directly to the Jinja2 dashboard.
    """
    return RedirectResponse(url="/dashboard")
