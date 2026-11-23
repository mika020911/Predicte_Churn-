"""Règle de mot de passe commune à l'inscription, la réinitialisation et l'invitation."""

from typing import Annotated

from pydantic import AfterValidator

PASSWORD_MIN_LENGTH = 12
PASSWORD_MAX_LENGTH = 128


def validate_password(value: str) -> str:
    if len(value) < PASSWORD_MIN_LENGTH:
        raise ValueError(
            f"Le mot de passe doit contenir au moins {PASSWORD_MIN_LENGTH} caractères."
        )
    if len(value) > PASSWORD_MAX_LENGTH:
        raise ValueError(
            f"Le mot de passe ne doit pas dépasser {PASSWORD_MAX_LENGTH} caractères."
        )
    return value


Password = Annotated[str, AfterValidator(validate_password)]
