from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import timedelta
from typing import List

from ..database import get_db
from ..models import User, Guild
from ..schemas import (
    Token, UserResponse, GuildResponse,
    DiscordAuthRequest, DiscordAuthResponse
)
from ..auth import AuthManager, DiscordOAuth, ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter()

@router.post("/login/discord", response_model=DiscordAuthResponse)
async def discord_login(
    auth_request: DiscordAuthRequest,
    db: AsyncSession = Depends(get_db)
):
    """Login with Discord OAuth2"""
    try:
        # Exchange code for token
        token_data = await DiscordOAuth.exchange_code(auth_request.code)
        access_token = token_data["access_token"]

        # Get user data from Discord
        user_data = await DiscordOAuth.get_user_data(access_token)
        guilds_data = await DiscordOAuth.get_user_guilds(access_token)

        # Check if user exists, if not create new user
        result = await db.execute(
            select(User).filter(User.discord_id == str(user_data["id"]))
        )
        user = result.scalar_one_or_none()

        if not user:
            user = User(
                discord_id=str(user_data["id"]),
                username=user_data["username"],
                email=user_data["email"],
                is_admin=False  # Set admin status based on your criteria
            )
            db.add(user)

        # Update user's guilds
        for guild_data in guilds_data:
            result = await db.execute(
                select(Guild).filter(Guild.discord_id == str(guild_data["id"]))
            )
            guild = result.scalar_one_or_none()

            if not guild:
                guild = Guild(
                    discord_id=str(guild_data["id"]),
                    name=guild_data["name"],
                    icon_url=guild_data.get("icon")
                )
                db.add(guild)

        await db.commit()

        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        jwt_token = AuthManager.create_access_token(
            data={"sub": str(user_data["id"])},
            expires_delta=access_token_expires
        )

        # Prepare response
        return DiscordAuthResponse(
            access_token=jwt_token,
            user=user,
            guilds=[
                GuildResponse(
                    id=g["id"],
                    discord_id=str(g["id"]),
                    name=g["name"],
                    icon_url=g.get("icon")
                )
                for g in guilds_data
                if (g["permissions"] & 0x8) == 0x8  # Check for admin permission
            ]
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Failed to authenticate: {str(e)}"
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user(
    current_user: User = Depends(AuthManager.get_current_user)
):
    """Get current authenticated user"""
    return current_user

@router.get("/guilds", response_model=List[GuildResponse])
async def get_user_guilds(
    current_user: User = Depends(AuthManager.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get guilds where the user has admin permissions"""
    try:
        # Get fresh guild data from Discord
        token_data = await DiscordOAuth.get_user_guilds(current_user.discord_id)
        
        # Filter guilds where user has admin permission
        admin_guilds = [
            guild for guild in token_data
            if (int(guild["permissions"]) & 0x8) == 0x8
        ]

        # Update local database with fresh guild data
        guild_responses = []
        for guild_data in admin_guilds:
            result = await db.execute(
                select(Guild).filter(Guild.discord_id == str(guild_data["id"]))
            )
            guild = result.scalar_one_or_none()

            if not guild:
                guild = Guild(
                    discord_id=str(guild_data["id"]),
                    name=guild_data["name"],
                    icon_url=guild_data.get("icon")
                )
                db.add(guild)
                await db.commit()
                await db.refresh(guild)

            guild_responses.append(guild)

        return guild_responses

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch guilds: {str(e)}"
        )

@router.get("/oauth-url")
async def get_oauth_url():
    """Get Discord OAuth2 URL"""
    return {"url": DiscordOAuth.get_oauth_url()}
