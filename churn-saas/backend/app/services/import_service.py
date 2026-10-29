import io
from datetime import datetime, timezone
import pandas as pd
from sqlalchemy.orm import Session

from app .models import Customer, ImportBatch, Observation, User

REQUIRED_COLUMNS = [
    "customer_id",  # identifiant externe du client chez le tenant
    "snapshot_date",
    "tenure_months",
    "contract_type",
    "mrr_change_pct",
    "support_tickets_30d",
    "recency_days",
    "frequency_trend_30d",
    "engagement_breadth",
    "payment_failures_90d",
]

def process_csv_import (
    file_bytes: bytes,
    filename: str,
    current_user: User,
    db: Session,
)-> ImportBatch:
    org_id = current_user.organization_id

    batch = ImportBatch(
        organization_id=org_id,
        uploaded_by_user_id=current_user.id,
        filename=filename,
        source="csv_upload",
        status="PROCESSING",
        total_rows=0,
        imported_rows=0,
        error_rows=0,
        anomaly_report=[],        
    )
    db.add(batch)
    db.flush()

    try:
        df = pd.read_csv(io.BytesIO(file_bytes))
        batch.total_rows = len(df)

        #verification des col
        missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
        if missing_cols:
            batch.status = "FAILED"
            batch.error_message =f"Colonnes requises manquantes : {', '.join(missing_cols)}"
            batch.completed_at = datetime.now(timezone.utc)
            db.commit()
            return batch
        
        anomalies=[]
        imported_count = 0
        error_count = 0

        #index client pour accelerer la recherche
        existing_customers = {
            c.external_id:c
            for c in db.query(Customer).filter(Customer.organization_id == org_id).all()
        }

        for idx, row in df.iterrows():
            row_num = idx + 2 
            ext_id = str(row["customer_id"]).strip() if pd.notna(row["customer_id"]) else None
            
            if not ext_id:
                error_count += 1
                anomalies.append({
                    "row_number": row_num,
                    "external_id": None,
                    "error_type": "MISSING_CUSTOMER_ID",
                    "message": "Le champ customer_id est obligatoire."                    
                })
                continue
            #creation et recupdes client
            customer = existing_customers.get(ext_id)
            if not customer :
                customer_name = str(row.get("customer_name", f"Client {ext_id}")) if pd.notna(row.get("customer_name")) else f"Client {ext_id}"  
                customer_email = str(row.get("customer_email", "")) if pd.notna(row.get("customer_email")) else None

                custumer = Customer(
                    organization_id=org_id,
                    external_id=ext_id,
                    name=customer_name,
                    email=customer_email,
                )
                db.add(customer)
                db.flush()
                existing_customers[ext_id] = customer

                #conserve/valide de la snapshot date
                try:
                    snapshot_dt =pd.to_datetime(row["snapshot_date"]).date()
                except Exception:
                    error_count += 1
                    anomalies.append({
                    "row_number": row_num,
                    "external_id": ext_id,
                    "error_type": "INVALID_DATE",
                    "message": f"Format de date invalide : {row['snapshot_date']}"
                })
                continue
            #(1 seule observation par client/date)

            duplicate_obs= (db.query(Observation).filter(
                Observation.customer_id == customer.id,
                Observation.snapshot_date == snapshot_dt,

            ).first()
            )
            if duplicate_obs:
                error_count += 1
                anomalies.append({
                    "row_number": row_num,
                    "external_id": ext_id,
                    "error_type": "DUPLICATE_SNAPSHOT",
                    "message": f"Une observation existe déjà pour ce client à la date {snapshot_dt}"
                })
                continue

            # Conversion des valeurs numériques avec gestion d'erreurs
            try:
                obs = Observation(
                    customer_id=customer.id,
                    import_batch_id=batch.id,
                    snapshot_date=snapshot_dt,
                    tenure_months=int(row["tenure_months"]),
                    contract_type=str(row["contract_type"]).strip().lower(),
                    mrr_change_pct=float(row["mrr_change_pct"]),
                    support_tickets_30d=int(row["support_tickets_30d"]),
                    recency_days=int(row["recency_days"]),
                    frequency_trend_30d=float(row["frequency_trend_30d"]),
                    engagement_breadth=float(row["engagement_breadth"]),
                    payment_failures_90d=int(row["payment_failures_90d"]),
                )
                db.add(obs)
                imported_count += 1
            except Exception as e :
                error_count += 1
                anomalies.append({
                    "row_number": row_num,
                    "external_id": ext_id,
                    "error_type": "DATA_PARSING_ERROR",
                    "message": f"Erreur de conversion de types : {str(e)}"
                })
        batch.imported_rows = imported_count
        batch.error_rows = error_count
        batch.anomaly_report = anomalies
        batch.status = "COMPLETED" if imported_count > 0 else "FAILED"
        batch.completed_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(batch)
        return batch
    except Exception as e:
        db.rollback()
        batch.status = "FAILED"
        batch.error_message = f"Erreur critique lors du traitement du fichier : {str(e)}"
        batch.completed_at = datetime.now(timezone.utc)
        db.commit()
        return batch