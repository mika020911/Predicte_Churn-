import json
from typing import List, Optional
 
from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile, status
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session
 
from app.api.deps import get_current_active_user, get_db
from app.models import ImportBatch, Organization, User
from app.schemas.imports import ImportBatchRead, ImportBatchSummary, ImportMappingIn
from app.services.import_service import (
    build_csv_template,
    build_import_preview,
    normalize,
    process_csv_import,
    validate_column_mapping,
)


router = APIRouter(prefix="/imports", tags=["Imports"])


def _parse_mapping(raw:Optional[dict]) -> dict:
    if not raw:
        return None
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="format JSON invalide.")
    if not isinstance(data, dict):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Le mapping doit être un objet JSON.")
    return data

async def _read_csv_upload(file: UploadFile) -> bytes:
    if not (file.filename or "").lower().endswith(".csv"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Seuls les fichiers .csv sont autorisés.")
    file_bytes = await file.read()
    if len(file_bytes) == 0:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Le fichier téléversé est vide.")
    return file_bytes

@router.get("/template")
def download_csv_template(current_user: User = Depends(get_current_active_user)):
    """CSV modèle (en-têtes + exemples). Déclaré avant /{import_batch_id} pour ne pas être capturé par lui."""
    return Response(
        content=build_csv_template(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="modele_import_churnsight.csv"'},
    )
 
@router.post("/preview")
async def preview_csv_import(
    file: UploadFile = File(...),
    mapping: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Colonnes du CSV, suggestions de mapping, valeurs inconnues et colonnes ignorées.
 
    N'écrit rien en base. La colonne `churn` (étiquette d'entraînement) est ignorée : le modèle
    est entraîné hors de la base (approche 1).
    """
    file_bytes = await _read_csv_upload(file)
    org = db.get(Organization, current_user.organization_id)
    try:
        return await run_in_threadpool(build_import_preview, file_bytes, org, _parse_mapping(mapping))
    except ValueError as e:  # CSV illisible (ParserError, EmptyDataError...)
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Fichier CSV illisible : {e}")
    
#---------------------------MAPPING---------------------------------------------------

@router.put("/mapping")
def save_import_mapping(
    body: ImportMappingIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Sauvegarde le mapping de l'organisation (colonnes et valeurs de contract_type)."""
    org = db.get(Organization, current_user.organization_id)
 
    if body.column_mapping:
        merged = {**(org.column_mapping or {}), **body.column_mapping}
        problems = validate_column_mapping(merged)
        if problems:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, " | ".join(problems))
        org.column_mapping = {k: v for k, v in merged.items() if v}
 
    if body.contract_values:
        org.contract_mapping = {
            **(org.contract_mapping or {}),
            **{normalize(k): v for k, v in body.contract_values.items()},
        }
 
    db.commit()
    return {"column_mapping": org.column_mapping, "contract_mapping": org.contract_mapping}

#-----------------------------IMPORTS---------------------------------------------------

@router.post("/upload", response_model=ImportBatchRead, status_code=status.HTTP_201_CREATED)
async def upload_csv_import(
    file: UploadFile = File(...),
    mapping: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    #Importe un CSV : applique le mapping, valide, crée les clients et enregistre les snapshots
    file_bytes = await _read_csv_upload(file)
    return await run_in_threadpool(
        process_csv_import,
        file_bytes=file_bytes,
        filename=file.filename,
        current_user=current_user,
        db=db,
        column_mapping=_parse_mapping(mapping),
    )


@router.get("/", response_model=List[ImportBatchSummary])
def list_import_batches(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
#all import 
    batches =(
        db.query(ImportBatch)
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
    import_batch_id: int,
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

