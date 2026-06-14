import datetime
import logging
from sqlalchemy.orm import Session
from backend.app import models, schemas

logger = logging.getLogger("infrawatch.alert_engine")

def create_alert_if_needed(
    db: Session,
    server_name: str,
    alert_type: str,
    severity: str,
    message: str
) -> bool:
    """
    Creates an alert in the database if there is no active alert of the same type
    for the same server within a 5-minute cooldown window.
    """
    cooldown_period = datetime.timedelta(minutes=5)
    cutoff_time = datetime.datetime.utcnow() - cooldown_period

    # Check for duplicate alert in the cooldown window
    existing_alert = (
        db.query(models.Alert)
        .filter(
            models.Alert.server_name == server_name,
            models.Alert.alert_type == alert_type,
            models.Alert.timestamp >= cutoff_time
        )
        .first()
    )

    if not existing_alert:
        alert = models.Alert(
            server_name=server_name,
            alert_type=alert_type,
            severity=severity,
            message=message,
            timestamp=datetime.datetime.utcnow()
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)
        logger.warning(f"ALERT GENERATED: [{severity}] {server_name} - {message}")
        return True
    
    logger.info(f"Alert [{alert_type}] for {server_name} throttled due to cooldown.")
    return False

def evaluate_rules(db: Session, payload: schemas.MetricsPayload):
    """
    Evaluates system metrics, service statuses, and security events to generate alerts.
    """
    server_name = payload.server_name

    # Rule 1: CPU > 90% -> CRITICAL
    if payload.cpu_percent > 90.0:
        create_alert_if_needed(
            db=db,
            server_name=server_name,
            alert_type="CPU_LIMIT",
            severity="CRITICAL",
            message=f"CPU usage is high: {payload.cpu_percent}% (Limit: 90%)"
        )

    # Rule 2: Memory > 85% -> WARNING
    if payload.memory_percent > 85.0:
        create_alert_if_needed(
            db=db,
            server_name=server_name,
            alert_type="MEMORY_LIMIT",
            severity="WARNING",
            message=f"Memory usage is high: {payload.memory_percent}% (Limit: 85%)"
        )

    # Rule 3: Disk > 90% -> CRITICAL
    if payload.disk_percent > 90.0:
        create_alert_if_needed(
            db=db,
            server_name=server_name,
            alert_type="DISK_LIMIT",
            severity="CRITICAL",
            message=f"Disk space is low: {payload.disk_percent}% (Limit: 90%)"
        )

    # Rule 4: Service Down -> CRITICAL
    for service in payload.services:
        if service.status != "active":
            create_alert_if_needed(
                db=db,
                server_name=server_name,
                alert_type=f"SERVICE_DOWN_{service.service_name.upper()}",
                severity="CRITICAL",
                message=f"Service '{service.service_name}' is down (Status: {service.status})"
            )

    # Rule 5: More than 5 failed logins in 10 minutes -> SECURITY_ALERT
    # First, save any new failed login attempts to database
    for failed in payload.failed_logins:
        # Convert Pydantic datetime if needed, else store
        db_failed = models.FailedLogin(
            server_name=server_name,
            timestamp=failed.timestamp,
            message=failed.message
        )
        db.add(db_failed)
    db.commit()

    # Query last 10 minutes failed login count
    ten_minutes_ago = datetime.datetime.utcnow() - datetime.timedelta(minutes=10)
    failed_count = (
        db.query(models.FailedLogin)
        .filter(
            models.FailedLogin.server_name == server_name,
            models.FailedLogin.timestamp >= ten_minutes_ago
        )
        .count()
    )

    if failed_count > 5:
        create_alert_if_needed(
            db=db,
            server_name=server_name,
            alert_type="SECURITY_ALERT",
            severity="SECURITY_ALERT",
            message=f"Multiple authentication failures: {failed_count} failed logins detected in the last 10 minutes."
        )
