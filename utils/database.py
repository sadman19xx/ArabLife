import aiosqlite
import asyncio
import logging
import os
import traceback
from typing import Optional, Any, List, Dict, AsyncGenerator, Tuple, Union
from datetime import datetime
from contextlib import asynccontextmanager

logger = logging.getLogger('discord')

class DatabaseError(Exception):
    """Base exception for database errors"""
    pass

class ConnectionError(DatabaseError):
    """Exception raised for connection-related errors"""
    pass

class TransactionError(DatabaseError):
    """Exception raised for transaction-related errors"""
    pass

class DatabasePool:
    """A connection pool for SQLite database
    
    Manages a pool of database connections to improve performance and resource usage.
    
    Attributes:
        db_path: Path to the SQLite database file
        max_connections: Maximum number of concurrent connections allowed
        _pool: List of available database connections
        _semaphore: Controls access to connections
        _lock: Ensures thread-safe operations on the pool
    """
    
    def __init__(self, db_path: str, max_connections: int = 5) -> None:
        self.db_path = db_path
        self.max_connections = max_connections
        self._pool: List[aiosqlite.Connection] = []
        self._semaphore = asyncio.Semaphore(max_connections)
        self._lock = asyncio.Lock()

    @asynccontextmanager
    async def acquire(self) -> AsyncGenerator[aiosqlite.Connection, None]:
        """Acquire a database connection from the pool
        
        Returns:
            A database connection from the pool
            
        Raises:
            ConnectionError: If unable to establish a database connection
        """
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
            except Exception as e:
                logger.error(f"Database connection error: {e}")
                logger.debug(traceback.format_exc())
                raise ConnectionError(f"Database connection error: {e}") from e
            finally:
                try:
                    # Return connection to pool
                    if len(self._pool) < self.max_connections:
                        self._pool.append(conn)
                    else:
                        await conn.close()
                except Exception as e:
                    logger.error(f"Error returning connection to pool: {e}")

    async def close_all(self) -> None:
        """Close all connections in the pool
        
        Ensures all database connections are properly closed when shutting down.
        """
        async with self._lock:
            while self._pool:
                conn = self._pool.pop()
                await conn.close()

class Database:
    """Database manager class
    
    Handles all database operations including initialization, transactions,
    and specific data operations like XP management.
    
    Attributes:
        db_path: Path to the SQLite database file
        _pool: Connection pool for managing database connections
    """
    
    def __init__(self) -> None:
        self.db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'bot.db')
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._pool: Optional[DatabasePool] = None
        
    async def check_health(self) -> bool:
        """Check database health
        
        Returns:
            True if database is healthy, False otherwise
        """
        if not self._pool:
            return False
            
        try:
            async with self.transaction() as cursor:
                await cursor.execute("SELECT 1")
                return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False

    async def _run_migrations(self, conn: aiosqlite.Connection) -> None:
        """Run database migrations
        
        Args:
            conn: Database connection to use
            
        Raises:
            DatabaseError: If migrations fail
        """
        try:
            # Create migrations table if it doesn't exist
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS migrations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            await conn.commit()
            
            # Add any new migrations here
            migrations = [
                # Example migration:
                # ("add_user_roles_index", """
                #     CREATE INDEX IF NOT EXISTS idx_user_roles_role ON user_roles(role_id);
                # """)
            ]
            
            async with conn.cursor() as cursor:
                # Apply migrations that haven't been applied yet
                for name, sql in migrations:
                    try:
                        await cursor.execute("SELECT 1 FROM migrations WHERE name = ?", (name,))
                        if not await cursor.fetchone():
                            await cursor.execute(sql)
                            await cursor.execute("INSERT INTO migrations (name) VALUES (?)", (name,))
                            await conn.commit()
                            logger.info(f"Applied migration: {name}")
                    except Exception as e:
                        error_msg = f"Failed to apply migration {name}: {e}"
                        logger.error(error_msg)
                        raise DatabaseError(error_msg) from e
                    
        except Exception as e:
            error_msg = f"Failed to run migrations: {e}"
            logger.error(error_msg)
            raise DatabaseError(error_msg) from e

    async def init(self) -> None:
        """Initialize the database
        
        Creates necessary tables and indexes if they don't exist.
        Must be called before any other database operations.
        
        Raises:
            DatabaseError: If initialization fails
        """
        try:
            self._pool = DatabasePool(self.db_path)
            
            # Use connection with timeout
            conn = await self._connect_with_timeout(self.db_path)
            try:
                # Enable foreign key support
                await conn.execute("PRAGMA foreign_keys = ON")
                
                # Run any pending migrations
                await self._run_migrations(conn)
                
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
                    ticket_type TEXT NOT NULL,
                    status TEXT DEFAULT 'open',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    closed_at DATETIME,
                    last_activity DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(guild_id) REFERENCES guilds(id) ON DELETE CASCADE
                );
                CREATE INDEX IF NOT EXISTS idx_tickets_guild_user ON tickets(guild_id, user_id);
                CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets(status);
                
                -- Ticket messages table
                CREATE TABLE IF NOT EXISTS ticket_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticket_id INTEGER NOT NULL,
                    user_id TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(ticket_id) REFERENCES tickets(id) ON DELETE CASCADE
                );
                CREATE INDEX IF NOT EXISTS idx_ticket_messages_ticket ON ticket_messages(ticket_id);

                -- User warnings table
                CREATE TABLE IF NOT EXISTS warnings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    moderator_id TEXT NOT NULL,
                    reason TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    expires_at DATETIME,
                    active BOOLEAN DEFAULT 1,
                    FOREIGN KEY(guild_id) REFERENCES guilds(id) ON DELETE CASCADE
                );
                CREATE INDEX IF NOT EXISTS idx_warnings_guild_user ON warnings(guild_id, user_id);
                CREATE INDEX IF NOT EXISTS idx_warnings_active ON warnings(active);

                -- User roles tracking table
                CREATE TABLE IF NOT EXISTS user_roles (
                    guild_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    role_id TEXT NOT NULL,
                    assigned_by TEXT NOT NULL,
                    assigned_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (guild_id, user_id, role_id),
                    FOREIGN KEY(guild_id) REFERENCES guilds(id) ON DELETE CASCADE
                );
                CREATE INDEX IF NOT EXISTS idx_user_roles_guild ON user_roles(guild_id);

                -- Command usage tracking table
                CREATE TABLE IF NOT EXISTS command_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    command_name TEXT NOT NULL,
                    used_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    success BOOLEAN DEFAULT 1,
                    error_message TEXT,
                    FOREIGN KEY(guild_id) REFERENCES guilds(id) ON DELETE CASCADE
                );
                CREATE INDEX IF NOT EXISTS idx_command_usage_guild ON command_usage(guild_id);
                CREATE INDEX IF NOT EXISTS idx_command_usage_user ON command_usage(user_id);

                -- Security settings table
                CREATE TABLE IF NOT EXISTS security_settings (
                    guild_id TEXT PRIMARY KEY,
                    settings TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(guild_id) REFERENCES guilds(id) ON DELETE CASCADE
                );

                -- Blacklisted words table
                CREATE TABLE IF NOT EXISTS blacklisted_words (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id TEXT NOT NULL,
                    word TEXT NOT NULL,
                    added_by TEXT NOT NULL,
                    added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(guild_id) REFERENCES guilds(id) ON DELETE CASCADE,
                    UNIQUE(guild_id, word)
                );
                CREATE INDEX IF NOT EXISTS idx_blacklisted_words_guild ON blacklisted_words(guild_id);
                """)
                await conn.commit()
            finally:
                await conn.close()
                
        except Exception as e:
            error_msg = f"Failed to initialize database: {e}"
            logger.error(f"{error_msg}\n{traceback.format_exc()}")
            raise DatabaseError(error_msg) from e

    @asynccontextmanager
    async def transaction(self) -> AsyncGenerator[aiosqlite.Cursor, None]:
        """Context manager for database transactions
        
        Provides a cursor for executing SQL statements within a transaction.
        Automatically handles commit/rollback.
        
        Yields:
            Database cursor for executing queries
            
        Raises:
            RuntimeError: If database is not initialized
            TransactionError: If transaction operations fail
            ConnectionError: If connection fails
        """
        if not self._pool:
            raise RuntimeError("Database not initialized")
            
        try:
            async with self._pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await conn.execute("BEGIN")
                    try:
                        yield cursor
                        await conn.commit()
                    except Exception as e:
                        await conn.rollback()
                        error_msg = f"Transaction failed: {e}"
                        logger.error(f"{error_msg}\n{traceback.format_exc()}")
                        raise TransactionError(error_msg) from e
        except ConnectionError as e:
            raise ConnectionError(f"Failed to acquire database connection: {e}") from e
        except Exception as e:
            error_msg = f"Unexpected database error: {e}"
            logger.error(f"{error_msg}\n{traceback.format_exc()}")
            raise DatabaseError(error_msg) from e

    async def add_xp(self, guild_id: str, user_id: str, xp_amount: int) -> Optional[int]:
        """Add XP to user and return new level if leveled up
        
        Args:
            guild_id: Discord guild ID
            user_id: Discord user ID
            xp_amount: Amount of XP to add
            
        Returns:
            New level if user leveled up, None otherwise
            
        Raises:
            TransactionError: If XP update fails
            ValueError: If input parameters are invalid
        """
        # Validate input
        if not guild_id or not user_id:
            raise ValueError("Guild ID and User ID must be provided")
        if xp_amount < 0:
            raise ValueError("XP amount must be non-negative")
            
        try:
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
                    logger.info(f"User {user_id} in guild {guild_id} leveled up to {new_level}")
                    return new_level
                return None
                
        except TransactionError as e:
            error_msg = f"Failed to update XP for user {user_id} in guild {guild_id}: {e}"
            logger.error(error_msg)
            raise TransactionError(error_msg) from e

    @staticmethod
    def calculate_level(xp: int) -> int:
        """Calculate level from XP amount
        
        Args:
            xp: Current XP amount
            
        Returns:
            Calculated level based on XP
        """
        # Simple level calculation: level = xp/100
        return xp // 100

    async def get_stats(self) -> Dict[str, Any]:
        """Get database statistics
        
        Returns:
            Dictionary containing database statistics
            
        Raises:
            DatabaseError: If stats collection fails
        """
        try:
            async with self.transaction() as cursor:
                stats = {}
                
                # Get table row counts
                for table in ['guilds', 'user_levels', 'tickets', 'warnings', 'custom_commands']:
                    await cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    result = await cursor.fetchone()
                    stats[f"{table}_count"] = result[0] if result else 0
                
                # Get database size
                await cursor.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
                result = await cursor.fetchone()
                stats['database_size'] = result[0] if result else 0
                
                # Get index statistics
                await cursor.execute("SELECT * FROM pragma_index_list('user_levels')")
                stats['index_count'] = len(await cursor.fetchall())
                
                return stats
                
        except Exception as e:
            error_msg = f"Failed to get database stats: {e}"
            logger.error(error_msg)
            raise DatabaseError(error_msg) from e

    async def vacuum(self) -> None:
        """Vacuum the database to optimize storage
        
        This operation can take a while for large databases.
        
        Raises:
            DatabaseError: If vacuum fails
        """
        try:
            async with self._pool.acquire() as conn:
                await conn.execute("VACUUM")
                logger.info("Database vacuum completed successfully")
        except Exception as e:
            error_msg = f"Failed to vacuum database: {e}"
            logger.error(error_msg)
            raise DatabaseError(error_msg) from e

    async def close(self) -> None:
        """Close all database connections
        
        Should be called when shutting down the bot to ensure clean cleanup.
        """
        if self._pool:
            await self._pool.close_all()
            self._pool = None

    @staticmethod
    async def _connect_with_timeout(db_path: str, timeout: float = 30.0) -> aiosqlite.Connection:
        """Connect to database with timeout
        
        Args:
            db_path: Path to database file
            timeout: Connection timeout in seconds
            
        Returns:
            Database connection
            
        Raises:
            ConnectionError: If connection times out or fails
        """
        try:
            async with asyncio.timeout(timeout):
                return await aiosqlite.connect(db_path)
        except asyncio.TimeoutError:
            raise ConnectionError(f"Database connection timed out after {timeout} seconds")
        except Exception as e:
            raise ConnectionError(f"Failed to connect to database: {e}")

# Global database instance
db = Database()
