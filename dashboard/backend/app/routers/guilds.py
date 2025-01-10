from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict
import httpx
from ..database import get_db
from ..auth import get_current_active_user, verify_guild_permissions, get_bot_token
from ..models import Guild as GuildModel
from ..schemas import (
    Guild,
    GuildCreate,
    GuildUpdate,
    GuildResponse,
    GuildListResponse,
    ErrorResponse
)

router = APIRouter(
    prefix="/api/guilds",
    tags=["guilds"],
    responses={401: {"model": ErrorResponse}}
)

@router.get("", response_model=GuildListResponse)
async def get_user_guilds(
    current_user: Dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all guilds available to the current user."""
    try:
        # Get guilds from Discord API using bot token
        bot_token = get_bot_token()
        headers = {
            "Authorization": f"Bot {bot_token}"
        }

        # Filter guilds where user has manage server permission
        user_guilds = current_user.get("guilds", [])
        managed_guilds = [
            guild for guild in user_guilds
            if (int(guild["permissions"]) & 0x20) == 0x20  # MANAGE_GUILD permission
        ]

        # Get detailed guild information for each managed guild
        guilds = []
        async with httpx.AsyncClient() as client:
            for guild in managed_guilds:
                guild_url = f"https://discord.com/api/v10/guilds/{guild['id']}"
                response = await client.get(guild_url, headers=headers)
                
                if response.status_code == 200:
                    guild_data = response.json()
                    guilds.append(Guild(
                        id=guild_data["id"],
                        name=guild_data["name"],
                        icon_url=f"https://cdn.discordapp.com/icons/{guild_data['id']}/{guild_data['icon']}.png" if guild_data.get("icon") else None,
                        owner_id=guild_data["owner_id"],
                        member_count=guild_data["approximate_member_count"] if "approximate_member_count" in guild_data else 0,
                        settings={}
                    ))

        return GuildListResponse(guilds=guilds)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/{guild_id}", response_model=GuildResponse)
async def get_guild(
    guild_id: str,
    current_user: Dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get detailed information about a specific guild."""
    try:
        # Verify user has access to this guild
        await verify_guild_permissions(guild_id, current_user)

        # Get guild data from Discord API
        bot_token = get_bot_token()
        headers = {
            "Authorization": f"Bot {bot_token}"
        }

        async with httpx.AsyncClient() as client:
            # Get guild information
            guild_url = f"https://discord.com/api/v10/guilds/{guild_id}"
            guild_response = await client.get(guild_url, headers=headers)

            if guild_response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Guild not found"
                )

            guild_data = guild_response.json()

            # Get roles
            roles_url = f"https://discord.com/api/v10/guilds/{guild_id}/roles"
            roles_response = await client.get(roles_url, headers=headers)
            roles_data = roles_response.json() if roles_response.status_code == 200 else []

            # Get channels
            channels_url = f"https://discord.com/api/v10/guilds/{guild_id}/channels"
            channels_response = await client.get(channels_url, headers=headers)
            channels_data = channels_response.json() if channels_response.status_code == 200 else []

            # Get bot settings from database
            # TODO: Implement database query for bot settings

            return GuildResponse(
                guild=Guild(
                    id=guild_data["id"],
                    name=guild_data["name"],
                    icon_url=f"https://cdn.discordapp.com/icons/{guild_data['id']}/{guild_data['icon']}.png" if guild_data.get("icon") else None,
                    owner_id=guild_data["owner_id"],
                    member_count=guild_data["approximate_member_count"] if "approximate_member_count" in guild_data else 0,
                    settings={}
                ),
                roles=[{
                    "id": role["id"],
                    "name": role["name"],
                    "color": role["color"],
                    "position": role["position"],
                    "permissions": str(role["permissions"])
                } for role in roles_data],
                channels=[{
                    "id": channel["id"],
                    "name": channel["name"],
                    "type": str(channel["type"]),
                    "position": channel["position"],
                    "settings": {}
                } for channel in channels_data],
                settings=None  # TODO: Add bot settings from database
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
