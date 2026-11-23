"""Génération des exports CSV/XLSX (clients, rapports d'import).

Neutralise les formules tableur : une cellule texte commençant par =, +, - ou @
est préfixée par une apostrophe pour ne pas être exécutée à l'ouverture.
"""

import csv
import io
from datetime import date

from openpyxl import Workbook

MAX_EXPORT_ROWS = 50_000
_FORMULA_PREFIXES = ("=", "+", "-", "@")


def neutralise_formula(value):
    """Empêche l'injection de formules dans un tableur."""
    if isinstance(value, str) and value.startswith(_FORMULA_PREFIXES):
        return "'" + value
    return value


def export_filename(prefix: str, extension: str) -> str:
    return f"{prefix}_{date.today().isoformat()}.{extension}"


def to_csv(headers: list[str], rows: list[list]) -> bytes:
    """CSV encodé en utf-8-sig (BOM pour Excel)."""
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(headers)
    for row in rows:
        writer.writerow([neutralise_formula(value) for value in row])
    return buffer.getvalue().encode("utf-8-sig")


def to_xlsx(headers: list[str], rows: list[list]) -> bytes:
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(headers)
    for row in rows:
        sheet.append([neutralise_formula(value) for value in row])

    buffer = io.BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def render_export(fmt: str, headers: list[str], rows: list[list]) -> tuple[bytes, str, str]:
    """Renvoie (contenu, media_type, extension)."""
    if fmt == "xlsx":
        return (
            to_xlsx(headers, rows),
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "xlsx",
        )
    return to_csv(headers, rows), "text/csv; charset=utf-8", "csv"
