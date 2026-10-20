from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, ConfigDict

#ORG
class OrganizationBase(BaseModel):
    name: str

class OrganizationCreate(OrganizationBase):
    pass

class OrganizationRead(OrganizationBase):
    id: str 
    isactive: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

#USR
class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    role: str ="admin"

class UserCreate(UserBase):
    password: str
    organization_name: Optional[str] = None

class UserRead(UserBase):
    id: str
    organization_id:str
    is_active:bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True) 