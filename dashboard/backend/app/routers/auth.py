from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from typing import Dict
import httpx
import os
from ..auth import (
    create_access_token,
    get_discord_oauth_url,
    DISCORD_CLIENT_ID,
    DISCORD_CLIENT_SECRET,
    DISCORD_REDIRECT_URI,
    DISCORD_API_ENDPOINT
)
from ..schemas import ErrorResponse

router = APIRouter(
    prefix="/api/auth",
    tags=["auth"],
    responses={401: {"model": ErrorResponse}}
)

@router.get("/login")
async def login():
    """Get Discord OAuth2 login URL."""
    try:
        return {"url": get_discord_oauth_url()}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/callback")
async def callback(code: str):
    """Handle Discord OAuth2 callback."""
    try:
        # Exchange code for access token
        token_url = "https://discord.com/api/oauth2/token"
        data = {
            "client_id": DISCORD_CLIENT_ID,
            "client_secret": DISCORD_CLIENT_SECRET,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": DISCORD_REDIRECT_URI
        }
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }

        async with httpx.AsyncClient() as client:
            token_response = await client.post(token_url, data=data, headers=headers)
            token_data = token_response.json()

            if token_response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to get access token"
                )

            # Get user data
            user_url = f"{DISCORD_API_ENDPOINT}/users/@me"
            guilds_url = f"{DISCORD_API_ENDPOINT}/users/@me/guilds"
            headers = {
                "Authorization": f"Bearer {token_data['access_token']}"
            }

            user_response = await client.get(user_url, headers=headers)
            guilds_response = await client.get(guilds_url, headers=headers)

            if user_response.status_code != 200 or guilds_response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to get user data"
                )

            user_data = user_response.json()
            guilds_data = guilds_response.json()

            # Create JWT token
            token_data = {
                "sub": user_data["id"],
                "username": user_data["username"],
                "discriminator": user_data.get("discriminator", "0"),
                "avatar": user_data.get("avatar"),
                "guilds": [
                    {
                        "id": guild["id"],
                        "name": guild["name"],
                        "icon": guild.get("icon"),
                        "owner": guild.get("owner", False),
                        "permissions": guild.get("permissions", "0")
                    }
                    for guild in guilds_data
                ]
            }

            access_token = create_access_token(token_data)
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "user": {
                    "id": user_data["id"],
                    "username": user_data["username"],
                    "discriminator": user_data.get("discriminator", "0"),
                    "avatar": user_data.get("avatar"),
                    "guilds": token_data["guilds"]
                }
            }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/me")
async def get_user_me(current_user: Dict = Depends(OAuth2PasswordBearer(tokenUrl="token"))):
    """Get current user data."""
    return current_user
