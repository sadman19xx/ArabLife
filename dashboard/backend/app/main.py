from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import os

from .database import get_db, init_db
from .models import Base
from .schemas import *
from .auth import *
from .routers import bot, guilds, commands, settings, automod, leveling, auth

app = FastAPI(
    title="ArabLife Bot Dashboard",
    description="API for managing the ArabLife Discord bot",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",          # Local development
        "http://localhost",               # Local production
        "http://45.76.83.149",           # Server production
        "http://45.76.83.149:3000",      # Server development
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(bot.router)
app.include_router(guilds.router)
app.include_router(commands.router)
app.include_router(settings.router)
app.include_router(automod.router)
app.include_router(leveling.router)

@app.on_event("startup")
async def startup_event():
    """Initialize database and create tables on startup."""
    try:
        await init_db()
    except Exception as e:
        print(f"Failed to initialize database: {e}")
        raise

@app.get("/")
async def root():
    """Root endpoint returning API information."""
    return {
        "name": "ArabLife Bot Dashboard API",
        "version": "1.0.0",
        "status": "running",
        "docs_url": "/docs",
        "redoc_url": "/redoc"
    }

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "database": "connected"  # This will fail if DB connection is not working due to dependency
    }

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions."""
    return {
        "detail": exc.detail,
        "status_code": exc.status_code
    }, exc.status_code

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions."""
    return {
        "detail": "Internal server error",
        "status_code": 500
    }, 500

# Additional configuration
if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment or use default
    port = int(os.getenv("PORT", 8000))
    
    # Get host from environment or use default
    host = os.getenv("HOST", "0.0.0.0")
    
    # Run the application
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=True,  # Enable auto-reload
        workers=1     # Use single worker for development
    )
