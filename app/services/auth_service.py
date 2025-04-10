from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.config import settings
from app.utils.supabase_client import supabase
from app.schemas.auth import TokenData
from app.models.user import User, UserInDB
import logging

logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme for token handling
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hash.
    
    Args:
        plain_password: Plain text password
        hashed_password: Hashed password from database
        
    Returns:
        True if password matches hash, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """
    Generate password hash.
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password
    """
    return pwd_context.hash(password)

def get_user(email: str) -> Optional[UserInDB]:
    """
    Get user from database by email.
    
    Args:
        email: User email
        
    Returns:
        User object if found, None otherwise
    """
    try:
        response = supabase.table("users").select("*").eq("email", email).execute()
        
        if response.data and len(response.data) > 0:
            user_data = response.data[0]
            return UserInDB(**user_data)
        return None
    except Exception as e:
        logger.error(f"Error getting user: {str(e)}")
        return None

def authenticate_user(email: str, password: str) -> Optional[User]:
    """
    Authenticate a user with email and password.
    
    Args:
        email: User email
        password: User password
        
    Returns:
        User object if authentication succeeds, None otherwise
    """
    user = get_user(email)
    if not user:
        return None
    if not verify_password(password, user.password):
        return None
    
    # Update last login timestamp
    try:
        supabase.table("users").update({"last_login": datetime.utcnow().isoformat()}).eq("id", user.id).execute()
    except Exception as e:
        logger.error(f"Error updating last login: {str(e)}")
    
    # Return user without password
    return User(id=user.id, email=user.email, created_at=user.created_at)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Data to encode in the token
        expires_delta: Token expiration time
        
    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SUPABASE_JWT_SECRET, algorithm="HS256")
    
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """
    Get current user from token.
    
    Args:
        token: JWT token
        
    Returns:
        User object
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, settings.SUPABASE_JWT_SECRET, algorithms=["HS256"])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        
        token_data = TokenData(user_id=user_id)
    except JWTError:
        raise credentials_exception
    
    try:
        response = supabase.table("users").select("*").eq("id", token_data.user_id).execute()
        
        if not response.data or len(response.data) == 0:
            raise credentials_exception
        
        user_data = response.data[0]
        return User(id=user_data["id"], email=user_data["email"], created_at=user_data["created_at"])
    except Exception as e:
        logger.error(f"Error getting current user: {str(e)}")
        raise credentials_exception

def register_new_user(email: str, password: str) -> User:
    """
    Register a new user.
    
    Args:
        email: User email
        password: User password
        
    Returns:
        Created user
        
    Raises:
        HTTPException: If user already exists or registration fails
    """
    # Check if user exists
    existing_user = get_user(email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash password
    hashed_password = get_password_hash(password)
    
    # Create user
    new_user = UserInDB(
        email=email,
        password=hashed_password,
    )
    
    try:
        response = supabase.table("users").insert({
            "id": new_user.id,
            "email": new_user.email,
            "password": new_user.password,
            "created_at": new_user.created_at.isoformat(),
            "last_login": None
        }).execute()
        
        if response.data and len(response.data) > 0:
            user_data = response.data[0]
            return User(id=user_data["id"], email=user_data["email"], created_at=user_data["created_at"])
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to register user"
            )
    except Exception as e:
        logger.error(f"Error registering user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register user: {str(e)}"
        )