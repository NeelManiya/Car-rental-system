from pydantic import BaseModel, EmailStr
from typing import Optional


class RegisterUserSchema(BaseModel):
    name: str
    email: EmailStr
    phone_no: str
    password: str


class GetAllUserSchema(BaseModel):
    id: str
    name: str
    email: str
    password: str


class UpdateUserSchema(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None


class ForgetPasswordSchema(BaseModel):
    new_password: str
    confirm_password: str


class ResetPasswordSchema(BaseModel):
    old_password: str
    new_password: str
    confirm_password: str
