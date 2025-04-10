from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List, Dict, Any
from datetime import datetime

class ProfileSourcesRequest(BaseModel):
    """Schema for profile data sources request."""
    youtube_url: Optional[HttpUrl] = None
    website_url: Optional[HttpUrl] = None
    linkedin_url: Optional[HttpUrl] = None
    # PDF files are handled separately via file upload

class ProfileResponse(BaseModel):
    """Schema for profile response."""
    id: str
    user_id: str
    name: Optional[str] = None
    expertise: Optional[List[str]] = None
    target_audience: Optional[List[str]] = None
    activity_summary: Optional[str] = None
    personal_tone: Optional[str] = None
    strengths: Optional[List[str]] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True  # instead of orm_mode = True

class RawProfileData(BaseModel):
    """Schema for raw profile data collected from sources."""
    pdf_text: Optional[List[str]] = None
    youtube_data: Optional[Dict[str, Any]] = None
    website_text: Optional[str] = None
    linkedin_data: Optional[Dict[str, Any]] = None

class ProfileGenerationRequest(BaseModel):
    """Schema for profile generation request."""
    raw_data: RawProfileData