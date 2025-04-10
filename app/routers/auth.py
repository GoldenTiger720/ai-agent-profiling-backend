from fastapi import APIRouter, Depends, HTTPException, status, Response, Cookie
from fastapi.security import OAuth2PasswordRequestForm
from typing import Optional
from datetime import datetime, timedelta
from app.schemas.auth import SignUpRequest, LoginRequest, TokenResponse
from app.services.auth_service import (
    authenticate_user, create_access_token, register_new_user, get_current_user
)
from app.config import settings
from app.models.user import User

router = APIRouter()

@router.post("/signup", response_model=TokenResponse)
async def signup(request: SignUpRequest):
    """
    Register a new user.
    """
    # Register user
    user = register_new_user(email=request.email, password=request.password)
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.id},
        expires_delta=access_token_expires
    )
    
    # Return token response
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user_id=user.id
    )

@router.post("/login", response_model=TokenResponse)
async def login(response: Response, request: LoginRequest):
    """
    Login with email and password.
    """
    # Authenticate user
    user = authenticate_user(email=request.email, password=request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.id},
        expires_delta=access_token_expires
    )
    
    # Set cookie with access token
    cookie_expires = int(access_token_expires.total_seconds())
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        max_age=cookie_expires,
        expires=cookie_expires,
        samesite="lax",
        secure=True  # Set to False in development if not using HTTPS
    )
    
    # Return token response
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user_id=user.id
    )

@router.post("/logout")
async def logout(response: Response):
    """
    Logout user by clearing access token cookie.
    """
    response.delete_cookie(key="access_token")
    return {"message": "Successfully logged out"}

@router.get("/me", response_model=User)
async def get_user_me(current_user: User = Depends(get_current_user)):
    """
    Get current user profile.
    """
    return current_user