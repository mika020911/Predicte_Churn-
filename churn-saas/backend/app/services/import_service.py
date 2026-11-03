import csv
import io
import math
import unicodedata
from datetime import datetime, timezone
 
import pandas as pd
from sqlalchemy.orm import Session
 
from app.models import Customer, ImportBatch, Observation, Organization, User


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
OPTIONAL_COLUMNS = ["customer_name", "customer_email"]
INTERNAL_FIELDS = REQUIRED_COLUMNS + OPTIONAL_COLUMNS

FLOAT_FIELDS = ("mrr_change_pct", "frequency_trend_30d", "engagement_breadth")
INT_FIELDS = ("tenure_months", "support_tickets_30d", "recency_days", "payment_failures_90d")

DEFAULT_CONTRACT_MAP = {
    "0": 0, "mensuel": 0, "monthly": 0,
    "1": 1, "annuel": 1, "annual": 1, "yearly": 1,
}

#Utilitaire
def normalize(value) -> str:
    """Ignore accents, majuscules et espaces parasites ('Jährlich ' -> 'jahrlich')."""
    text = unicodedata.normalize("NFKD", str(value))
    text = "".join(c for c in text if not unicodedata.combining(c))
    return text.strip().casefold()
 
 
def contract_key(value) -> str:
    """Clé de recherche pour contract_type ('1.0' exporté par Excel devient '1')."""
    key = normalize(value)
    return key[0] if key in ("0.0", "1.0") else key
 
 
def build_contract_map(org_mapping: dict | None) -> dict:
    custom = {normalize(k): v for k, v in (org_mapping or {}).items()}
    return {**DEFAULT_CONTRACT_MAP, **custom}  # le mapping du client est prioritaire
 
 
def to_int(value) -> int:
    """Convertit '12' ou '12.0' en 12, refuse '3.7' au lieu de le tronquer."""
    number = float(value)
    if not number.is_integer():
        raise ValueError(f"entier attendu, reçu {value}")
    return int(number)
 
 
def to_float(value) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"nombre fini attendu, reçu {value}")
    return number
 
 
def parse_number(row: dict, key: str, parser):
    """Convertit row[key] avec `parser` ; l'erreur nomme la colonne concernée."""
    value = row[key]
    if pd.isna(value):
        raise ValueError(f"{key} : valeur manquante")
    try:
        return parser(value)
    except ValueError as e:
        raise ValueError(f"{key} : {e}")
 
 
def read_csv_as_text(file_bytes: bytes) -> pd.DataFrame:
    """Lit le CSV en texte : les noms de colonnes ne sont pas connus avant le mapping."""
    try:
        df = pd.read_csv(io.BytesIO(file_bytes), dtype=str, encoding="utf-8-sig")
    except UnicodeDecodeError:
        df = pd.read_csv(io.BytesIO(file_bytes), dtype=str, encoding="latin-1")
    df.columns = [str(c).strip() for c in df.columns]
    return df
 
 
def build_csv_template() -> str:
    """CSV modèle téléchargeable : en-têtes + 2 lignes d'exemple valides."""
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(REQUIRED_COLUMNS + OPTIONAL_COLUMNS)
    writer.writerow(["C00001", "2026-01-15", 12, "mensuel", 2.5, 1, 5, 0.95, 0.7, 0,
                     "Client exemple", "client@exemple.com"])
    writer.writerow(["C00002", "2026-01-15", 36, "annuel", -1.2, 0, 2, 1.05, 0.9, 0, "", ""])
    return buffer.getvalue()
 
 
def suggest_column_mapping(csv_columns: list[str], saved: dict | None) -> dict:
    """champ interne -> colonne du CSV (ou None).
 
    Priorité : mapping fourni/sauvegardé (si la colonne existe encore),
    puis correspondance par nom normalisé.
    """
    saved = saved or {}
    by_norm = {normalize(c): c for c in csv_columns}
    result = {}
    for field in INTERNAL_FIELDS:
        if saved.get(field) in csv_columns:
            result[field] = saved[field]
        else:
            result[field] = by_norm.get(normalize(field))
    return result
 
 
def validate_column_mapping(mapping: dict) -> list[str]:
    """Retourne la liste des problèmes (vide = mapping valide)."""
    problems = []
    unmapped = [f for f in REQUIRED_COLUMNS if not mapping.get(f)]
    if unmapped:
        problems.append(f"Champs obligatoires non mappés : {', '.join(unmapped)}")
    used = [c for c in mapping.values() if c]
    dupes = sorted({c for c in used if used.count(c) > 1})
    if dupes:
        problems.append(f"Colonnes utilisées plusieurs fois : {dupes}")
    return problems
 
 
def apply_column_mapping(df: pd.DataFrame, mapping: dict) -> pd.DataFrame:
    """Garde les colonnes mappées et les renomme avec les noms internes."""
    rename = {csv_col: field for field, csv_col in mapping.items() if csv_col}
    return df[list(rename)].rename(columns=rename)
 
 
def build_import_preview(file_bytes: bytes, org: Organization, sent_mapping: dict | None = None) -> dict:
    """Aperçu pour l'écran de mapping. N'écrit rien en base."""
    df = read_csv_as_text(file_bytes)
    saved = org.column_mapping or {}
    mapping = suggest_column_mapping(list(df.columns), {**saved, **(sent_mapping or {})})
 
    unknown: list[str] = []
    contract_col = mapping.get("contract_type")
    if contract_col:
        contract_map = build_contract_map(org.contract_mapping)
        unknown = sorted(
            {contract_key(v) for v in df[contract_col].dropna()} - set(contract_map) - {""}
        )
 
    used_columns = {c for c in mapping.values() if c}
    return {
        "csv_columns": list(df.columns),
        # Colonnes du CSV non importées (ex. `churn` : l'étiquette reste hors base, approche 1)
        "ignored_columns": [c for c in df.columns if c not in used_columns],
        "fields": [
            {"field": f, "required": f in REQUIRED_COLUMNS, "mapped_to": mapping[f]}
            for f in INTERNAL_FIELDS
        ],
        "sample_rows": df.head(5).fillna("").to_dict("records"),
        "unknown_contract_values": unknown,
        "problems": validate_column_mapping(mapping),
        # True si l'organisation a déjà confirmé un mapping complet pour ce fichier
        "confirmed": all(saved.get(f) in df.columns for f in REQUIRED_COLUMNS),
    }
# Import

def process_csv_import(
    file_bytes: bytes,
    filename: str,
    current_user: User,
    db: Session,
    column_mapping: dict | None = None,
) -> ImportBatch:
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
    db.commit()
    batch_id = batch.id


    try:
        df = read_csv_as_text(file_bytes)
        batch.total_rows = len(df)
 
        # --- Mapping des colonnes : requête > organisation > détection par nom
        org = db.get(Organization, org_id)
        mapping = suggest_column_mapping(
            list(df.columns),
            {**(org.column_mapping or {}), **(column_mapping or {})},
        )
        problems = validate_column_mapping(mapping)
        if problems:
            batch.status = "FAILED"
            batch.error_message = " | ".join(problems)
            batch.completed_at = datetime.now(timezone.utc)
            db.commit()
            return batch
 
        df = apply_column_mapping(df, mapping)
        contract_map = build_contract_map(org.contract_mapping)
 
        anomalies: list[dict] = []
        imported_count = 0
 
        def add_anomaly(row_num, ext_id, error_type, message):
            anomalies.append({
                "row_number": row_num,
                "external_id": ext_id,
                "error_type": error_type,
                "message": message,
            })
 
        # Cache des clients de l'organisation
        existing_customers = {
            c.external_id: c
            for c in db.query(Customer).filter(Customer.organization_id == org_id).all()
        }
        # Couples (client, date) déjà en base : une seule requête au lieu d'une par ligne
        existing_pairs = {
            (cid, d)
            for cid, d in db.query(Observation.customer_id, Observation.snapshot_date)
            .join(Customer, Customer.id == Observation.customer_id)
            .filter(Customer.organization_id == org_id)
            .all()
        }
        seen_in_file: set = set()
 
        for pos, row in enumerate(df.to_dict("records")):
            row_num = pos + 2  # ligne 1 = en-tête
 
            # 1. ID externe
            raw_id = row["customer_id"]
            ext_id = str(raw_id).strip() if pd.notna(raw_id) else ""
            if not ext_id:
                add_anomaly(row_num, None, "MISSING_CUSTOMER_ID",
                            "Le champ customer_id est obligatoire.")
                continue
 
            # 2. Date
            raw_date = row["snapshot_date"]
            try:
                ts = pd.to_datetime(raw_date)
                if pd.isna(ts):
                    raise ValueError("date manquante")
                snapshot_dt = ts.date()
            except (ValueError, TypeError, OverflowError):
                add_anomaly(row_num, ext_id, "INVALID_DATE",
                            f"Format de date invalide : {raw_date}")
                continue
 
            # 3. Conversion de tous les champs AVANT toute écriture en base
            try:
                raw_contract = row["contract_type"]
                if pd.isna(raw_contract):
                    raise ValueError("contract_type manquant")
                contract_value = contract_map.get(contract_key(raw_contract))
                if contract_value is None:  # ne pas écrire `if not` : 0 est un contrat valide
                    raise ValueError(
                        f"contract_type non reconnu : '{raw_contract}' "
                        "(attendu : mensuel/annuel, 0/1 ou une valeur du mapping)"
                    )
                floats = {k: parse_number(row, k, to_float) for k in FLOAT_FIELDS}
                ints = {k: parse_number(row, k, to_int) for k in INT_FIELDS}
            except (ValueError, TypeError, OverflowError) as e:
                add_anomaly(row_num, ext_id, "DATA_PARSING_ERROR",
                            f"Erreur de conversion de types : {e}")
                continue
 
            # 4. Doublons : dans le fichier, puis en base
            key = (ext_id, snapshot_dt)
            customer = existing_customers.get(ext_id)
            if key in seen_in_file:
                add_anomaly(row_num, ext_id, "DUPLICATE_SNAPSHOT",
                            f"Ce client apparaît déjà à la date {snapshot_dt} dans le fichier")
                continue
            if customer is not None and (customer.id, snapshot_dt) in existing_pairs:
                add_anomaly(row_num, ext_id, "DUPLICATE_SNAPSHOT",
                            f"Une observation existe déjà pour ce client à la date {snapshot_dt}")
                continue
 
            # 5. Création du client (la ligne est valide à ce stade)
            if customer is None:
                raw_name = row.get("customer_name")
                raw_email = row.get("customer_email")
                name = str(raw_name).strip() if pd.notna(raw_name) else ""
                email = str(raw_email).strip() if pd.notna(raw_email) else ""
                customer = Customer(
                    organization_id=org_id,
                    external_id=ext_id,
                    name=name or f"Client {ext_id}",
                    email=email or None,
                )
                db.add(customer)
                db.flush()
                existing_customers[ext_id] = customer
 
            # 6. Observation
            db.add(Observation(
                customer_id=customer.id,
                import_batch_id=batch_id,
                snapshot_date=snapshot_dt,
                # str() : fonctionne que la colonne soit String ("0"/"1") ou Integer
                contract_type=str(contract_value),
                **floats,
                **ints,
            ))
            seen_in_file.add(key)
            imported_count += 1
 
        batch.imported_rows = imported_count
        batch.error_rows = len(anomalies)
        batch.anomaly_report = anomalies
        batch.status = "COMPLETED" if imported_count > 0 else "FAILED"
        batch.completed_at = datetime.now(timezone.utc)
 
        db.commit()
        db.refresh(batch)
        return batch
    except Exception as e:
        db.rollback()
        batch = db.get(ImportBatch, batch_id)
        batch.status = "FAILED"
        batch.error_message = f"Erreur critique lors du traitement du fichier : {str(e)}"
        batch.completed_at = datetime.now(timezone.utc)
        db.commit()
        return batch
