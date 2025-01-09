from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional
import discord

from ..database import get_db
from ..models import Guild, GuildSettings, RoleMenu
from ..schemas import (
    GuildSettingsResponse, GuildSettingsUpdate,
    RoleMenu as RoleMenuSchema,
    RoleMenuResponse
)
from ..auth import AuthManager
from ..models import User

router = APIRouter()

async def get_discord_roles(guild_id: str) -> List[dict]:
    """Get roles from Discord API"""
    # This would typically use Discord's API to fetch roles
    # For now, returning mock data
    return [
        {"id": "123", "name": "Admin", "color": 0xFF0000},
        {"id": "456", "name": "Moderator", "color": 0x00FF00},
        {"id": "789", "name": "Member", "color": 0x0000FF}
    ]

@router.get("/roles/{guild_id}")
async def get_guild_roles(
    guild_id: int,
    current_user: User = Depends(AuthManager.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all roles in the guild"""
    result = await db.execute(select(Guild).filter(Guild.id == guild_id))
    guild = result.scalar_one_or_none()
    
    if not guild:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Guild not found"
        )
    
    try:
        roles = await get_discord_roles(guild.discord_id)
        return {"roles": roles}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch roles: {str(e)}"
        )

@router.get("/role-menus/{guild_id}", response_model=List[RoleMenuResponse])
async def get_role_menus(
    guild_id: int,
    current_user: User = Depends(AuthManager.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all role menus in the guild"""
    result = await db.execute(
        select(RoleMenu).filter(RoleMenu.guild_id == guild_id)
    )
    menus = result.scalars().all()
    return menus

@router.post("/role-menus/{guild_id}", response_model=RoleMenuResponse)
async def create_role_menu(
    guild_id: int,
    menu: RoleMenuSchema,
    current_user: User = Depends(AuthManager.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new role menu"""
    # Verify guild exists
    result = await db.execute(select(Guild).filter(Guild.id == guild_id))
    guild = result.scalar_one_or_none()
    
    if not guild:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Guild not found"
        )
    
    # Create role menu
    new_menu = RoleMenu(
        guild_id=guild_id,
        channel_id=menu.channel_id,
        title=menu.title,
        description=menu.description,
        roles=menu.roles
    )
    
    db.add(new_menu)
    await db.commit()
    await db.refresh(new_menu)
    
    # Here you would typically create the actual message in Discord
    # and update the message_id in the database
    
    return new_menu

@router.patch("/role-menus/{menu_id}", response_model=RoleMenuResponse)
async def update_role_menu(
    menu_id: int,
    menu_update: RoleMenuSchema,
    current_user: User = Depends(AuthManager.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a role menu"""
    result = await db.execute(
        select(RoleMenu).filter(RoleMenu.id == menu_id)
    )
    menu = result.scalar_one_or_none()
    
    if not menu:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role menu not found"
        )
    
    # Update menu with new values
    for field, value in menu_update.dict(exclude_unset=True).items():
        setattr(menu, field, value)
    
    await db.commit()
    await db.refresh(menu)
    
    # Here you would typically update the message in Discord
    
    return menu

@router.delete("/role-menus/{menu_id}")
async def delete_role_menu(
    menu_id: int,
    current_user: User = Depends(AuthManager.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a role menu"""
    result = await db.execute(
        select(RoleMenu).filter(RoleMenu.id == menu_id)
    )
    menu = result.scalar_one_or_none()
    
    if not menu:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role menu not found"
        )
    
    # Here you would typically delete the message in Discord
    
    await db.delete(menu)
    await db.commit()
    
    return {"status": "success", "message": "Role menu deleted"}

@router.get("/channels/{guild_id}")
async def get_guild_channels(
    guild_id: int,
    current_user: User = Depends(AuthManager.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all channels in the guild"""
    result = await db.execute(select(Guild).filter(Guild.id == guild_id))
    guild = result.scalar_one_or_none()
    
    if not guild:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Guild not found"
        )
    
    try:
        # This would typically use Discord's API to fetch channels
        # For now, returning mock data
        channels = [
            {"id": "123", "name": "general", "type": "text"},
            {"id": "456", "name": "voice", "type": "voice"},
            {"id": "789", "name": "announcements", "type": "text"}
        ]
        return {"channels": channels}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch channels: {str(e)}"
        )

@router.get("/permissions/{guild_id}")
async def get_role_permissions(
    guild_id: int,
    role_id: str = Query(..., description="Discord role ID"),
    current_user: User = Depends(AuthManager.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get permissions for a specific role"""
    result = await db.execute(select(Guild).filter(Guild.id == guild_id))
    guild = result.scalar_one_or_none()
    
    if not guild:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Guild not found"
        )
    
    try:
        # This would typically use Discord's API to fetch role permissions
        # For now, returning mock data
        permissions = {
            "administrator": False,
            "manage_guild": True,
            "manage_roles": True,
            "manage_channels": True,
            "kick_members": True,
            "ban_members": False
        }
        return {"permissions": permissions}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch permissions: {str(e)}"
        )
