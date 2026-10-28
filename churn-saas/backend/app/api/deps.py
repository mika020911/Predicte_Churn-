from typing import Generator

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from sqlalchemy.orm import Session

from app.config import settings
from app.core.security import ALGORITHM
from app.database import SessionLocal
from app.models import User
from app.schemas.auth import TokenPayload

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

from app.database import get_db

def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Identifiants invalides ou token expiré",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        print("--- [DIAG] PAYLOAD DÉCODÉ ---")
        print(payload)
        
        token_data = TokenPayload(**payload)
    except Exception as e:
        raise credentials_exception
        
    if token_data.sub is None:
        raise credentials_exception
        
    try:
        user_id_condition = int(token_data.sub)
    except ValueError:
        user_id_condition = token_data.sub
    user = db.query(User).filter(User.id == user_id_condition).first()
    
    if user is None:
        raise credentials_exception
    return user

def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Utilisateur inactif")
        
    if not current_user.organization.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Organisation inactive")
        
    return current_user

def get_current_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Droits administrateur requis")
    return current_user
