from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict
from datetime import datetime
import uuid

class UserBase(BaseModel):
    """Base user model with common fields."""
    email: EmailStr

class UserCreate(UserBase):
    """Model for user creation."""
    password: str

class UserInDB(UserBase):
    """Model for user as stored in the database."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None

class User(UserBase):
    """User model for API responses."""
    id: str
    created_at: datetime

class Profile(BaseModel):
    """Speaker profile model."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    name: Optional[str] = None
    expertise: Optional[List[str]] = None
    target_audience: Optional[List[str]] = None
    activity_summary: Optional[str] = None
    personal_tone: Optional[str] = None
    strengths: Optional[List[str]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        from_attributes = True  # instead of orm_mode = True

class ProfileCreate(BaseModel):
    """Model for creating a profile with source data."""
    pdf_urls: Optional[List[str]] = None
    youtube_url: Optional[str] = None
    website_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    
class ProfileResponse(Profile):
    """Model for profile API responses."""
    pass

class Token(BaseModel):
    """Token model for authentication responses."""
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    """Token data model for decoded JWT tokens."""
    user_id: Optional[str] = None