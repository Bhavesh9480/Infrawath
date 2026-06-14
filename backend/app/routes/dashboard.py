from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func
import os
from backend.app.database import get_db
from backend.app import models

router = APIRouter(tags=["Dashboard"])

# Set up templates directory path.
# Assumes structure: backend/app/routes/dashboard.py, templates are in backend/app/templates/
current_dir = os.path.dirname(os.path.abspath(__file__))
templates_dir = os.path.abspath(os.path.join(current_dir, "..", "templates"))
templates = Jinja2Templates(directory=templates_dir)

@router.get("/dashboard", response_class=HTMLResponse)
def get_dashboard(request: Request, db: Session = Depends(get_db)):
    """
    Renders the HTML monitoring dashboard, injecting live system metrics,
    service health, alert logs, and chronological data for the timeline chart.
    """
    # 1. Fetch latest system metrics
    latest_metric = db.query(models.Metric).order_by(models.Metric.timestamp.desc()).first()

    # 2. Fetch current status of monitored services
    subq = (
        db.query(
            models.Service.service_name,
            func.max(models.Service.id).label("max_id")
        )
        .group_by(models.Service.service_name)
        .subquery()
    )
    services = (
        db.query(models.Service)
        .join(subq, models.Service.id == subq.c.max_id)
        .order_by(models.Service.service_name.asc())
        .all()
    )

    # 3. Fetch recent alert logs
    recent_alerts = db.query(models.Alert).order_by(models.Alert.timestamp.desc()).limit(15).all()

    # 4. Fetch last 20 metrics (ordered oldest first for Chart.js timeline rendering)
    metrics_history_desc = db.query(models.Metric).order_by(models.Metric.timestamp.desc()).limit(20).all()
    metrics_history = list(reversed(metrics_history_desc))

    # Extrapolate server name if available
    server_name = latest_metric.server_name if latest_metric else "No host connected"

    # Context to inject into Jinja2 template
    context = {
        "request": request,
        "latest_metric": latest_metric,
        "services": services,
        "recent_alerts": recent_alerts,
        "metrics_history": metrics_history,
        "server_name": server_name
    }

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context=context
    )

