from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict
import subprocess
import os
import psutil
from ..database import get_db
from ..auth import get_current_active_user, verify_guild_permissions
from ..schemas import ErrorResponse

router = APIRouter(
    prefix="/api/bot",
    tags=["bot"],
    responses={401: {"model": ErrorResponse}}
)

def get_bot_process():
    """Get the bot process if it's running."""
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['cmdline'] and 'python' in proc.info['cmdline'][0] and 'bot.py' in proc.info['cmdline']:
                return proc
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return None

@router.get("/status")
async def get_bot_status(
    current_user: Dict = Depends(get_current_active_user)
):
    """Get the current status of the bot."""
    try:
        process = get_bot_process()
        if process:
            # Get process information
            with process.oneshot():
                cpu_percent = process.cpu_percent()
                memory_info = process.memory_info()
                uptime = process.create_time()
                status = "running"
        else:
            cpu_percent = 0
            memory_info = None
            uptime = 0
            status = "stopped"

        return {
            "status": status,
            "cpu_percent": cpu_percent,
            "memory_mb": memory_info.rss / 1024 / 1024 if memory_info else 0,
            "uptime": uptime if uptime else 0
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/start")
async def start_bot(
    current_user: Dict = Depends(get_current_active_user)
):
    """Start the bot if it's not already running."""
    try:
        if get_bot_process():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bot is already running"
            )

        # Start the bot using screen
        subprocess.run([
            "screen",
            "-dmS",
            "arablife",
            "python3",
            "bot.py"
        ], check=True)

        return {"message": "Bot started successfully"}

    except subprocess.CalledProcessError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start bot: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/stop")
async def stop_bot(
    current_user: Dict = Depends(get_current_active_user)
):
    """Stop the bot if it's running."""
    try:
        process = get_bot_process()
        if not process:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bot is not running"
            )

        # Stop the bot process
        process.terminate()
        process.wait(timeout=5)  # Wait up to 5 seconds for graceful shutdown

        return {"message": "Bot stopped successfully"}

    except psutil.TimeoutExpired:
        # Force kill if graceful shutdown fails
        if process:
            process.kill()
        return {"message": "Bot force stopped"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/restart")
async def restart_bot(
    current_user: Dict = Depends(get_current_active_user)
):
    """Restart the bot."""
    try:
        # Stop the bot if it's running
        process = get_bot_process()
        if process:
            process.terminate()
            try:
                process.wait(timeout=5)
            except psutil.TimeoutExpired:
                process.kill()

        # Start the bot
        subprocess.run([
            "screen",
            "-dmS",
            "arablife",
            "python3",
            "bot.py"
        ], check=True)

        return {"message": "Bot restarted successfully"}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/logs")
async def get_bot_logs(
    current_user: Dict = Depends(get_current_active_user),
    lines: int = 100
):
    """Get the bot's recent logs."""
    try:
        # Get logs from screen session
        result = subprocess.run([
            "screen",
            "-S",
            "arablife",
            "-X",
            "hardcopy",
            "bot.log"
        ], capture_output=True, text=True)

        # Read the log file
        if os.path.exists("bot.log"):
            with open("bot.log", "r") as f:
                logs = f.readlines()
            
            # Clean up log file
            os.remove("bot.log")
            
            # Return the most recent lines
            return {"logs": logs[-lines:]}
        else:
            return {"logs": []}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
