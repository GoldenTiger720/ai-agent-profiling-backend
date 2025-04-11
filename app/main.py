from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, profiles, uploads
from app.config import settings
from app.services.storage_service import init_storage_bucket
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="API for automating speaker profile generation",
    version="1.0.0",
)

# CORS middleware setup with more permissive settings for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins in development
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# Include routers
app.include_router(
    auth.router,
    prefix=f"{settings.API_V1_STR}/auth",
    tags=["Authentication"]
)
app.include_router(
    profiles.router,
    prefix=f"{settings.API_V1_STR}/profiles",
    tags=["Profiles"]
)
app.include_router(
    uploads.router,
    prefix=f"{settings.API_V1_STR}/uploads",
    tags=["Uploads"]
)

@app.get("/")
async def root():
    return {"message": f"Welcome to the {settings.APP_NAME} API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Initialize storage bucket on startup
@app.on_event("startup")
async def startup_event():
    logging.info("Initializing application...")
    # Initialize storage bucket
    init_storage_bucket()
    logging.info("Application startup complete")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)