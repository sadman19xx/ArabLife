from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional
import discord

from ..database import get_db
from ..models import Guild, CustomCommand
from ..schemas import (
    CustomCommandCreate,
    CustomCommandUpdate,
    CustomCommandResponse
)
from ..auth import AuthManager
from ..models import User

router = APIRouter()

@router.get("/{guild_id}", response_model=List[CustomCommandResponse])
async def list_commands(
    guild_id: int,
    current_user: User = Depends(AuthManager.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all custom commands for a guild"""
    result = await db.execute(
        select(CustomCommand).filter(CustomCommand.guild_id == guild_id)
    )
    commands = result.scalars().all()
    return commands

@router.post("/{guild_id}", response_model=CustomCommandResponse)
async def create_command(
    guild_id: int,
    command: CustomCommandCreate,
    current_user: User = Depends(AuthManager.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new custom command"""
    # Check if command name already exists
    result = await db.execute(
        select(CustomCommand).filter(
            CustomCommand.guild_id == guild_id,
            CustomCommand.name == command.name
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Command name already exists"
        )

    # Validate command name format
    if not command.name.isalnum() or len(command.name) > 32:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Command name must be alphanumeric and max 32 characters"
        )

    new_command = CustomCommand(
        guild_id=guild_id,
        name=command.name,
        response=command.response,
        description=command.description,
        required_role_id=command.required_role_id,
        cooldown=command.cooldown
    )
    
    db.add(new_command)
    await db.commit()
    await db.refresh(new_command)
    return new_command

@router.get("/{guild_id}/{command_id}", response_model=CustomCommandResponse)
async def get_command(
    guild_id: int,
    command_id: int,
    current_user: User = Depends(AuthManager.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific custom command"""
    result = await db.execute(
        select(CustomCommand).filter(
            CustomCommand.guild_id == guild_id,
            CustomCommand.id == command_id
        )
    )
    command = result.scalar_one_or_none()
    
    if not command:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Command not found"
        )
    
    return command

@router.patch("/{guild_id}/{command_id}", response_model=CustomCommandResponse)
async def update_command(
    guild_id: int,
    command_id: int,
    command_update: CustomCommandUpdate,
    current_user: User = Depends(AuthManager.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a custom command"""
    result = await db.execute(
        select(CustomCommand).filter(
            CustomCommand.guild_id == guild_id,
            CustomCommand.id == command_id
        )
    )
    command = result.scalar_one_or_none()
    
    if not command:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Command not found"
        )

    # Check if new name conflicts with existing commands
    if command_update.name and command_update.name != command.name:
        result = await db.execute(
            select(CustomCommand).filter(
                CustomCommand.guild_id == guild_id,
                CustomCommand.name == command_update.name
            )
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Command name already exists"
            )

    # Update command with new values
    for field, value in command_update.dict(exclude_unset=True).items():
        setattr(command, field, value)
    
    await db.commit()
    await db.refresh(command)
    return command

@router.delete("/{guild_id}/{command_id}")
async def delete_command(
    guild_id: int,
    command_id: int,
    current_user: User = Depends(AuthManager.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a custom command"""
    result = await db.execute(
        select(CustomCommand).filter(
            CustomCommand.guild_id == guild_id,
            CustomCommand.id == command_id
        )
    )
    command = result.scalar_one_or_none()
    
    if not command:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Command not found"
        )
    
    await db.delete(command)
    await db.commit()
    
    return {"status": "success", "message": "Command deleted"}

@router.post("/{guild_id}/{command_id}/toggle")
async def toggle_command(
    guild_id: int,
    command_id: int,
    current_user: User = Depends(AuthManager.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Toggle a command's enabled status"""
    result = await db.execute(
        select(CustomCommand).filter(
            CustomCommand.guild_id == guild_id,
            CustomCommand.id == command_id
        )
    )
    command = result.scalar_one_or_none()
    
    if not command:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Command not found"
        )
    
    command.is_enabled = not command.is_enabled
    await db.commit()
    
    return {
        "status": "success",
        "message": f"Command {'enabled' if command.is_enabled else 'disabled'}",
        "is_enabled": command.is_enabled
    }

@router.get("/{guild_id}/search")
async def search_commands(
    guild_id: int,
    query: str = Query(..., min_length=1),
    current_user: User = Depends(AuthManager.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Search for commands by name or description"""
    result = await db.execute(
        select(CustomCommand).filter(
            CustomCommand.guild_id == guild_id,
            (CustomCommand.name.ilike(f"%{query}%") |
             CustomCommand.description.ilike(f"%{query}%"))
        )
    )
    commands = result.scalars().all()
    return commands
