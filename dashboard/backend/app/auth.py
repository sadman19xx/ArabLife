from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional, Dict
import os
from .schemas import ErrorResponse

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key")  # Change in production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# Discord OAuth2 settings
DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")
DISCORD_CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET")
DISCORD_REDIRECT_URI = os.getenv("DISCORD_REDIRECT_URI", "http://45.76.83.149/callback")
DISCORD_API_ENDPOINT = "https://discord.com/api/v10"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def create_access_token(data: Dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a new JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict:
    """Validate and decode JWT token to get current user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        
        # Add additional user data as needed
        user_data = {
            "id": user_id,
            "username": payload.get("username"),
            "discriminator": payload.get("discriminator"),
            "avatar": payload.get("avatar"),
            "guilds": payload.get("guilds", [])
        }
        return user_data
        
    except JWTError:
        raise credentials_exception

def get_discord_oauth_url() -> str:
    """Generate Discord OAuth2 URL."""
    if not DISCORD_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Discord client ID not configured"
        )
    
    params = {
        "client_id": DISCORD_CLIENT_ID,
        "redirect_uri": DISCORD_REDIRECT_URI,
        "response_type": "code",
        "scope": "identify guilds"
    }
    
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return f"https://discord.com/api/oauth2/authorize?{query}"

async def verify_guild_access(user_data: Dict, guild_id: str) -> bool:
    """Verify if user has access to the specified guild."""
    user_guilds = user_data.get("guilds", [])
    return any(str(guild["id"]) == guild_id for guild in user_guilds)

def get_bot_token() -> str:
    """Get bot token from environment variables."""
    token = os.getenv("DISCORD_BOT_TOKEN")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Bot token not configured"
        )
    return token

# Dependencies
async def get_current_active_user(
    current_user: Dict = Depends(get_current_user)
) -> Dict:
    """Get current active user with additional checks if needed."""
    return current_user

async def verify_guild_permissions(
    guild_id: str,
    current_user: Dict = Depends(get_current_active_user)
) -> None:
    """Verify user has permissions for the specified guild."""
    if not await verify_guild_access(current_user, guild_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this guild"
        )
