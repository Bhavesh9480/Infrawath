from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from backend.app.database import get_db
from backend.app import models, schemas

router = APIRouter(tags=["Alerts"])

@router.get("/alerts", response_model=List[schemas.AlertResponse])
def get_alerts(
    limit: int = 50,
    severity: Optional[str] = None,
    server_name: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Retrieve system and security alerts, sorted by latest first.
    Filters by severity or server_name if provided.
    """
    query = db.query(models.Alert)
    
    if severity:
        query = query.filter(models.Alert.severity == severity)
    if server_name:
        query = query.filter(models.Alert.server_name == server_name)
        
    return query.order_by(models.Alert.timestamp.desc()).limit(limit).all()
