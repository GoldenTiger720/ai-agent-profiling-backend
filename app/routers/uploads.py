from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Header, Request
from typing import List, Optional
from app.models.user import User
from app.services.auth_service import get_current_user
from app.services.storage_service import upload_file, list_user_files, delete_file
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/pdf")
async def upload_pdf_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    Upload a PDF file to Supabase storage.
    """
    # Check file type
    if not file.content_type or "application/pdf" not in file.content_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are allowed"
        )
    
    try:
        # Upload file
        file_info = await upload_file(file, current_user.id, "pdf")
        
        return {
            "message": "File uploaded successfully",
            "file_info": file_info
        }
    
    except Exception as e:
        logger.error(f"Error uploading PDF file: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}"
        )

@router.post("/multiple-pdfs")
async def upload_multiple_pdf_files(
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    Upload multiple PDF files to Supabase storage.
    """
    uploaded_files = []
    failed_files = []
    
    for file in files:
        # Check file type
        if not file.content_type or "application/pdf" not in file.content_type:
            failed_files.append({
                "filename": file.filename,
                "reason": "Not a PDF file"
            })
            continue
        
        try:
            # Upload file
            file_info = await upload_file(file, current_user.id, "pdf")
            uploaded_files.append(file_info)
        
        except Exception as e:
            logger.error(f"Error uploading PDF file {file.filename}: {str(e)}")
            failed_files.append({
                "filename": file.filename,
                "reason": str(e)
            })
    
    return {
        "message": f"Uploaded {len(uploaded_files)} files, {len(failed_files)} failed",
        "uploaded_files": uploaded_files,
        "failed_files": failed_files
    }

@router.get("/pdfs")
async def list_pdf_files(current_user: User = Depends(get_current_user)):
    """
    List all PDF files for the current user.
    """
    try:
        # List files
        files = list_user_files(current_user.id, "pdf")
        
        return {
            "files": files
        }
    
    except Exception as e:
        logger.error(f"Error listing PDF files: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list files: {str(e)}"
        )

@router.delete("/pdf/{file_path:path}")
async def delete_pdf_file(
    file_path: str,
    current_user: User = Depends(get_current_user)
):
    """
    Delete a PDF file from Supabase storage.
    """
    # Verify file belongs to user
    if not file_path.startswith(f"{current_user.id}/pdf/"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this file"
        )
    
    try:
        # Delete file
        success = delete_file(file_path)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete file"
            )
        
        return {
            "message": "File deleted successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting PDF file: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete file: {str(e)}"
        )