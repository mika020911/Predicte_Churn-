import logging
import smtplib
from email.message import EmailMessage

from app.config import settings

logger = logging.getLogger(__name__)


def send_password_reset_email(recipient: str, reset_url: str) -> None:
    """Envoie par SMTP le lien de réinitialisation."""
    if not settings.smtp_user or not settings.smtp_password or not settings.smtp_from_email:
        logger.error("Configuration SMTP manquante pour l'envoi de réinitialisation.")
        return

    message = EmailMessage()
    message["Subject"] = "Réinitialisation de votre mot de passe ChurnSight"
    message["From"] = (
        f"{settings.smtp_from_name} <{settings.smtp_from_email}>"
    )
    message["To"] = recipient
    message.set_content(
        "Bonjour,\n\n"
        "Pour choisir un nouveau mot de passe ChurnSight, ouvrez ce lien :\n"
        f"{reset_url}\n\n"
        "Ce lien expire dans 30 minutes et ne peut être utilisé qu'une seule fois.\n"
        "Si vous n'avez pas demandé cette réinitialisation, ignorez cet email.\n"
    )

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as smtp:
            smtp.starttls()
            smtp.login(settings.smtp_user, settings.smtp_password)
            smtp.send_message(message)
    except Exception:
        # Ne jamais écrire le mot de passe SMTP ou le jeton dans les logs.
        logger.exception("Échec de l'envoi de l'email de réinitialisation.")