import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Retrieve database URL from environment or fallback to local SQLite
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./infrawatch.db")

# Automatically create parent directories for SQLite databases if they don't exist
if DATABASE_URL.startswith("sqlite://"):
    # Extract the database path
    # sqlite:////app/data/infrawatch.db -> /app/data/infrawatch.db
    # sqlite:///./infrawatch.db -> ./infrawatch.db
    db_path = DATABASE_URL.replace("sqlite:///", "").replace("sqlite://", "")
    if db_path and db_path != ":memory:":
        db_dir = os.path.dirname(db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)

# For SQLite, we need connect_args={"check_same_thread": False}
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """
    FastAPI dependency that provides a transactional database session.
    Ensures the session is closed after the request completes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
