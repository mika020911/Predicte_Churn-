from datetime import datetime, timedelta, timezone
from typing import Optional, Union, Any
import jwt
import bcrypt
from pydantic import BaseModel, ConfigDict
from app.config import settings

ALGORITHM = "HS256"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Vérifie si un mot de passe brut correspond au hash stocké."""
    try:
        
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8")
        )
    except ValueError:
        return False

def get_password_hash(password: str) -> str:

    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")

def create_access_token(
        subject: Union[str, Any],
        organization_id: str,
        expires_delta: Optional[timedelta] = None
) -> str:
    
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.access_token_expire_minutes)
        
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode = {"exp": expire, "sub": str(subject), "org_id": organization_id}
    
    
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=ALGORITHM)
    return encoded_jwt
