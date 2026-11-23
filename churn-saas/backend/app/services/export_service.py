"""Génération des exports CSV/XLSX (clients, rapports d'import).

Neutralise les formules tableur : en CSV, une cellule texte commençant par =, +, - ou @
est préfixée par une apostrophe (sauf les numéros de téléphone) ; en XLSX, seules les
valeurs commençant par = sont préfixées.
"""

import csv
import io
import re
from datetime import date

from openpyxl import Workbook

MAX_EXPORT_ROWS = 50_000
_FORMULA_PREFIXES = ("=", "+", "-", "@")
_PHONE_PATTERN = re.compile(r"^\+?[0-9() .-]+$")


def is_phone_number(value) -> bool:
    """Un numéro de téléphone ne doit pas être préfixé (sinon il devient du texte)."""
    if not isinstance(value, str) or not _PHONE_PATTERN.fullmatch(value.strip()):
        return False
    # Un vrai numéro contient plusieurs chiffres : évite de blanchir « -1+1 ».
    return sum(character.isdigit() for character in value) >= 6


def neutralise_csv(value):
    """CSV : apostrophe devant =, +, - ou @, sauf pour un numéro de téléphone."""
    if (
        isinstance(value, str)
        and value.startswith(_FORMULA_PREFIXES)
        and not is_phone_number(value)
    ):
        return "'" + value
    return value


def neutralise_xlsx(value):
    """XLSX : openpyxl n'interprète comme formule que les valeurs commençant par =."""
    if isinstance(value, str) and value.startswith("="):
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
        writer.writerow([neutralise_csv(value) for value in row])
    return buffer.getvalue().encode("utf-8-sig")


def to_xlsx(headers: list[str], rows: list[list]) -> bytes:
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(headers)
    for row in rows:
        sheet.append([neutralise_xlsx(value) for value in row])

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
