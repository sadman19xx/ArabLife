from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from .database import get_db
from .models import User
import os

# Security configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")  # Change in production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Discord OAuth2 settings
DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")
DISCORD_CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET")
DISCORD_REDIRECT_URI = os.getenv("DISCORD_REDIRECT_URI", "http://localhost:3000/auth/callback")
DISCORD_API_ENDPOINT = "https://discord.com/api/v10"

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class AuthManager:
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password: str) -> str:
        return pwd_context.hash(password)

    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    @staticmethod
    async def get_current_user(
        token: str = Depends(oauth2_scheme),
        db: AsyncSession = Depends(get_db)
    ) -> User:
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
        except JWTError:
            raise credentials_exception

        result = await db.execute(select(User).filter(User.discord_id == user_id))
        user = result.scalar_one_or_none()
        
        if user is None:
            raise credentials_exception
        return user

    @staticmethod
    async def get_current_admin(
        current_user: User = Depends(get_current_user)
    ) -> User:
        if not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        return current_user

class DiscordOAuth:
    @staticmethod
    def get_oauth_url() -> str:
        return f"{DISCORD_API_ENDPOINT}/oauth2/authorize?client_id={DISCORD_CLIENT_ID}&redirect_uri={DISCORD_REDIRECT_URI}&response_type=code&scope=identify%20email%20guilds"

    @staticmethod
    async def exchange_code(code: str) -> dict:
        """Exchange authorization code for access token"""
        import aiohttp

        data = {
            'client_id': DISCORD_CLIENT_ID,
            'client_secret': DISCORD_CLIENT_SECRET,
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': DISCORD_REDIRECT_URI,
            'scope': 'identify email guilds'
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(f'{DISCORD_API_ENDPOINT}/oauth2/token', data=data) as response:
                if response.status != 200:
                    raise HTTPException(
                        status_code=response.status,
                        detail="Failed to exchange code"
                    )
                return await response.json()

    @staticmethod
    async def get_user_data(access_token: str) -> dict:
        """Get user data from Discord"""
        import aiohttp

        headers = {'Authorization': f'Bearer {access_token}'}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(f'{DISCORD_API_ENDPOINT}/users/@me', headers=headers) as response:
                if response.status != 200:
                    raise HTTPException(
                        status_code=response.status,
                        detail="Failed to get user data"
                    )
                return await response.json()

    @staticmethod
    async def get_user_guilds(access_token: str) -> list:
        """Get user's guilds from Discord"""
        import aiohttp

        headers = {'Authorization': f'Bearer {access_token}'}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(f'{DISCORD_API_ENDPOINT}/users/@me/guilds', headers=headers) as response:
                if response.status != 200:
                    raise HTTPException(
                        status_code=response.status,
                        detail="Failed to get user guilds"
                    )
                return await response.json()
