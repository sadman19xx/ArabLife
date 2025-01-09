from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, JSON, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    discord_id = Column(String, unique=True, index=True)
    username = Column(String)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Guild(Base):
    __tablename__ = "guilds"

    id = Column(Integer, primary_key=True, index=True)
    discord_id = Column(String, unique=True, index=True)
    name = Column(String)
    icon_url = Column(String, nullable=True)
    settings = relationship("GuildSettings", back_populates="guild", uselist=False)
    welcome_messages = relationship("WelcomeMessage", back_populates="guild")
    custom_commands = relationship("CustomCommand", back_populates="guild")
    automod_logs = relationship("AutoModLog", back_populates="guild")
    leveling_entries = relationship("Leveling", back_populates="guild")

class GuildSettings(Base):
    __tablename__ = "guild_settings"

    id = Column(Integer, primary_key=True, index=True)
    guild_id = Column(Integer, ForeignKey("guilds.id"))
    prefix = Column(String, default="/")
    mod_role_id = Column(String, nullable=True)
    admin_role_id = Column(String, nullable=True)
    mute_role_id = Column(String, nullable=True)
    welcome_channel_id = Column(String, nullable=True)
    log_channel_id = Column(String, nullable=True)
    auto_role_id = Column(String, nullable=True)
    level_up_channel_id = Column(String, nullable=True)
    ticket_category_id = Column(String, nullable=True)
    verification_level = Column(Integer, default=0)
    anti_spam = Column(Boolean, default=True)
    anti_raid = Column(Boolean, default=True)
    max_warnings = Column(Integer, default=3)
    custom_settings = Column(JSON, nullable=True)
    guild = relationship("Guild", back_populates="settings")

class WelcomeMessage(Base):
    __tablename__ = "welcome_messages"

    id = Column(Integer, primary_key=True, index=True)
    guild_id = Column(Integer, ForeignKey("guilds.id"))
    content = Column(String)
    embed_title = Column(String, nullable=True)
    embed_description = Column(String, nullable=True)
    embed_color = Column(String, nullable=True)
    is_enabled = Column(Boolean, default=True)
    guild = relationship("Guild", back_populates="welcome_messages")

class CustomCommand(Base):
    __tablename__ = "custom_commands"

    id = Column(Integer, primary_key=True, index=True)
    guild_id = Column(Integer, ForeignKey("guilds.id"))
    name = Column(String)
    response = Column(String)
    description = Column(String, nullable=True)
    is_enabled = Column(Boolean, default=True)
    required_role_id = Column(String, nullable=True)
    cooldown = Column(Integer, default=0)
    guild = relationship("Guild", back_populates="custom_commands")

class AutoMod(Base):
    __tablename__ = "automod"

    id = Column(Integer, primary_key=True, index=True)
    guild_id = Column(Integer, ForeignKey("guilds.id"))
    banned_words = Column(JSON, nullable=True)
    banned_links = Column(JSON, nullable=True)
    spam_threshold = Column(Integer, default=5)
    spam_interval = Column(Integer, default=5)
    raid_threshold = Column(Integer, default=10)
    raid_interval = Column(Integer, default=30)
    action_type = Column(String, default="warn")  # warn, mute, kick, ban
    is_enabled = Column(Boolean, default=True)
    guild = relationship("Guild", back_populates="automod")

class AutoModLog(Base):
    __tablename__ = "automod_logs"

    id = Column(Integer, primary_key=True, index=True)
    guild_id = Column(Integer, ForeignKey("guilds.id"))
    user_id = Column(Integer)  # Discord user ID
    action = Column(String)  # warn, mute, kick, ban, raid_protection
    reason = Column(String)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    guild = relationship("Guild", back_populates="automod_logs")

class Leveling(Base):
    __tablename__ = "leveling"

    id = Column(Integer, primary_key=True, index=True)
    guild_id = Column(Integer, ForeignKey("guilds.id"))
    user_discord_id = Column(String)
    xp = Column(Integer, default=0)
    level = Column(Integer, default=0)
    last_message_time = Column(DateTime(timezone=True), nullable=True)
    guild = relationship("Guild", back_populates="leveling_entries")

class RoleMenu(Base):
    __tablename__ = "role_menus"

    id = Column(Integer, primary_key=True, index=True)
    guild_id = Column(Integer, ForeignKey("guilds.id"))
    channel_id = Column(String)
    message_id = Column(String)
    title = Column(String)
    description = Column(String, nullable=True)
    roles = Column(JSON)  # List of {role_id: str, emoji: str, description: str}
    is_enabled = Column(Boolean, default=True)
    guild = relationship("Guild", back_populates="role_menus")
