import aiosqlite
import asyncio
import logging
import os
from typing import Optional, Any, List, Dict
from datetime import datetime
from contextlib import asynccontextmanager

logger = logging.getLogger('discord')

class DatabasePool:
    """A connection pool for SQLite database"""
    
    def __init__(self, db_path: str, max_connections: int = 5):
        self.db_path = db_path
        self.max_connections = max_connections
        self._pool: List[aiosqlite.Connection] = []
        self._semaphore = asyncio.Semaphore(max_connections)
        self._lock = asyncio.Lock()

    @asynccontextmanager
    async def acquire(self):
        """Acquire a database connection from the pool"""
        async with self._semaphore:
            # Try to get an existing connection
            conn = None
            async with self._lock:
                if self._pool:
                    conn = self._pool.pop()
            
            # Create new connection if needed
            if conn is None:
                conn = await aiosqlite.connect(self.db_path)
                await conn.execute("PRAGMA foreign_keys = ON")
            
            try:
                yield conn
            finally:
                # Return connection to pool
                if len(self._pool) < self.max_connections:
                    self._pool.append(conn)
                else:
                    await conn.close()

    async def close_all(self):
        """Close all connections in the pool"""
        async with self._lock:
            while self._pool:
                conn = self._pool.pop()
                await conn.close()

class Database:
    """Database manager class"""
    
    def __init__(self):
        self.db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'bot.db')
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._pool: Optional[DatabasePool] = None
        
    async def init(self):
        """Initialize the database"""
        self._pool = DatabasePool(self.db_path)
        
        async with self._pool.acquire() as conn:
            # Enable foreign key support
            await conn.execute("PRAGMA foreign_keys = ON")
            
            # Create tables
            await conn.executescript("""
                -- Guilds table
                CREATE TABLE IF NOT EXISTS guilds (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    owner_id TEXT NOT NULL,
                    member_count INTEGER NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
                
                -- Bot settings table
                CREATE TABLE IF NOT EXISTS bot_settings (
                    guild_id TEXT PRIMARY KEY,
                    prefix TEXT DEFAULT '!',
                    welcome_channel_id TEXT,
                    audit_log_channel_id TEXT,
                    role_log_channel_id TEXT,
                    FOREIGN KEY(guild_id) REFERENCES guilds(id) ON DELETE CASCADE
                );
                
                -- User levels table
                CREATE TABLE IF NOT EXISTS user_levels (
                    guild_id TEXT,
                    user_id TEXT,
                    xp INTEGER DEFAULT 0,
                    level INTEGER DEFAULT 0,
                    last_message_time DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (guild_id, user_id),
                    FOREIGN KEY(guild_id) REFERENCES guilds(id) ON DELETE CASCADE
                );
                
                -- Leveling settings table
                CREATE TABLE IF NOT EXISTS leveling_settings (
                    guild_id TEXT PRIMARY KEY,
                    xp_per_message INTEGER DEFAULT 15,
                    xp_cooldown INTEGER DEFAULT 60,
                    level_up_channel_id TEXT,
                    level_up_message TEXT,
                    role_rewards TEXT DEFAULT '{}',
                    channel_multipliers TEXT DEFAULT '{}',
                    role_multipliers TEXT DEFAULT '{}',
                    leveling_enabled BOOLEAN DEFAULT 1,
                    FOREIGN KEY(guild_id) REFERENCES guilds(id) ON DELETE CASCADE
                );
                
                -- AutoMod settings table
                CREATE TABLE IF NOT EXISTS automod_settings (
                    guild_id TEXT PRIMARY KEY,
                    settings TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(guild_id) REFERENCES guilds(id) ON DELETE CASCADE
                );
                
                -- AutoMod logs table
                CREATE TABLE IF NOT EXISTS automod_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    reason TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(guild_id) REFERENCES guilds(id) ON DELETE CASCADE
                );
                
                -- Custom commands table
                CREATE TABLE IF NOT EXISTS custom_commands (
                    guild_id TEXT,
                    name TEXT,
                    response TEXT NOT NULL,
                    created_by TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (guild_id, name),
                    FOREIGN KEY(guild_id) REFERENCES guilds(id) ON DELETE CASCADE
                );
                
                -- Tickets table
                CREATE TABLE IF NOT EXISTS tickets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id TEXT NOT NULL,
                    channel_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    status TEXT DEFAULT 'open',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    closed_at DATETIME,
                    FOREIGN KEY(guild_id) REFERENCES guilds(id) ON DELETE CASCADE
                );
                
                -- Ticket messages table
                CREATE TABLE IF NOT EXISTS ticket_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticket_id INTEGER NOT NULL,
                    user_id TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(ticket_id) REFERENCES tickets(id) ON DELETE CASCADE
                );
            """)
            await conn.commit()

    @asynccontextmanager
    async def transaction(self):
        """Context manager for database transactions"""
        if not self._pool:
            raise RuntimeError("Database not initialized")
            
        async with self._pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await conn.execute("BEGIN")
                try:
                    yield cursor
                    await conn.commit()
                except Exception:
                    await conn.rollback()
                    raise

    async def add_xp(self, guild_id: str, user_id: str, xp_amount: int) -> Optional[int]:
        """Add XP to user and return new level if leveled up"""
        async with self.transaction() as cursor:
            # Get current XP and level
            await cursor.execute("""
                SELECT xp, level FROM user_levels
                WHERE guild_id = ? AND user_id = ?
            """, (guild_id, user_id))
            result = await cursor.fetchone()
            
            if result:
                current_xp, current_level = result
                new_xp = current_xp + xp_amount
            else:
                current_level = 0
                new_xp = xp_amount
                
            # Calculate new level
            new_level = self.calculate_level(new_xp)
            
            # Update database
            await cursor.execute("""
                INSERT OR REPLACE INTO user_levels (guild_id, user_id, xp, level, last_message_time)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (guild_id, user_id, new_xp, new_level))
            
            # Return new level if leveled up
            if new_level > current_level:
                return new_level
            return None

    @staticmethod
    def calculate_level(xp: int) -> int:
        """Calculate level from XP amount"""
        # Simple level calculation: level = xp/100
        return xp // 100

    async def close(self):
        """Close all database connections"""
        if self._pool:
            await self._pool.close_all()
            self._pool = None

# Global database instance
db = Database()
