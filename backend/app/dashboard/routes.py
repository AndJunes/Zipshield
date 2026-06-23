from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.dashboard import service
from app.dashboard.schemas import DashboardSummary

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("", response_model=DashboardSummary)
def get_summary(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return service.dashboard_summary(db)
