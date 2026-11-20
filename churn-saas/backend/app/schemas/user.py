from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, ConfigDict

#ORG
class OrganizationBase(BaseModel):
    name: str

class OrganizationCreate(OrganizationBase):
    pass

class OrganizationRead(OrganizationBase):
    id: int
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

#USR
class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    role: str ="admin"

class RegisterRequest(BaseModel):
    """Inscription publique : le rôle n'est jamais fourni par le client."""

    email: EmailStr
    password: str
    full_name: str
    organization_name: str


class UserCreate(UserBase):
    """Création interne d'un utilisateur (usage serveur uniquement)."""

    password: str
    organization_name: Optional[str] = None

class UserRead(UserBase):
    id: int
    organization_id:int
    is_active:bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True) 