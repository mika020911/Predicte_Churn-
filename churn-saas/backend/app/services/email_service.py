import logging
import smtplib
from email.message import EmailMessage

from app.config import settings

logger = logging.getLogger(__name__)

ROLE_LABELS = {
    "admin": "administrateur",
    "analyst": "analyste",
    "viewer": "lecture seule",
}


def _smtp_is_configured() -> bool:
    return bool(
        settings.smtp_user
        and settings.smtp_password
        and settings.smtp_from_email
    )


def _send_email(recipient: str, subject: str, body: str) -> bool:
    """Envoie un email et renvoie True/False. Ne journalise jamais le corps."""
    if settings.email_dry_run:
        logger.info("Email non envoyé (dry-run) à %s : %s", recipient, subject)
        return True

    if not _smtp_is_configured():
        logger.error(
            "Configuration SMTP manquante : email non envoyé à %s.", recipient
        )
        return False

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = f"{settings.smtp_from_name} <{settings.smtp_from_email}>"
    message["To"] = recipient
    message.set_content(body)

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as smtp:
            smtp.starttls()
            smtp.login(settings.smtp_user, settings.smtp_password)
            smtp.send_message(message)
    except Exception:
        # Ne jamais écrire le mot de passe SMTP ou le jeton dans les logs.
        logger.exception("Échec de l'envoi d'un email à %s.", recipient)
        return False
    return True


def send_password_reset_email(recipient: str, reset_url: str) -> bool:
    """Envoie par SMTP le lien de réinitialisation."""
    body = (
        "Bonjour,\n\n"
        "Pour choisir un nouveau mot de passe ChurnSight, ouvrez ce lien :\n"
        f"{reset_url}\n\n"
        "Ce lien expire dans 30 minutes et ne peut être utilisé qu'une seule fois.\n"
        "Si vous n'avez pas demandé cette réinitialisation, ignorez cet email.\n"
    )
    return _send_email(
        recipient,
        "Réinitialisation de votre mot de passe ChurnSight",
        body,
    )


def send_invitation_email(
    recipient: str,
    organization_name: str,
    role: str,
    invite_url: str,
) -> bool:
    """Envoie l'invitation à rejoindre une organisation."""
    role_label = ROLE_LABELS.get(role, role)
    body = (
        f"Bonjour,\n\n"
        f"{organization_name} vous invite à rejoindre ChurnSight "
        f"avec le rôle « {role_label} ».\n\n"
        "Pour créer votre compte, ouvrez ce lien :\n"
        f"{invite_url}\n\n"
        f"Ce lien expire dans {settings.invitation_expire_hours // 24} jours "
        "et ne peut être utilisé qu'une seule fois.\n"
        "Si vous n'êtes pas à l'origine de cette demande, ignorez cet email.\n"
    )
    return _send_email(
        recipient,
        f"Invitation à rejoindre {organization_name} sur ChurnSight",
        body,
    )
