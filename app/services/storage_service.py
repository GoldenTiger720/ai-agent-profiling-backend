import logging
import os
from typing import Optional, Dict, Any, BinaryIO
from fastapi import UploadFile
import uuid
from app.utils.supabase_client import supabase
from app.config import settings

logger = logging.getLogger(__name__)

def init_storage_bucket():
    """
    Initialize storage bucket if it doesn't exist.
    """
    try:
        # Check if bucket exists
        buckets = supabase.storage.list_buckets()
        bucket_exists = any(bucket.name == settings.STORAGE_BUCKET for bucket in buckets)
        
        if not bucket_exists:
            # Create bucket
            supabase.storage.create_bucket(settings.STORAGE_BUCKET, {'public': False})
            logger.info(f"Created storage bucket: {settings.STORAGE_BUCKET}")
    except Exception as e:
        logger.error(f"Error initializing storage bucket: {str(e)}")

async def upload_file(file: UploadFile, user_id: str, file_type: str) -> Dict[str, Any]:
    """
    Upload file to Supabase storage.
    
    Args:
        file: File to upload
        user_id: User ID
        file_type: Type of file (e.g., 'pdf', 'image')
        
    Returns:
        Dictionary with file information
    """
    try:
        # Generate unique file path
        file_id = str(uuid.uuid4())
        file_ext = os.path.splitext(file.filename)[1].lower()
        file_path = f"{user_id}/{file_type}/{file_id}{file_ext}"
        
        # Read file content
        file_content = await file.read()
        
        # Upload file
        supabase.storage.from_(settings.STORAGE_BUCKET).upload(
            path=file_path,
            file=file_content,
            file_options={"content-type": file.content_type}
        )
        
        # Get public URL
        file_url = supabase.storage.from_(settings.STORAGE_BUCKET).get_public_url(file_path)
        
        # Return file information
        return {
            "id": file_id,
            "filename": file.filename,
            "content_type": file.content_type,
            "size": len(file_content),
            "path": file_path,
            "url": file_url
        }
    
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        raise

async def download_file(file_path: str) -> Optional[bytes]:
    """
    Download file from Supabase storage.
    
    Args:
        file_path: Path to file in storage
        
    Returns:
        File content as bytes if successful, None otherwise
    """
    try:
        # Download file
        response = supabase.storage.from_(settings.STORAGE_BUCKET).download(file_path)
        
        return response
    
    except Exception as e:
        logger.error(f"Error downloading file: {str(e)}")
        return None

def delete_file(file_path: str) -> bool:
    """
    Delete file from Supabase storage.
    
    Args:
        file_path: Path to file in storage
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Delete file
        supabase.storage.from_(settings.STORAGE_BUCKET).remove([file_path])
        
        return True
    
    except Exception as e:
        logger.error(f"Error deleting file: {str(e)}")
        return False

def list_user_files(user_id: str, file_type: Optional[str] = None) -> list:
    """
    List files for a user.
    
    Args:
        user_id: User ID
        file_type: Optional file type filter
        
    Returns:
        List of file information
    """
    try:
        # Determine path
        path = f"{user_id}"
        if file_type:
            path = f"{user_id}/{file_type}"
        
        # List files
        response = supabase.storage.from_(settings.STORAGE_BUCKET).list(path)
        
        # Get public URLs and add to response
        for item in response:
            item_path = f"{path}/{item['name']}"
            item['url'] = supabase.storage.from_(settings.STORAGE_BUCKET).get_public_url(item_path)
        
        return response
    
    except Exception as e:
        logger.error(f"Error listing user files: {str(e)}")
        return []

# Initialize storage bucket
# init_storage_bucket()