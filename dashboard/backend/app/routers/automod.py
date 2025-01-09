from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from ..database import get_db
from ..models import AutoMod, Guild
from ..schemas import AutoModSettings, Response
from ..auth import get_current_user

router = APIRouter()

@router.get("/{guild_id}", response_model=AutoModSettings)
async def get_automod_settings(
    guild_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get AutoMod settings for a guild"""
    # First check if guild exists
    guild_result = await db.execute(
        select(Guild).where(Guild.discord_id == guild_id)
    )
    guild = guild_result.scalar_one_or_none()
    if not guild:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Guild not found"
        )

    # Get AutoMod settings
    result = await db.execute(
        select(AutoMod).where(AutoMod.guild_id == guild.id)
    )
    settings = result.scalar_one_or_none()
    
    if not settings:
        # Create default settings if none exist
        settings = AutoMod(
            guild_id=guild.id,
            banned_words=[],
            banned_links=[],
            spam_threshold=5,
            spam_interval=5,
            raid_threshold=10,
            raid_interval=30,
            action_type="warn",
            is_enabled=True
        )
        db.add(settings)
        await db.commit()
        await db.refresh(settings)

    return AutoModSettings(
        is_enabled=settings.is_enabled,
        banned_words=settings.banned_words or [],
        banned_links=settings.banned_links or [],
        spam_threshold=settings.spam_threshold,
        spam_interval=settings.spam_interval,
        raid_threshold=settings.raid_threshold,
        raid_interval=settings.raid_interval,
        action_type=settings.action_type
    )

@router.patch("/{guild_id}", response_model=Response)
async def update_automod_settings(
    guild_id: str,
    settings: AutoModSettings,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update AutoMod settings for a guild"""
    # Check if guild exists
    guild_result = await db.execute(
        select(Guild).where(Guild.discord_id == guild_id)
    )
    guild = guild_result.scalar_one_or_none()
    if not guild:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Guild not found"
        )

    # Get existing settings
    result = await db.execute(
        select(AutoMod).where(AutoMod.guild_id == guild.id)
    )
    automod = result.scalar_one_or_none()
    
    if not automod:
        automod = AutoMod(guild_id=guild.id)
        db.add(automod)

    # Update settings
    automod.is_enabled = settings.is_enabled
    automod.banned_words = settings.banned_words
    automod.banned_links = settings.banned_links
    automod.spam_threshold = settings.spam_threshold
    automod.spam_interval = settings.spam_interval
    automod.raid_threshold = settings.raid_threshold
    automod.raid_interval = settings.raid_interval
    automod.action_type = settings.action_type

    await db.commit()
    await db.refresh(automod)

    return Response(
        success=True,
        message="AutoMod settings updated successfully",
        data=settings.dict()
    )
