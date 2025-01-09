from pydantic import BaseModel
from typing import List, Optional, Dict

# Auth schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class User(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None

# Bot schemas
class BotStatus(BaseModel):
    is_online: bool
    uptime: str
    guild_count: int
    member_count: int

# Guild schemas
class Guild(BaseModel):
    id: str
    name: str
    icon: Optional[str]
    member_count: int
    owner_id: str

# Command schemas
class Command(BaseModel):
    name: str
    description: str
    usage: str
    category: str
    is_enabled: bool

# Settings schemas
class WelcomeSettings(BaseModel):
    channel_id: Optional[str]
    message: str
    is_enabled: bool

class RoleSettings(BaseModel):
    role_id: str
    name: str
    color: str
    position: int

# AutoMod schemas
class AutoModSettings(BaseModel):
    is_enabled: bool
    banned_words: List[str]
    banned_links: List[str]
    spam_threshold: int
    spam_interval: int
    raid_threshold: int
    raid_interval: int
    action_type: str

class AutoModAction(BaseModel):
    user_id: str
    action: str
    reason: str
    timestamp: str

# Leveling schemas
class RoleReward(BaseModel):
    level: int
    role_id: str

class LevelingSettings(BaseModel):
    is_enabled: bool
    xp_per_message: int
    xp_cooldown: int
    level_up_channel_id: Optional[str]
    level_up_message: str
    role_rewards: List[RoleReward]

class UserLevel(BaseModel):
    user_discord_id: str
    username: str
    level: int
    xp: int
    rank: int

class LeaderboardEntry(BaseModel):
    user_discord_id: str
    username: str
    level: int
    xp: int
    rank: int

# Response schemas
class Response(BaseModel):
    success: bool
    message: str
    data: Optional[Dict] = None
