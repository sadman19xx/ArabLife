from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Dict, Optional
from ..database import get_db
from ..auth import get_current_active_user, verify_guild_permissions
from ..models import BotSettings as BotSettingsModel
from ..schemas import (
    BotSettings,
    BotSettingsCreate,
    BotSettingsUpdate,
    ErrorResponse
)

router = APIRouter(
    prefix="/api/settings",
    tags=["settings"],
    responses={401: {"model": ErrorResponse}}
)

@router.get("/{guild_id}", response_model=BotSettings)
async def get_guild_settings(
    guild_id: str,
    current_user: Dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get bot settings for a specific guild."""
    try:
        # Verify user has access to this guild
        await verify_guild_permissions(guild_id, current_user)

        # Get settings from database
        query = select(BotSettingsModel).where(BotSettingsModel.guild_id == guild_id)
        result = await db.execute(query)
        settings = result.scalar_one_or_none()

        if not settings:
            # Create default settings if none exist
            settings = BotSettingsModel(
                guild_id=guild_id,
                welcome_channel_id=None,
                welcome_message=None,
                role_channel_id=None,
                log_channel_id=None,
                ticket_category_id=None,
                automod_enabled=False,
                leveling_enabled=False
            )
            db.add(settings)
            await db.commit()
            await db.refresh(settings)

        return settings

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.put("/{guild_id}", response_model=BotSettings)
async def update_guild_settings(
    guild_id: str,
    settings_update: BotSettingsUpdate,
    current_user: Dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update bot settings for a specific guild."""
    try:
        # Verify user has access to this guild
        await verify_guild_permissions(guild_id, current_user)

        # Get existing settings
        query = select(BotSettingsModel).where(BotSettingsModel.guild_id == guild_id)
        result = await db.execute(query)
        settings = result.scalar_one_or_none()

        if not settings:
            # Create new settings if none exist
            settings = BotSettingsModel(guild_id=guild_id)
            db.add(settings)

        # Update settings with new values
        for key, value in settings_update.dict(exclude_unset=True).items():
            setattr(settings, key, value)

        await db.commit()
        await db.refresh(settings)

        return settings

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/{guild_id}/welcome-message")
async def test_welcome_message(
    guild_id: str,
    current_user: Dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Test the welcome message in the configured channel."""
    try:
        # Verify user has access to this guild
        await verify_guild_permissions(guild_id, current_user)

        # Get settings
        query = select(BotSettingsModel).where(BotSettingsModel.guild_id == guild_id)
        result = await db.execute(query)
        settings = result.scalar_one_or_none()

        if not settings or not settings.welcome_channel_id or not settings.welcome_message:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Welcome message or channel not configured"
            )

        # TODO: Send test welcome message using bot
        # This will be implemented when integrating with the Discord bot

        return {"message": "Test welcome message sent"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/{guild_id}/verify-channels")
async def verify_channel_settings(
    guild_id: str,
    current_user: Dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Verify that all configured channels exist and are accessible."""
    try:
        # Verify user has access to this guild
        await verify_guild_permissions(guild_id, current_user)

        # Get settings
        query = select(BotSettingsModel).where(BotSettingsModel.guild_id == guild_id)
        result = await db.execute(query)
        settings = result.scalar_one_or_none()

        if not settings:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Settings not found"
            )

        # TODO: Verify channel access using bot
        # This will be implemented when integrating with the Discord bot

        return {
            "welcome_channel": True if settings.welcome_channel_id else None,
            "role_channel": True if settings.role_channel_id else None,
            "log_channel": True if settings.log_channel_id else None,
            "ticket_category": True if settings.ticket_category_id else None
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
