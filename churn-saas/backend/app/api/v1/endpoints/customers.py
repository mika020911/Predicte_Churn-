from typing import Literal, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.models import User
from app.schemas.customers import CustomerListResponse
from app.services import customer_service

router = APIRouter(prefix="/customers", tags=["Clients"])


@router.get("", response_model=CustomerListResponse)
def list_customers(
    zone: Optional[Literal["low", "medium", "high"]] = Query(None, description="Filtre par zone de risque"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Clients de l'organisation avec leur score actif, du plus risqué au moins risqué."""
    return customer_service.list_customers(db, current_user.organization_id, zone, page, page_size)