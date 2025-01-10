from pydantic import BaseModel, Field
from typing import Optional, Dict, List
from datetime import datetime

# Base Models
class BaseSchema(BaseModel):
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

# Guild Schemas
class GuildBase(BaseSchema):
    name: str
    icon_url: Optional[str] = None
    owner_id: str
    member_count: int
    settings: Dict = Field(default_factory=dict)

class GuildCreate(GuildBase):
    id: str

class GuildUpdate(GuildBase):
    pass

class Guild(GuildBase):
    id: str
    created_at: datetime
    updated_at: datetime

# Role Schemas
class RoleBase(BaseSchema):
    name: str
    color: int
    position: int
    permissions: str

class RoleCreate(RoleBase):
    id: str
    guild_id: str

class RoleUpdate(RoleBase):
    pass

class Role(RoleBase):
    id: str
    guild_id: str
    created_at: datetime
    updated_at: datetime

# Channel Schemas
class ChannelBase(BaseSchema):
    name: str
    type: str
    position: int
    settings: Dict = Field(default_factory=dict)

class ChannelCreate(ChannelBase):
    id: str
    guild_id: str

class ChannelUpdate(ChannelBase):
    pass

class Channel(ChannelBase):
    id: str
    guild_id: str
    created_at: datetime
    updated_at: datetime

# Bot Settings Schemas
class BotSettingsBase(BaseSchema):
    welcome_channel_id: Optional[str] = None
    welcome_message: Optional[str] = None
    role_channel_id: Optional[str] = None
    log_channel_id: Optional[str] = None
    ticket_category_id: Optional[str] = None
    automod_enabled: bool = False
    leveling_enabled: bool = False

class BotSettingsCreate(BotSettingsBase):
    guild_id: str

class BotSettingsUpdate(BotSettingsBase):
    pass

class BotSettings(BotSettingsBase):
    id: int
    guild_id: str
    created_at: datetime
    updated_at: datetime

# AutoMod Rule Schemas
class AutoModRuleBase(BaseSchema):
    name: str
    type: str
    settings: Dict = Field(default_factory=dict)
    enabled: bool = True

class AutoModRuleCreate(AutoModRuleBase):
    guild_id: str

class AutoModRuleUpdate(AutoModRuleBase):
    pass

class AutoModRule(AutoModRuleBase):
    id: int
    guild_id: str
    created_at: datetime
    updated_at: datetime

# Leveling Settings Schemas
class LevelingSettingsBase(BaseSchema):
    xp_per_message: int = 1
    xp_cooldown: int = 60
    level_up_channel_id: Optional[str] = None
    level_up_message: Optional[str] = None
    role_rewards: Dict[str, str] = Field(default_factory=dict)

class LevelingSettingsCreate(LevelingSettingsBase):
    guild_id: str

class LevelingSettingsUpdate(LevelingSettingsBase):
    pass

class LevelingSettings(LevelingSettingsBase):
    id: int
    guild_id: str
    created_at: datetime
    updated_at: datetime

# User Level Schemas
class UserLevelBase(BaseSchema):
    xp: int = 0
    level: int = 0
    last_message_time: Optional[datetime] = None

class UserLevelCreate(UserLevelBase):
    guild_id: str
    user_id: str

class UserLevelUpdate(UserLevelBase):
    pass

class UserLevel(UserLevelBase):
    id: int
    guild_id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

# Response Models
class GuildResponse(BaseSchema):
    guild: Guild
    roles: List[Role]
    channels: List[Channel]
    settings: Optional[BotSettings] = None

class GuildListResponse(BaseSchema):
    guilds: List[Guild]

class ErrorResponse(BaseSchema):
    detail: str
