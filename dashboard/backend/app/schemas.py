from pydantic import BaseModel, HttpUrl
from typing import List, Optional

# Bot Installation Schemas
class BotInstallRequest(BaseModel):
    token: str
    guild_id: int
    role_ids_allowed: List[int]
    role_id_to_give: int
    role_id_remove_allowed: int
    role_activity_log_channel_id: int
    audit_log_channel_id: int
    visa_image_url: HttpUrl

class BotStatusResponse(BaseModel):
    status: str  # "running" or "stopped"
    logs: List[str]

# Guild Settings Schemas
class GuildSettingsBase(BaseModel):
    prefix: str = "/"
    language: str = "en"
    timezone: str = "UTC"
    welcome_channel_id: Optional[int] = None
    log_channel_id: Optional[int] = None
    mute_role_id: Optional[int] = None
    auto_role_id: Optional[int] = None

class GuildSettingsCreate(GuildSettingsBase):
    guild_id: int

class GuildSettingsUpdate(GuildSettingsBase):
    pass

class GuildSettingsResponse(GuildSettingsBase):
    id: int
    guild_id: int

    class Config:
        orm_mode = True

# Custom Command Schemas
class CustomCommandBase(BaseModel):
    name: str
    response: str
    description: Optional[str] = None
    enabled: bool = True

class CustomCommandCreate(CustomCommandBase):
    guild_id: int

class CustomCommandUpdate(CustomCommandBase):
    pass

class CustomCommandResponse(CustomCommandBase):
    id: int
    guild_id: int

    class Config:
        orm_mode = True

# Welcome Message Schemas
class WelcomeMessageBase(BaseModel):
    content: str
    embed_title: Optional[str] = None
    embed_description: Optional[str] = None
    embed_color: Optional[int] = None
    enabled: bool = True

class WelcomeMessageCreate(WelcomeMessageBase):
    guild_id: int

class WelcomeMessageUpdate(WelcomeMessageBase):
    pass

class WelcomeMessageResponse(WelcomeMessageBase):
    id: int
    guild_id: int

    class Config:
        orm_mode = True

# AutoMod Schemas
class AutoModBase(BaseModel):
    enabled: bool = True
    spam_detection: bool = True
    spam_threshold: int = 5
    spam_interval: int = 5
    raid_protection: bool = True
    raid_threshold: int = 10
    raid_interval: int = 30
    banned_words: List[str] = []
    warn_threshold: int = 3
    mute_duration: int = 300
    ban_duration: Optional[int] = None

class AutoModCreate(AutoModBase):
    guild_id: int

class AutoModUpdate(AutoModBase):
    pass

class AutoModResponse(AutoModBase):
    id: int
    guild_id: int

    class Config:
        orm_mode = True

# Leveling Schemas
class LevelingSettingsBase(BaseModel):
    enabled: bool = True
    xp_per_message: int = 15
    xp_cooldown: int = 60
    level_up_channel_id: Optional[int] = None
    level_up_message: str = "Congratulations {user}! You reached level {level}!"
    role_rewards: dict = {}

class LevelingSettingsCreate(LevelingSettingsBase):
    guild_id: int

class LevelingSettingsUpdate(LevelingSettingsBase):
    pass

class LevelingSettingsResponse(LevelingSettingsBase):
    id: int
    guild_id: int

    class Config:
        orm_mode = True
