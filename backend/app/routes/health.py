from fastapi import APIRouter, status
from backend.app.models.schemas import HealthResponse

router = APIRouter(prefix="/api", tags=["Health"])

@router.get("/health", response_model=HealthResponse, status_code=status.HTTP_200_OK)
def get_health():
    """Health check endpoint returning system operational status"""
    return HealthResponse(status="ok")
