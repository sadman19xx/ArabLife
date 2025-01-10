from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, List
import httpx
from ..database import get_db
from ..auth import get_current_active_user, verify_guild_permissions, get_bot_token
from ..schemas import ErrorResponse

router = APIRouter(
    prefix="/api/commands",
    tags=["commands"],
    responses={401: {"model": ErrorResponse}}
)

@router.get("/{guild_id}")
async def get_guild_commands(
    guild_id: str,
    current_user: Dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all commands available in a guild."""
    try:
        # Verify user has access to this guild
        await verify_guild_permissions(guild_id, current_user)

        # Get bot token
        bot_token = get_bot_token()
        headers = {
            "Authorization": f"Bot {bot_token}"
        }

        # Get application ID from bot token
        async with httpx.AsyncClient() as client:
            me_response = await client.get(
                "https://discord.com/api/v10/users/@me",
                headers=headers
            )
            if me_response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to get bot information"
                )
            
            application_id = me_response.json()["id"]

            # Get guild commands
            commands_url = f"https://discord.com/api/v10/applications/{application_id}/guilds/{guild_id}/commands"
            commands_response = await client.get(commands_url, headers=headers)

            if commands_response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to get guild commands"
                )

            commands = commands_response.json()

            # Format commands for response
            formatted_commands = []
            for cmd in commands:
                formatted_cmd = {
                    "id": cmd["id"],
                    "name": cmd["name"],
                    "description": cmd["description"],
                    "options": cmd.get("options", []),
                    "default_member_permissions": cmd.get("default_member_permissions"),
                    "type": cmd.get("type", 1)  # 1 is CHAT_INPUT
                }
                formatted_commands.append(formatted_cmd)

            return formatted_commands

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.put("/{guild_id}/{command_id}/permissions")
async def update_command_permissions(
    guild_id: str,
    command_id: str,
    permissions: List[Dict],
    current_user: Dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update permissions for a specific command in a guild."""
    try:
        # Verify user has access to this guild
        await verify_guild_permissions(guild_id, current_user)

        # Get bot token
        bot_token = get_bot_token()
        headers = {
            "Authorization": f"Bot {bot_token}"
        }

        # Get application ID from bot token
        async with httpx.AsyncClient() as client:
            me_response = await client.get(
                "https://discord.com/api/v10/users/@me",
                headers=headers
            )
            if me_response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to get bot information"
                )
            
            application_id = me_response.json()["id"]

            # Update command permissions
            permissions_url = f"https://discord.com/api/v10/applications/{application_id}/guilds/{guild_id}/commands/{command_id}/permissions"
            permissions_response = await client.put(
                permissions_url,
                headers=headers,
                json={"permissions": permissions}
            )

            if permissions_response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update command permissions"
                )

            return permissions_response.json()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/{guild_id}/sync")
async def sync_commands(
    guild_id: str,
    current_user: Dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Sync all commands to a guild."""
    try:
        # Verify user has access to this guild
        await verify_guild_permissions(guild_id, current_user)

        # Get bot token
        bot_token = get_bot_token()
        headers = {
            "Authorization": f"Bot {bot_token}"
        }

        # Get application ID from bot token
        async with httpx.AsyncClient() as client:
            me_response = await client.get(
                "https://discord.com/api/v10/users/@me",
                headers=headers
            )
            if me_response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to get bot information"
                )
            
            application_id = me_response.json()["id"]

            # TODO: Get commands from bot's command registry
            # This will be implemented when integrating with the Discord bot
            commands_to_sync = []

            # Sync commands to guild
            sync_url = f"https://discord.com/api/v10/applications/{application_id}/guilds/{guild_id}/commands"
            sync_response = await client.put(
                sync_url,
                headers=headers,
                json=commands_to_sync
            )

            if sync_response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to sync commands"
                )

            return {"message": "Commands synced successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
