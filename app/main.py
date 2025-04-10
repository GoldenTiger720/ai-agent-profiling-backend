from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, profiles, uploads
from app.config import settings

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="API for automating speaker profile generation",
    version="1.0.0",
)

# CORS middleware setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update this for production to include only trusted domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)