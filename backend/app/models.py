import datetime
from sqlalchemy import Column, Integer, String, Float, BigInteger, DateTime
from backend.app.database import Base

class Metric(Base):
    __tablename__ = "metrics"

    id = Column(Integer, primary_key=True, index=True)
    server_name = Column(String, index=True, nullable=False)
    cpu_percent = Column(Float, nullable=False)
    memory_percent = Column(Float, nullable=False)
    disk_percent = Column(Float, nullable=False)
    bytes_sent = Column(BigInteger, nullable=False)
    bytes_recv = Column(BigInteger, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    server_name = Column(String, index=True, nullable=False)
    alert_type = Column(String, nullable=False)  # CPU_LIMIT, MEMORY_LIMIT, DISK_LIMIT, SERVICE_DOWN, SECURITY_ALERT
    severity = Column(String, nullable=False)    # WARNING, CRITICAL, SECURITY_ALERT
    message = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)

class Service(Base):
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True)
    service_name = Column(String, index=True, nullable=False)
    status = Column(String, nullable=False)  # active, down
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)

class FailedLogin(Base):
    __tablename__ = "failed_logins"

    id = Column(Integer, primary_key=True, index=True)
    server_name = Column(String, index=True, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    message = Column(String, nullable=False)
