from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class SignUpRequest(BaseModel):
    """Schema for sign-up request."""
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    """Schema for login request."""
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    """Schema for token response."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: str
    
class TokenData(BaseModel):
    """Schema for decoded token data."""
    user_id: Optional[str] = None
    email: Optional[EmailStr] = None