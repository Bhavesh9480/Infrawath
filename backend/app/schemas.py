from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime

# ==========================================
# Metric Schemas
# ==========================================
class MetricBase(BaseModel):
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    bytes_sent: int
    bytes_recv: int

class MetricCreate(MetricBase):
    server_name: str
    timestamp: Optional[datetime] = None

class MetricResponse(MetricBase):
    id: int
    server_name: str
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)

# ==========================================
# Service Schemas
# ==========================================
class ServiceBase(BaseModel):
    service_name: str
    status: str  # active, down

class ServiceCreate(ServiceBase):
    timestamp: Optional[datetime] = None

class ServiceResponse(ServiceBase):
    id: int
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)

# ==========================================
# Failed Login Schemas
# ==========================================
class FailedLoginCreate(BaseModel):
    timestamp: datetime
    message: str

# ==========================================
# Alert Schemas
# ==========================================
class AlertBase(BaseModel):
    server_name: str
    alert_type: str
    severity: str
    message: str

class AlertResponse(AlertBase):
    id: int
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)

# ==========================================
# Ingestion Payload Schema
# ==========================================
class MetricsPayload(BaseModel):
    server_name: str
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    bytes_sent: int
    bytes_recv: int
    services: List[ServiceBase]
    failed_logins: List[FailedLoginCreate]
