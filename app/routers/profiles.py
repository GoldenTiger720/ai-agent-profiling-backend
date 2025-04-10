from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.models.user import User, Profile, ProfileResponse
from app.schemas.profile import ProfileSourcesRequest, ProfileGenerationRequest, RawProfileData
from app.services.auth_service import get_current_user
from app.services.pdf_service import process_pdf_for_profile
from app.services.youtube_service import process_youtube_channel
from app.services.website_service import crawl_website
from app.services.linkedin_service import process_linkedin_profile
from app.services.openai_service import generate_speaker_profile
from app.services.storage_service import download_file
from app.utils.supabase_client import supabase
import logging
import json
import uuid

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/create", response_model=ProfileResponse)
async def create_profile(
    request: ProfileSourcesRequest,
    pdf_urls: Optional[List[str]] = Query(None),
    current_user: User = Depends(get_current_user)
):
    """
    Create a speaker profile using all provided sources.
    """
    try:
        # 1. Initialize data container
        raw_data = RawProfileData(
            pdf_text=[],
            youtube_data=None,
            website_text=None,
            linkedin_data=None
        )
        
        # 2. Process PDF documents
        if pdf_urls:
            for pdf_url in pdf_urls:
                try:
                    # Get file path from URL (stored in Supabase)
                    file_path = pdf_url.split("/")[-1]
                    
                    # Download PDF from storage
                    pdf_bytes = await download_file(file_path)
                    
                    if pdf_bytes:
                        # Process PDF
                        pdf_text = process_pdf_for_profile(pdf_bytes)
                        raw_data.pdf_text.extend(pdf_text)
                except Exception as e:
                    logger.error(f"Error processing PDF {pdf_url}: {str(e)}")
        
        # 3. Process YouTube channel
        if request.youtube_url:
            try:
                youtube_data = process_youtube_channel(str(request.youtube_url))
                raw_data.youtube_data = youtube_data
            except Exception as e:
                logger.error(f"Error processing YouTube channel: {str(e)}")
        
        # 4. Process website
        if request.website_url:
            try:
                website_data = crawl_website(str(request.website_url))
                raw_data.website_text = website_data
            except Exception as e:
                logger.error(f"Error processing website: {str(e)}")
        
        # 5. Process LinkedIn profile
        if request.linkedin_url:
            try:
                linkedin_data = process_linkedin_profile(str(request.linkedin_url))
                raw_data.linkedin_data = linkedin_data
            except Exception as e:
                logger.error(f"Error processing LinkedIn profile: {str(e)}")
        
        # 6. Generate speaker profile with OpenAI
        profile_data = generate_speaker_profile({
            "pdf_text": raw_data.pdf_text,
            "youtube_data": raw_data.youtube_data,
            "website_text": raw_data.website_text,
            "linkedin_data": raw_data.linkedin_data
        })
        
        # 7. Save profile to database
        profile_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        
        profile_record = {
            "id": profile_id,
            "user_id": current_user.id,
            "name": profile_data.get("name", ""),
            "expertise": json.dumps(profile_data.get("expertise", [])),
            "target_audience": json.dumps(profile_data.get("target_audience", [])),
            "activity_summary": profile_data.get("activity_summary", ""),
            "personal_tone": profile_data.get("personal_tone", ""),
            "strengths": json.dumps(profile_data.get("strengths", [])),
            "created_at": now,
            "updated_at": now
        }
        
        # Insert into database
        response = supabase.table("profiles").insert(profile_record).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save profile"
            )
        
        # 8. Return profile
        created_profile = Profile(
            id=profile_id,
            user_id=current_user.id,
            name=profile_data.get("name", ""),
            expertise=profile_data.get("expertise", []),
            target_audience=profile_data.get("target_audience", []),
            activity_summary=profile_data.get("activity_summary", ""),
            personal_tone=profile_data.get("personal_tone", ""),
            strengths=profile_data.get("strengths", []),
            created_at=datetime.fromisoformat(now),
            updated_at=datetime.fromisoformat(now)
        )
        
        return ProfileResponse.from_orm(created_profile)
    
    except Exception as e:
        logger.error(f"Error creating profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create profile: {str(e)}"
        )

@router.get("/list", response_model=List[ProfileResponse])
async def list_profiles(current_user: User = Depends(get_current_user)):
    """
    List all profiles for the current user.
    """
    try:
        # Get profiles from database
        response = supabase.table("profiles").select("*").eq("user_id", current_user.id).execute()
        
        profiles = []
        for item in response.data:
            # Convert JSON strings to lists
            item["expertise"] = json.loads(item["expertise"])
            item["target_audience"] = json.loads(item["target_audience"])
            item["strengths"] = json.loads(item["strengths"])
            
            # Convert to Profile model
            profile = Profile(
                id=item["id"],
                user_id=item["user_id"],
                name=item["name"],
                expertise=item["expertise"],
                target_audience=item["target_audience"],
                activity_summary=item["activity_summary"],
                personal_tone=item["personal_tone"],
                strengths=item["strengths"],
                created_at=datetime.fromisoformat(item["created_at"]),
                updated_at=datetime.fromisoformat(item["updated_at"])
            )
            
            profiles.append(profile)
        
        return [ProfileResponse.from_orm(profile) for profile in profiles]
    
    except Exception as e:
        logger.error(f"Error listing profiles: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list profiles: {str(e)}"
        )

@router.get("/{profile_id}", response_model=ProfileResponse)
async def get_profile(
    profile_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific profile by ID.
    """
    try:
        # Get profile from database
        response = supabase.table("profiles").select("*").eq("id", profile_id).eq("user_id", current_user.id).execute()
        
        if not response.data or len(response.data) == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found"
            )
        
        item = response.data[0]
        
        # Convert JSON strings to lists
        item["expertise"] = json.loads(item["expertise"])
        item["target_audience"] = json.loads(item["target_audience"])
        item["strengths"] = json.loads(item["strengths"])
        
        # Convert to Profile model
        profile = Profile(
            id=item["id"],
            user_id=item["user_id"],
            name=item["name"],
            expertise=item["expertise"],
            target_audience=item["target_audience"],
            activity_summary=item["activity_summary"],
            personal_tone=item["personal_tone"],
            strengths=item["strengths"],
            created_at=datetime.fromisoformat(item["created_at"]),
            updated_at=datetime.fromisoformat(item["updated_at"])
        )
        
        return ProfileResponse.from_orm(profile)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get profile: {str(e)}"
        )

@router.delete("/{profile_id}")
async def delete_profile(
    profile_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Delete a specific profile by ID.
    """
    try:
        # Check if profile exists and belongs to user
        response = supabase.table("profiles").select("id").eq("id", profile_id).eq("user_id", current_user.id).execute()
        
        if not response.data or len(response.data) == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found"
            )
        
        # Delete profile
        supabase.table("profiles").delete().eq("id", profile_id).execute()
        
        return {"message": "Profile deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete profile: {str(e)}"
        )