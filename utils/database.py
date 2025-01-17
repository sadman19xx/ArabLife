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
                
# Global database instance
db = Database()

async def setup(bot):
    """Setup function for loading as extension"""
    await db.init()
