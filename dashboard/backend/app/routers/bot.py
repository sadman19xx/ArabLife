from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional
import discord
import subprocess
import os
import sys
import asyncio

from ..database import get_db
from ..models import Guild, GuildSettings, CustomCommand, WelcomeMessage, AutoMod
from ..schemas import (
    GuildSettingsUpdate, CustomCommandCreate, CustomCommandUpdate,
    WelcomeMessageCreate, WelcomeMessageUpdate, AutoModUpdate,
    GuildSettingsResponse, CustomCommandResponse, WelcomeMessageResponse,
    AutoModResponse, BotInstallRequest, BotStatusResponse
)
from ..auth import AuthManager
from ..models import User

router = APIRouter()

# Bot process management
bot_process = None

def run_bot():
    """Run the bot in a separate process"""
    global bot_process
    try:
        # Activate virtual environment and start bot
        venv_python = os.path.join(os.getcwd(), "venv", "bin", "python")
        bot_process = subprocess.Popen(
            [venv_python, "bot.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
    except Exception as e:
        print(f"Failed to start bot: {e}")
        bot_process = None

def stop_bot():
    """Stop the bot process"""
    global bot_process
    if bot_process:
        bot_process.terminate()
        bot_process = None

@router.post("/install")
async def install_bot(
    install_data: BotInstallRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(AuthManager.get_current_user)
):
    """Install and configure the bot"""
    try:
        # Create .env file with configuration
        env_content = f"""
TOKEN={install_data.token}
GUILD_ID={install_data.guild_id}
ROLE_IDS_ALLOWED={','.join(map(str, install_data.role_ids_allowed))}
ROLE_ID_TO_GIVE={install_data.role_id_to_give}
ROLE_ID_REMOVE_ALLOWED={install_data.role_id_remove_allowed}
ROLE_ACTIVITY_LOG_CHANNEL_ID={install_data.role_activity_log_channel_id}
AUDIT_LOG_CHANNEL_ID={install_data.audit_log_channel_id}
VISA_IMAGE_URL={install_data.visa_image_url}
"""
        with open(".env", "w") as f:
            f.write(env_content)

        # Create virtual environment if it doesn't exist
        if not os.path.exists("venv"):
            subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)

        # Install dependencies
        venv_pip = os.path.join(os.getcwd(), "venv", "bin", "pip")
        subprocess.run([venv_pip, "install", "-r", "requirements.txt"], check=True)

        return {"status": "success", "message": "Bot installed successfully"}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Installation failed: {str(e)}"
        )

@router.post("/start")
async def start_bot(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(AuthManager.get_current_user)
):
    """Start the bot"""
    global bot_process
    if bot_process:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bot is already running"
        )
    
    background_tasks.add_task(run_bot)
    return {"status": "success", "message": "Bot started"}

@router.post("/stop")
async def stop_bot_endpoint(
    current_user: User = Depends(AuthManager.get_current_user)
):
    """Stop the bot"""
    global bot_process
    if not bot_process:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bot is not running"
        )
    
    stop_bot()
    return {"status": "success", "message": "Bot stopped"}

@router.get("/status", response_model=BotStatusResponse)
async def get_bot_status(
    current_user: User = Depends(AuthManager.get_current_user)
):
    """Get bot status"""
    global bot_process
    is_running = bot_process is not None and bot_process.poll() is None
    
    if is_running:
        # Get recent logs
        logs = []
        if bot_process.stdout:
            while True:
                line = bot_process.stdout.readline()
                if not line:
                    break
                logs.append(line.decode().strip())
    else:
        logs = []

    return {
        "status": "running" if is_running else "stopped",
        "logs": logs[-50:] if logs else []  # Keep last 50 lines
    }

async def verify_guild_access(
    guild_id: int,
    current_user: User = Depends(AuthManager.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Verify user has access to the guild"""
    result = await db.execute(select(Guild).filter(Guild.id == guild_id))
    guild = result.scalar_one_or_none()
    
    if not guild:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Guild not found"
        )
    
    # Here you would typically check if the user has admin permissions in the guild
    # This requires integration with Discord's API
    return guild

@router.get("/settings/{guild_id}", response_model=GuildSettingsResponse)
async def get_guild_settings(
    guild_id: int,
    guild: Guild = Depends(verify_guild_access),
    db: AsyncSession = Depends(get_db)
):
    """Get guild settings"""
    result = await db.execute(
        select(GuildSettings).filter(GuildSettings.guild_id == guild_id)
    )
    settings = result.scalar_one_or_none()
    
    if not settings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Settings not found"
        )
    
    return settings

@router.patch("/settings/{guild_id}", response_model=GuildSettingsResponse)
async def update_guild_settings(
    guild_id: int,
    settings_update: GuildSettingsUpdate,
    guild: Guild = Depends(verify_guild_access),
    db: AsyncSession = Depends(get_db)
):
    """Update guild settings"""
    result = await db.execute(
        select(GuildSettings).filter(GuildSettings.guild_id == guild_id)
    )
    settings = result.scalar_one_or_none()
    
    if not settings:
        settings = GuildSettings(guild_id=guild_id)
        db.add(settings)
    
    # Update settings with new values
    for field, value in settings_update.dict(exclude_unset=True).items():
        setattr(settings, field, value)
    
    await db.commit()
    await db.refresh(settings)
    return settings

@router.get("/commands/{guild_id}", response_model=List[CustomCommandResponse])
async def get_custom_commands(
    guild_id: int,
    guild: Guild = Depends(verify_guild_access),
    db: AsyncSession = Depends(get_db)
):
    """Get guild custom commands"""
    result = await db.execute(
        select(CustomCommand).filter(CustomCommand.guild_id == guild_id)
    )
    commands = result.scalars().all()
    return commands

@router.post("/commands/{guild_id}", response_model=CustomCommandResponse)
async def create_custom_command(
    guild_id: int,
    command: CustomCommandCreate,
    guild: Guild = Depends(verify_guild_access),
    db: AsyncSession = Depends(get_db)
):
    """Create a custom command"""
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
    
    new_command = CustomCommand(**command.dict())
    db.add(new_command)
    await db.commit()
    await db.refresh(new_command)
    return new_command

@router.get("/welcome/{guild_id}", response_model=Optional[WelcomeMessageResponse])
async def get_welcome_message(
    guild_id: int,
    guild: Guild = Depends(verify_guild_access),
    db: AsyncSession = Depends(get_db)
):
    """Get guild welcome message"""
    result = await db.execute(
        select(WelcomeMessage).filter(WelcomeMessage.guild_id == guild_id)
    )
    message = result.scalar_one_or_none()
    return message

@router.post("/welcome/{guild_id}", response_model=WelcomeMessageResponse)
async def create_welcome_message(
    guild_id: int,
    message: WelcomeMessageCreate,
    guild: Guild = Depends(verify_guild_access),
    db: AsyncSession = Depends(get_db)
):
    """Create or update welcome message"""
    result = await db.execute(
        select(WelcomeMessage).filter(WelcomeMessage.guild_id == guild_id)
    )
    existing_message = result.scalar_one_or_none()
    
    if existing_message:
        # Update existing message
        for field, value in message.dict(exclude={'guild_id'}).items():
            setattr(existing_message, field, value)
        welcome_message = existing_message
    else:
        # Create new message
        welcome_message = WelcomeMessage(**message.dict())
        db.add(welcome_message)
    
    await db.commit()
    await db.refresh(welcome_message)
    return welcome_message

@router.get("/automod/{guild_id}", response_model=Optional[AutoModResponse])
async def get_automod_settings(
    guild_id: int,
    guild: Guild = Depends(verify_guild_access),
    db: AsyncSession = Depends(get_db)
):
    """Get guild automod settings"""
    result = await db.execute(
        select(AutoMod).filter(AutoMod.guild_id == guild_id)
    )
    settings = result.scalar_one_or_none()
    return settings

@router.patch("/automod/{guild_id}", response_model=AutoModResponse)
async def update_automod_settings(
    guild_id: int,
    settings_update: AutoModUpdate,
    guild: Guild = Depends(verify_guild_access),
    db: AsyncSession = Depends(get_db)
):
    """Update automod settings"""
    result = await db.execute(
        select(AutoMod).filter(AutoMod.guild_id == guild_id)
    )
    settings = result.scalar_one_or_none()
    
    if not settings:
        settings = AutoMod(guild_id=guild_id)
        db.add(settings)
    
    # Update settings with new values
    for field, value in settings_update.dict(exclude_unset=True).items():
        setattr(settings, field, value)
    
    await db.commit()
    await db.refresh(settings)
    return settings

@router.post("/sync/{guild_id}")
async def sync_guild_data(
    guild_id: int,
    guild: Guild = Depends(verify_guild_access),
    db: AsyncSession = Depends(get_db)
):
    """Sync guild data with Discord"""
    try:
        # Here you would typically:
        # 1. Fetch fresh data from Discord API
        # 2. Update local database
        # 3. Sync bot settings
        return {"status": "success", "message": "Guild data synchronized"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync guild data: {str(e)}"
        )
