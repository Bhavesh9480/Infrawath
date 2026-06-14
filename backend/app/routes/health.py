import datetime
from fastapi import APIRouter

router = APIRouter(tags=["Health"])

@router.get("/health")
def get_health():
    """
    Health check endpoint returning system status and current server time.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.datetime.utcnow().isoformat()
    }
