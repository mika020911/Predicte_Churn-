"""Règle de mot de passe commune à l'inscription, la réinitialisation et l'invitation."""

from typing import Annotated

from pydantic import AfterValidator

PASSWORD_MIN_LENGTH = 12
# bcrypt refuse les mots de passe de plus de 72 octets UTF-8.
PASSWORD_MAX_BYTES = 72


def validate_password(value: str) -> str:
    if len(value) < PASSWORD_MIN_LENGTH:
        raise ValueError(
            f"Le mot de passe doit contenir au moins {PASSWORD_MIN_LENGTH} caractères."
        )
    if len(value.encode("utf-8")) > PASSWORD_MAX_BYTES:
        raise ValueError(
            "Le mot de passe ne doit pas dépasser 72 octets en UTF-8 "
            "(limite de bcrypt)."
        )
    return value


Password = Annotated[str, AfterValidator(validate_password)]
