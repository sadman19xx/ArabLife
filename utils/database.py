import aiosqlite
import logging
import os
from typing import Optional, Any, AsyncContextManager
from contextlib import asynccontextmanager

logger = logging.getLogger('discord')

class Database:
    """Database handler class"""
    
    def __init__(self):
        self.db_path = os.path.join('data', 'bot.db')
        self._connection: Optional[aiosqlite.Connection] = None
        
    async def init(self):
        """Initialize database connection and tables"""
        # Ensure data directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # Create initial connection
        self._connection = await aiosqlite.connect(self.db_path)
        self._connection.row_factory = aiosqlite.Row
        
        # Initialize schema
        try:
            with open('utils/schema.sql') as f:
                await self._connection.executescript(f.read())
            await self._connection.commit()
        except Exception as e:
            logger.error(f"Failed to initialize database schema: {e}")
            raise
            
        logger.info("Database initialized successfully")
        
    async def close(self):
        """Close database connection"""
        if self._connection:
            await self._connection.close()
            self._connection = None
            
    @asynccontextmanager
    async def transaction(self) -> AsyncContextManager[aiosqlite.Cursor]:
        """Get a database cursor within a transaction"""
        if not self._connection:
            raise RuntimeError("Database not initialized")
            
        async with self._connection.cursor() as cursor:
            try:
                yield cursor
                await self._connection.commit()
            except Exception:
                await self._connection.rollback()
                raise
                
    def calculate_level(self, xp: int) -> int:
        """Calculate level from XP amount"""
        # Simple level calculation: level = xp/100
        return xp // 100
        
    async def add_xp(self, guild_id: str, user_id: str, amount: int) -> Optional[int]:
        """Add XP to user and return new level if leveled up"""
        try:
            async with self.transaction() as cursor:
                # Get current XP
                await cursor.execute("""
                    SELECT xp, level FROM user_levels
                    WHERE guild_id = ? AND user_id = ?
                """, (guild_id, user_id))
                result = await cursor.fetchone()
                
                if result:
                    current_xp = result['xp']
                    current_level = result['level']
                else:
                    current_xp = 0
                    current_level = 0
                    
                # Add XP
                new_xp = current_xp + amount
                new_level = self.calculate_level(new_xp)
                
                # Update database
                await cursor.execute("""
                    INSERT OR REPLACE INTO user_levels (
                        guild_id, user_id, xp, level, last_message_time
                    ) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (guild_id, user_id, new_xp, new_level))
                
                # Return new level if leveled up
                if new_level > current_level:
                    return new_level
                return None
                
        except Exception as e:
            logger.error(f"Failed to add XP: {e}")
            return None

# Global database instance
db = Database()

async def setup(bot):
    """Setup function for loading as extension"""
    await db.init()
