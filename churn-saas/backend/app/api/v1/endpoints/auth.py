import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.config import settings
from app.core.security import create_access_token, get_password_hash, verify_password
from app.models import Organization, User, RiskSettings,  PasswordResetToken
from app.schemas.auth import LoginRequest, Token
from app.schemas.user import RegisterRequest, UserRead

import hashlib

from app.schemas.auth import (
    ForgotPasswordRequest,
    PasswordResetMessage,
    ResetPasswordRequest,
)
from app.services.email_service import send_password_reset_email


router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserRead, status_code = status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> User:
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Un compte existe déjà avec cet email")
    if not payload.organization_name:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Le nom de l'organisation est requis")
    try:
        organization = Organization(
            name=payload.organization_name,
            api_key=secrets.token_urlsafe(32),
            is_active=True
        )
        db.add(organization)
        db.flush()  # Flush to get the organization ID

        user = User(
            organization_id=organization.id,
            email=payload.email.lower(),
            hashed_password=get_password_hash(payload.password),
            full_name= payload.full_name,
            role="admin",
            is_active=True,
        )
        db.add(user)
        db.flush()

        risk_settings= RiskSettings(
            organization_id= organization.id,
            threshold_high=0.7,
            threshold_medium=0.4,
            updated_by_user_id= user.id,
        )
        db.add(risk_settings)

        db.commit()
        db.refresh(user)
    except Exception :
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la création du compte",
        )

    return user

@router.post("/login", response_model=Token)
def login(
        form_data: OAuth2PasswordRequestForm = Depends(),
        db: Session = Depends(get_db)
) -> Token:
    user = db.query(User).filter(User.email == form_data.username.lower()).first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Compte désactivé")

    access_token = create_access_token(
        subject=user.id,
        organization_id=user.organization_id,
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
    )
    return Token(access_token=access_token, token_type="bearer")

@router.post("/login/json", response_model=Token)
def login_json(payload:LoginRequest, db:Session = Depends(get_db)) -> Token:
    #Variante JSON de /login, pratique pour le frontend Next.js.
    user = db.query(User).filter(User.email == payload.email.lower()).first()

    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect",
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Compte désactivé")

    access_token = create_access_token(
        subject=str(user.id),
        organization_id=user.organization_id,
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
    )
    return Token(access_token=access_token, token_type="bearer")


@router.get("/me", response_model=UserRead)
def read_current_user(current_user: User = Depends(get_current_active_user)) -> User:
    #Profil User
    return current_user

#forget password------------------

RESET_TOKEN_TTL_MINUTES = 30

GENERIC_RESET_MESSAGE = (
    "Si un compte correspond à cette adresse, un lien de réinitialisation "
    "va être envoyé."
)


@router.post(
    "/forgot-password",
    response_model=PasswordResetMessage,
)
def forgot_password(
    payload: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    email = str(payload.email).strip().lower()
    user = db.query(User).filter(User.email == email).first()

    # Réponse identique pour une adresse inconnue ou connue :
    # on ne révèle pas si un compte existe.
    if not user or not user.is_active:
        return {"message": GENERIC_RESET_MESSAGE}

    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=RESET_TOKEN_TTL_MINUTES
    )

    # Invalide les anciens jetons encore actifs.
    (
        db.query(PasswordResetToken)
        .filter(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.used_at.is_(None),
        )
        .delete(synchronize_session=False)
    )

    db.add(
        PasswordResetToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
    )
    db.commit()

    reset_url = (
        f"{settings.frontend_url.rstrip('/')}"
        f"/auth/reset-password?token={raw_token}"
    )

    # L'envoi se fait après la réponse HTTP ; le jeton n'est jamais renvoyé
    # dans la réponse API.
    background_tasks.add_task(
        send_password_reset_email,
        user.email,
        reset_url,
    )

    return {"message": GENERIC_RESET_MESSAGE}


@router.post(
    "/reset-password",
    response_model=PasswordResetMessage,
)
def reset_password(
    payload: ResetPasswordRequest,
    db: Session = Depends(get_db),
):
    now = datetime.now(timezone.utc)
    token_hash = hashlib.sha256(payload.token.encode("utf-8")).hexdigest()

    reset_record = (
        db.query(PasswordResetToken)
        .filter(
            PasswordResetToken.token_hash == token_hash,
            PasswordResetToken.used_at.is_(None),
            PasswordResetToken.expires_at > now,
        )
        .first()
    )

    if not reset_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le lien de réinitialisation est invalide ou a expiré.",
        )

    user = db.query(User).filter(User.id == reset_record.user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le lien de réinitialisation est invalide ou a expiré.",
        )

    user.hashed_password = get_password_hash(payload.new_password)
    reset_record.used_at = now

    # Invalide aussi tout autre jeton de réinitialisation actif du compte.
    (
        db.query(PasswordResetToken)
        .filter(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.id != reset_record.id,
            PasswordResetToken.used_at.is_(None),
        )
        .update(
            {PasswordResetToken.used_at: now},
            synchronize_session=False,
        )
    )

    db.commit()

    return {
        "message": "Le mot de passe a été réinitialisé. Tu peux te connecter."
    }


    
