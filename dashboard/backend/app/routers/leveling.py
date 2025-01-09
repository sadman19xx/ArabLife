from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List
from ..database import get_db
from ..models import Leveling, Guild, GuildSettings
from ..schemas import LevelingSettings, LeaderboardEntry, Response, RoleReward
from ..auth import get_current_user

router = APIRouter()

@router.get("/{guild_id}/settings", response_model=LevelingSettings)
async def get_leveling_settings(
    guild_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get leveling settings for a guild"""
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

    # Get guild settings
    settings_result = await db.execute(
        select(GuildSettings).where(GuildSettings.guild_id == guild.id)
    )
    settings = settings_result.scalar_one_or_none()
    
    if not settings:
        settings = GuildSettings(
            guild_id=guild.id,
            level_up_channel_id=None,
            custom_settings={
                "leveling": {
                    "is_enabled": True,
                    "xp_per_message": 15,
                    "xp_cooldown": 60,
                    "level_up_message": "Congratulations {user}! You reached level {level}!",
                    "role_rewards": []
                }
            }
        )
        db.add(settings)
        await db.commit()
        await db.refresh(settings)

    leveling_settings = settings.custom_settings.get("leveling", {})
    return LevelingSettings(
        is_enabled=leveling_settings.get("is_enabled", True),
        xp_per_message=leveling_settings.get("xp_per_message", 15),
        xp_cooldown=leveling_settings.get("xp_cooldown", 60),
        level_up_channel_id=settings.level_up_channel_id,
        level_up_message=leveling_settings.get("level_up_message", "Congratulations {user}! You reached level {level}!"),
        role_rewards=leveling_settings.get("role_rewards", [])
    )

@router.patch("/{guild_id}/settings", response_model=Response)
async def update_leveling_settings(
    guild_id: str,
    settings: LevelingSettings,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update leveling settings for a guild"""
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

    # Get guild settings
    settings_result = await db.execute(
        select(GuildSettings).where(GuildSettings.guild_id == guild.id)
    )
    guild_settings = settings_result.scalar_one_or_none()
    
    if not guild_settings:
        guild_settings = GuildSettings(guild_id=guild.id)
        db.add(guild_settings)

    # Update settings
    if not guild_settings.custom_settings:
        guild_settings.custom_settings = {}
    
    guild_settings.level_up_channel_id = settings.level_up_channel_id
    guild_settings.custom_settings["leveling"] = {
        "is_enabled": settings.is_enabled,
        "xp_per_message": settings.xp_per_message,
        "xp_cooldown": settings.xp_cooldown,
        "level_up_message": settings.level_up_message,
        "role_rewards": [reward.dict() for reward in settings.role_rewards]
    }

    await db.commit()
    await db.refresh(guild_settings)

    return Response(
        success=True,
        message="Leveling settings updated successfully",
        data=settings.dict()
    )

@router.get("/{guild_id}/leaderboard", response_model=List[LeaderboardEntry])
async def get_leaderboard(
    guild_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get the XP leaderboard for a guild"""
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

    # Get leaderboard
    result = await db.execute(
        select(Leveling)
        .where(Leveling.guild_id == guild.id)
        .order_by(Leveling.xp.desc())
        .limit(10)
    )
    entries = result.scalars().all()

    # Format leaderboard entries
    leaderboard = []
    for rank, entry in enumerate(entries, 1):
        leaderboard.append(
            LeaderboardEntry(
                user_discord_id=entry.user_discord_id,
                username=entry.user_discord_id,  # This would be replaced with actual username in production
                level=entry.level,
                xp=entry.xp,
                rank=rank
            )
        )

    return leaderboard

@router.get("/{guild_id}/user/{user_id}", response_model=LeaderboardEntry)
async def get_user_level(
    guild_id: str,
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get level information for a specific user"""
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

    # Get user's level info
    result = await db.execute(
        select(Leveling)
        .where(Leveling.guild_id == guild.id)
        .where(Leveling.user_discord_id == user_id)
    )
    user_level = result.scalar_one_or_none()
    
    if not user_level:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found in leveling system"
        )

    # Get user's rank
    rank_result = await db.execute(
        select(func.count())
        .select_from(Leveling)
        .where(Leveling.guild_id == guild.id)
        .where(Leveling.xp > user_level.xp)
    )
    rank = rank_result.scalar() + 1

    return LeaderboardEntry(
        user_discord_id=user_level.user_discord_id,
        username=user_level.user_discord_id,  # This would be replaced with actual username in production
        level=user_level.level,
        xp=user_level.xp,
        rank=rank
    )
