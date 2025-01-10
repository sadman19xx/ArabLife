from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import os

from .database import get_db
from .models import Base
from .schemas import *
from .auth import *
from .routers import bot, guilds, commands, settings, automod, leveling

app = FastAPI(title="ArabLife Bot Dashboard")

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
app.include_router(bot.router, prefix="/api/bot", tags=["bot"])
app.include_router(guilds.router, prefix="/api/guilds", tags=["guilds"])
app.include_router(commands.router, prefix="/api/commands", tags=["commands"])
app.include_router(settings.router, prefix="/api/settings", tags=["settings"])
app.include_router(automod.router, prefix="/api/automod", tags=["automod"])
app.include_router(leveling.router, prefix="/api/leveling", tags=["leveling"])

@app.get("/")
async def root():
    return {"message": "ArabLife Bot Dashboard API"}

@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return {"detail": exc.detail}, exc.status_code

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
