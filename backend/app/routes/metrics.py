import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from backend.app.database import get_db
from backend.app import models, schemas, alert_engine

router = APIRouter(tags=["Metrics"])

@router.post("/metrics", status_code=status.HTTP_201_CREATED)
def post_metrics(payload: schemas.MetricsPayload, db: Session = Depends(get_db)):
    """
    Ingest a new set of system metrics, service statuses, and security events.
    Triggers the alert engine rules verification.
    """
    try:
        # 1. Store host system metrics
        db_metric = models.Metric(
            server_name=payload.server_name,
            cpu_percent=payload.cpu_percent,
            memory_percent=payload.memory_percent,
            disk_percent=payload.disk_percent,
            bytes_sent=payload.bytes_sent,
            bytes_recv=payload.bytes_recv,
            timestamp=datetime.datetime.utcnow()
        )
        db.add(db_metric)

        # 2. Store service status entries
        for service in payload.services:
            db_service = models.Service(
                service_name=service.service_name,
                status=service.status,
                timestamp=datetime.datetime.utcnow()
            )
            db.add(db_service)

        db.commit()

        # 3. Process the Alert Engine
        # The engine will also store the failed logins and evaluate all rules
        alert_engine.evaluate_rules(db, payload)

        return {"status": "success", "message": "Metrics received and processed successfully."}

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while processing metrics: {str(e)}"
        )

@router.get("/metrics", response_model=List[schemas.MetricResponse])
def get_metrics(
    limit: int = 20,
    server_name: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Retrieve historical system metrics, ordered from most recent to oldest.
    """
    query = db.query(models.Metric)
    if server_name:
        query = query.filter(models.Metric.server_name == server_name)
    
    return query.order_by(models.Metric.timestamp.desc()).limit(limit).all()
