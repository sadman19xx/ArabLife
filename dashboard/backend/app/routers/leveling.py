from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Dict, List
from ..database import get_db
from ..auth import get_current_active_user, verify_guild_permissions
from ..models import (
    LevelingSettings as LevelingSettingsModel,
    UserLevel as UserLevelModel
)
from ..schemas import (
    LevelingSettings,
    LevelingSettingsCreate,
    LevelingSettingsUpdate,
    UserLevel,
    ErrorResponse
)

router = APIRouter(
    prefix="/api/leveling",
    tags=["leveling"],
    responses={401: {"model": ErrorResponse}}
)

@router.get("/{guild_id}/settings", response_model=LevelingSettings)
async def get_leveling_settings(
    guild_id: str,
    current_user: Dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get leveling settings for a guild."""
    try:
        # Verify user has access to this guild
        await verify_guild_permissions(guild_id, current_user)

        # Get settings from database
        query = select(LevelingSettingsModel).where(LevelingSettingsModel.guild_id == guild_id)
        result = await db.execute(query)
        settings = result.scalar_one_or_none()

        if not settings:
            # Create default settings if none exist
            settings = LevelingSettingsModel(
                guild_id=guild_id,
                xp_per_message=1,
                xp_cooldown=60,
                level_up_channel_id=None,
                level_up_message=None,
                role_rewards={}
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

@router.put("/{guild_id}/settings", response_model=LevelingSettings)
async def update_leveling_settings(
    guild_id: str,
    settings_update: LevelingSettingsUpdate,
    current_user: Dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update leveling settings for a guild."""
    try:
        # Verify user has access to this guild
        await verify_guild_permissions(guild_id, current_user)

        # Get existing settings
        query = select(LevelingSettingsModel).where(LevelingSettingsModel.guild_id == guild_id)
        result = await db.execute(query)
        settings = result.scalar_one_or_none()

        if not settings:
            # Create new settings if none exist
            settings = LevelingSettingsModel(guild_id=guild_id)
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

@router.get("/{guild_id}/leaderboard")
async def get_guild_leaderboard(
    guild_id: str,
    limit: int = 10,
    offset: int = 0,
    current_user: Dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get the XP leaderboard for a guild."""
    try:
        # Verify user has access to this guild
        await verify_guild_permissions(guild_id, current_user)

        # Get user levels from database
        query = (
            select(UserLevelModel)
            .where(UserLevelModel.guild_id == guild_id)
            .order_by(UserLevelModel.xp.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await db.execute(query)
        users = result.scalars().all()

        # Get total count for pagination
        count_query = (
            select(UserLevelModel)
            .where(UserLevelModel.guild_id == guild_id)
        )
        count_result = await db.execute(count_query)
        total_users = len(count_result.scalars().all())

        return {
            "users": users,
            "total": total_users,
            "offset": offset,
            "limit": limit
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/{guild_id}/users/{user_id}", response_model=UserLevel)
async def get_user_level(
    guild_id: str,
    user_id: str,
    current_user: Dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get level information for a specific user."""
    try:
        # Verify user has access to this guild
        await verify_guild_permissions(guild_id, current_user)

        # Get user level from database
        query = select(UserLevelModel).where(
            UserLevelModel.guild_id == guild_id,
            UserLevelModel.user_id == user_id
        )
        result = await db.execute(query)
        user_level = result.scalar_one_or_none()

        if not user_level:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        return user_level

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/{guild_id}/reset")
async def reset_guild_levels(
    guild_id: str,
    current_user: Dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Reset all levels and XP in a guild."""
    try:
        # Verify user has access to this guild
        await verify_guild_permissions(guild_id, current_user)

        # Delete all user levels for the guild
        query = select(UserLevelModel).where(UserLevelModel.guild_id == guild_id)
        result = await db.execute(query)
        users = result.scalars().all()

        for user in users:
            await db.delete(user)

        await db.commit()

        return {"message": "All levels have been reset"}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
