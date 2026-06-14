from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from backend.app.database import get_db
from backend.app import models, schemas

router = APIRouter(tags=["Services"])

@router.get("/services", response_model=List[schemas.ServiceResponse])
def get_services(db: Session = Depends(get_db)):
    """
    Retrieve the current status of all monitored Linux services.
    Returns the most recent status record for each unique service name.
    """
    # Create subquery to find the maximum auto-incrementing ID for each service
    subq = (
        db.query(
            models.Service.service_name,
            func.max(models.Service.id).label("max_id")
        )
        .group_by(models.Service.service_name)
        .subquery()
    )

    # Join the main table to pull the full records associated with those IDs
    latest_services = (
        db.query(models.Service)
        .join(subq, models.Service.id == subq.c.max_id)
        .order_by(models.Service.service_name.asc())
        .all()
    )

    return latest_services
