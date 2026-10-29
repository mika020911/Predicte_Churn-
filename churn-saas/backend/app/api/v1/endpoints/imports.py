from typing import List
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.models import ImportBatch, User
from app.schemas.imports import ImportBatchRead, ImportBatchSummary
from app.services.import_service import process_csv_import

router = APIRouter(prefix="/imports", tags=["Imports"])


@router.post("/upload", response_model=ImportBatchRead, status_code=status.HTTP_201_CREATED)
async def upload_csv_import(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    #import CVS obs client  , valide les donner , creer client et enregister les snapshot
    if not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="euls les fichiers .csv sont autorisés.",
        )
    file_bytes =await file.read()
    if len(file_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le fichier téléversé est vide.",
        )
    batch = process_csv_import(
        file_bytes=file_bytes,
        filename=file.filename,
        current_user=current_user,
        db=db,
    )
    return batch

@router.get("/", response_model=List[ImportBatchSummary])
def list_import_batches(
    db: Session = Depends(get_db),current_user: User = Depends(get_current_active_user),
):
#all import 
    batches =(
        db.querry(ImportBatch)
        .filter(ImportBatch.organization_id == current_user.organization_id)
        .order_by(ImportBatch.created_at.desc())
        .all()
    )
    return [
        ImportBatchSummary(
            import_batch_id=b.id,
            filename=b.filename,
            status=b.status,
            total_rows=b.total_rows,
            imported_rows=b.imported_rows,
            error_rows=b.error_rows,
            created_at=b.created_at,
        )
        for b in batches
    ]
@router.get("/{import_batch_id}", response_model = ImportBatchRead)
def get_import_batch_detail(
    import_batch_id: str,
    db: Session = Depends (get_db),
    current_user: User = Depends(get_current_active_user),
):
    #Détail et rapport d'anomalies d'un import spécifique (isolation multi-tenant).
    batch = (
        db.query(ImportBatch)
        .filter(
            ImportBatch.id == import_batch_id,
            ImportBatch.organization_id == current_user.organization_id,
        )
        .first()
    )

    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lot d'import introuvable.",
        )

    return batch

