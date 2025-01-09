from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional, Dict, Any
import discord

from ..database import get_db
from ..models import Guild, GuildSettings, Leveling, AutoMod
from ..schemas import (
    GuildResponse,
    GuildSettingsResponse,
    GuildUpdate
)
from ..auth import AuthManager
from ..models import User

router = APIRouter()

async def get_guild_stats(guild_id: str) -> Dict[str, Any]:
    """Get guild statistics from Discord API"""
    # This would typically use Discord's API to fetch real stats
    # For now, returning mock data
    return {
        "member_count": 150,
        "online_members": 45,
        "message_count_24h": 1250,
        "new_members_24h": 5,
        "voice_channels_active": 2,
        "total_channels": 15,
        "total_roles": 8,
        "bot_commands_used_24h": 324
    }

@router.get("/", response_model=List[GuildResponse])
async def list_guilds(
    current_user: User = Depends(AuthManager.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all guilds the user has access to"""
    # In a real implementation, you would filter based on user's Discord permissions
    result = await db.execute(select(Guild))
    guilds = result.scalars().all()
    return guilds

@router.get("/{guild_id}", response_model=GuildResponse)
async def get_guild(
    guild_id: int,
    current_user: User = Depends(AuthManager.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get detailed information about a specific guild"""
    result = await db.execute(select(Guild).filter(Guild.id == guild_id))
    guild = result.scalar_one_or_none()
    
    if not guild:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Guild not found"
        )
    
    return guild

@router.get("/{guild_id}/stats")
async def get_guild_statistics(
    guild_id: int,
    current_user: User = Depends(AuthManager.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get statistics for a guild"""
    result = await db.execute(select(Guild).filter(Guild.id == guild_id))
    guild = result.scalar_one_or_none()
    
    if not guild:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Guild not found"
        )
    
    try:
        stats = await get_guild_stats(guild.discord_id)
        
        # Get additional stats from database
        leveling_result = await db.execute(
            select(Leveling).filter(Leveling.guild_id == guild_id)
        )
        leveling_stats = leveling_result.scalars().all()
        
        automod_result = await db.execute(
            select(AutoMod).filter(AutoMod.guild_id == guild_id)
        )
        automod = automod_result.scalar_one_or_none()
        
        # Combine stats
        stats.update({
            "total_leveled_users": len(leveling_stats),
            "highest_level": max((user.level for user in leveling_stats), default=0),
            "automod_enabled": automod.is_enabled if automod else False,
            "automod_actions_24h": 15  # Mock data
        })
        
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch guild statistics: {str(e)}"
        )

@router.get("/{guild_id}/leaderboard")
async def get_guild_leaderboard(
    guild_id: int,
    limit: int = 10,
    current_user: User = Depends(AuthManager.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get guild leveling leaderboard"""
    result = await db.execute(
        select(Leveling)
        .filter(Leveling.guild_id == guild_id)
        .order_by(Leveling.level.desc(), Leveling.xp.desc())
        .limit(limit)
    )
    leaderboard = result.scalars().all()
    
    # Format leaderboard data
    return [
        {
            "user_id": entry.user_discord_id,
            "level": entry.level,
            "xp": entry.xp,
            "rank": idx + 1
        }
        for idx, entry in enumerate(leaderboard)
    ]

@router.get("/{guild_id}/audit-log")
async def get_guild_audit_log(
    guild_id: int,
    limit: int = 50,
    current_user: User = Depends(AuthManager.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get guild audit log"""
    # This would typically fetch from Discord's audit log API
    # For now, returning mock data
    return {
        "entries": [
            {
                "action": "MEMBER_BAN_ADD",
                "target": "user_id_123",
                "reason": "Spam",
                "executor": "mod_id_456",
                "timestamp": "2023-12-01T12:00:00Z"
            },
            {
                "action": "CHANNEL_CREATE",
                "target": "channel_id_789",
                "executor": "admin_id_012",
                "timestamp": "2023-12-01T11:30:00Z"
            }
        ]
    }

@router.get("/{guild_id}/activity")
async def get_guild_activity(
    guild_id: int,
    days: int = 7,
    current_user: User = Depends(AuthManager.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get guild activity statistics over time"""
    # This would typically aggregate data from your database
    # For now, returning mock data
    return {
        "message_activity": [
            {"date": "2023-12-01", "count": 1200},
            {"date": "2023-12-02", "count": 1500},
            {"date": "2023-12-03", "count": 1100}
        ],
        "member_growth": [
            {"date": "2023-12-01", "count": 100},
            {"date": "2023-12-02", "count": 105},
            {"date": "2023-12-03", "count": 110}
        ],
        "command_usage": [
            {"date": "2023-12-01", "count": 300},
            {"date": "2023-12-02", "count": 250},
            {"date": "2023-12-03", "count": 400}
        ]
    }

@router.get("/{guild_id}/insights")
async def get_guild_insights(
    guild_id: int,
    current_user: User = Depends(AuthManager.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get insights and recommendations for the guild"""
    # This would typically analyze guild data and provide recommendations
    # For now, returning mock data
    return {
        "activity_score": 8.5,
        "engagement_rate": "75%",
        "recommendations": [
            {
                "type": "FEATURE",
                "title": "Enable Welcome Messages",
                "description": "Increase member retention by enabling welcome messages",
                "priority": "HIGH"
            },
            {
                "type": "SECURITY",
                "title": "Configure AutoMod",
                "description": "Protect your server by setting up automod rules",
                "priority": "MEDIUM"
            }
        ],
        "top_channels": [
            {"name": "general", "messages_24h": 500},
            {"name": "gaming", "messages_24h": 300}
        ],
        "peak_hours": [
            {"hour": 18, "activity": "HIGH"},
            {"hour": 20, "activity": "HIGH"}
        ]
    }
