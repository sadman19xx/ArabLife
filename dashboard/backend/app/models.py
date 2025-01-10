from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class Guild(Base):
    __tablename__ = "guilds"

    id = Column(String, primary_key=True)  # Discord Guild ID
    name = Column(String)
    icon_url = Column(String, nullable=True)
    owner_id = Column(String)
    member_count = Column(Integer)
    settings = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    roles = relationship("Role", back_populates="guild", cascade="all, delete-orphan")
    channels = relationship("Channel", back_populates="guild", cascade="all, delete-orphan")

class Role(Base):
    __tablename__ = "roles"

    id = Column(String, primary_key=True)  # Discord Role ID
    guild_id = Column(String, ForeignKey("guilds.id"))
    name = Column(String)
    color = Column(Integer)
    position = Column(Integer)
    permissions = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    guild = relationship("Guild", back_populates="roles")

class Channel(Base):
    __tablename__ = "channels"

    id = Column(String, primary_key=True)  # Discord Channel ID
    guild_id = Column(String, ForeignKey("guilds.id"))
    name = Column(String)
    type = Column(String)  # text, voice, category, etc.
    position = Column(Integer)
    settings = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    guild = relationship("Guild", back_populates="channels")

class BotSettings(Base):
    __tablename__ = "bot_settings"

    id = Column(Integer, primary_key=True)
    guild_id = Column(String, ForeignKey("guilds.id"), unique=True)
    welcome_channel_id = Column(String, nullable=True)
    welcome_message = Column(String, nullable=True)
    role_channel_id = Column(String, nullable=True)
    log_channel_id = Column(String, nullable=True)
    ticket_category_id = Column(String, nullable=True)
    automod_enabled = Column(Boolean, default=False)
    leveling_enabled = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class AutoModRule(Base):
    __tablename__ = "automod_rules"

    id = Column(Integer, primary_key=True)
    guild_id = Column(String, ForeignKey("guilds.id"))
    name = Column(String)
    type = Column(String)  # spam, banned_words, links, etc.
    settings = Column(JSON, default={})
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class LevelingSettings(Base):
    __tablename__ = "leveling_settings"

    id = Column(Integer, primary_key=True)
    guild_id = Column(String, ForeignKey("guilds.id"), unique=True)
    xp_per_message = Column(Integer, default=1)
    xp_cooldown = Column(Integer, default=60)  # seconds
    level_up_channel_id = Column(String, nullable=True)
    level_up_message = Column(String, nullable=True)
    role_rewards = Column(JSON, default={})  # {level: role_id}
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class UserLevel(Base):
    __tablename__ = "user_levels"

    id = Column(Integer, primary_key=True)
    guild_id = Column(String, ForeignKey("guilds.id"))
    user_id = Column(String)
    xp = Column(Integer, default=0)
    level = Column(Integer, default=0)
    last_message_time = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
