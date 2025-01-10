import aiosqlite
import json
from datetime import datetime
from typing import Optional, Dict, Any
import logging
import os

logger = logging.getLogger('discord')

class Database:
    """Unified database handler for bot and dashboard"""
    
    def __init__(self, db_path: str = "./dashboard.db"):
        self.db_path = db_path
        
    async def init(self):
        """Initialize database tables"""
        async with aiosqlite.connect(self.db_path) as db:
            # Enable foreign keys
            await db.execute("PRAGMA foreign_keys = ON")
            
            # Create tables if they don't exist
            await db.executescript("""
                -- Guilds table
                CREATE TABLE IF NOT EXISTS guilds (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    icon_url TEXT,
                    owner_id TEXT,
                    member_count INTEGER,
                    settings JSON DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                -- Roles table
                CREATE TABLE IF NOT EXISTS roles (
                    id TEXT PRIMARY KEY,
                    guild_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    color INTEGER,
                    position INTEGER,
                    permissions TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (guild_id) REFERENCES guilds(id) ON DELETE CASCADE
                );

                -- Channels table
                CREATE TABLE IF NOT EXISTS channels (
                    id TEXT PRIMARY KEY,
                    guild_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL,
                    position INTEGER,
                    settings JSON DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (guild_id) REFERENCES guilds(id) ON DELETE CASCADE
                );

                -- Bot settings table
                CREATE TABLE IF NOT EXISTS bot_settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id TEXT UNIQUE NOT NULL,
                    prefix TEXT DEFAULT '!',
                    welcome_channel_id TEXT,
                    welcome_message TEXT,
                    role_channel_id TEXT,
                    log_channel_id TEXT,
                    ticket_category_id TEXT,
                    automod_enabled BOOLEAN DEFAULT 0,
                    leveling_enabled BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (guild_id) REFERENCES guilds(id) ON DELETE CASCADE
                );

                -- AutoMod rules table
                CREATE TABLE IF NOT EXISTS automod_rules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL,
                    settings JSON DEFAULT '{}',
                    enabled BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (guild_id) REFERENCES guilds(id) ON DELETE CASCADE
                );

                -- Leveling settings table
                CREATE TABLE IF NOT EXISTS leveling_settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id TEXT UNIQUE NOT NULL,
                    xp_per_message INTEGER DEFAULT 1,
                    xp_cooldown INTEGER DEFAULT 60,
                    level_up_channel_id TEXT,
                    level_up_message TEXT,
                    role_rewards JSON DEFAULT '{}',
                    channel_multipliers JSON DEFAULT '{}',
                    role_multipliers JSON DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (guild_id) REFERENCES guilds(id) ON DELETE CASCADE
                );

                -- User levels table
                CREATE TABLE IF NOT EXISTS user_levels (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    xp INTEGER DEFAULT 0,
                    level INTEGER DEFAULT 0,
                    last_message_time TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(guild_id, user_id),
                    FOREIGN KEY (guild_id) REFERENCES guilds(id) ON DELETE CASCADE
                );

                -- Custom commands table
                CREATE TABLE IF NOT EXISTS custom_commands (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    response TEXT NOT NULL,
                    created_by TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(guild_id, name),
                    FOREIGN KEY (guild_id) REFERENCES guilds(id) ON DELETE CASCADE
                );

                -- AutoMod settings table
                CREATE TABLE IF NOT EXISTS automod_settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id TEXT UNIQUE NOT NULL,
                    settings JSON DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (guild_id) REFERENCES guilds(id) ON DELETE CASCADE
                );

                -- AutoMod logs table
                CREATE TABLE IF NOT EXISTS automod_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    reason TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (guild_id) REFERENCES guilds(id) ON DELETE CASCADE
                );

                -- Message similarity cache table
                CREATE TABLE IF NOT EXISTS message_similarity_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    message_hash TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (guild_id) REFERENCES guilds(id) ON DELETE CASCADE
                );
            """)
            await db.commit()

    async def get_guild_settings(self, guild_id: str) -> Optional[Dict[str, Any]]:
        """Get all settings for a guild"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            # Get bot settings
            async with db.execute(
                "SELECT * FROM bot_settings WHERE guild_id = ?",
                (guild_id,)
            ) as cursor:
                bot_settings = await cursor.fetchone()
            
            # Get leveling settings
            async with db.execute(
                "SELECT * FROM leveling_settings WHERE guild_id = ?",
                (guild_id,)
            ) as cursor:
                leveling_settings = await cursor.fetchone()
            
            # Get automod rules
            async with db.execute(
                "SELECT * FROM automod_rules WHERE guild_id = ?",
                (guild_id,)
            ) as cursor:
                automod_rules = await cursor.fetchall()
            
            if not bot_settings:
                return None
                
            return {
                "bot": dict(bot_settings),
                "leveling": dict(leveling_settings) if leveling_settings else {},
                "automod_rules": [dict(rule) for rule in automod_rules]
            }

    async def update_guild_settings(self, guild_id: str, settings: Dict[str, Any]):
        """Update guild settings"""
        async with aiosqlite.connect(self.db_path) as db:
            if "bot" in settings:
                bot_settings = settings["bot"]
                placeholders = ", ".join(f"{k} = ?" for k in bot_settings.keys())
                values = list(bot_settings.values())
                await db.execute(
                    f"UPDATE bot_settings SET {placeholders} WHERE guild_id = ?",
                    (*values, guild_id)
                )
            
            if "leveling" in settings:
                leveling_settings = settings["leveling"]
                placeholders = ", ".join(f"{k} = ?" for k in leveling_settings.keys())
                values = list(leveling_settings.values())
                await db.execute(
                    f"UPDATE leveling_settings SET {placeholders} WHERE guild_id = ?",
                    (*values, guild_id)
                )
            
            await db.commit()

    async def add_xp(self, guild_id: str, user_id: str, xp_amount: int) -> Optional[int]:
        """Add XP to user and return new level if leveled up"""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                # Get current XP and level
                async with db.execute(
                    "SELECT xp, level FROM user_levels WHERE guild_id = ? AND user_id = ?",
                    (guild_id, user_id)
                ) as cursor:
                    result = await cursor.fetchone()
                
                if result:
                    current_xp, current_level = result
                else:
                    current_xp, current_level = 0, 0
                    await db.execute(
                        "INSERT INTO user_levels (guild_id, user_id, xp, level) VALUES (?, ?, 0, 0)",
                        (guild_id, user_id)
                    )
                
                # Calculate new XP and level
                new_xp = current_xp + xp_amount
                new_level = self.calculate_level(new_xp)
                
                # Update database
                await db.execute(
                    """UPDATE user_levels 
                    SET xp = ?, level = ?, last_message_time = CURRENT_TIMESTAMP
                    WHERE guild_id = ? AND user_id = ?""",
                    (new_xp, new_level, guild_id, user_id)
                )
                
                await db.commit()
                return new_level if new_level > current_level else None
                
            except Exception as e:
                logger.error(f"Failed to add XP: {str(e)}")
                return None

    @staticmethod
    def calculate_level(xp: int) -> int:
        """Calculate level based on total XP"""
        level = 0
        xp_for_level = 0
        
        while True:
            xp_needed = 5 * (level ** 2) + 50 * level + 100
            if xp_for_level + xp_needed > xp:
                break
            xp_for_level += xp_needed
            level += 1
            
        return level

# Create global database instance
db = Database()
