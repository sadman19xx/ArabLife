import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional, Union, cast
from aiohttp import web
import psutil
import discord
from config import Config

logger = logging.getLogger('discord')

class HealthCheckError(Exception):
    """Base exception for health check errors"""
    pass

class MetricsError(Exception):
    """Exception for metrics collection errors"""
    pass

class HealthCheck:
    """Health check server for the bot
    
    Provides HTTP endpoints for monitoring bot health and metrics.
    
    Attributes:
        bot: Discord bot instance
        start_time: Server start timestamp
        app: aiohttp web application
        _runner: Application runner
        _last_metrics_time: Last metrics request timestamp
        _metrics_cooldown: Cooldown between metrics requests
    """
    
    def __init__(self, bot: discord.Client, host: str = '0.0.0.0', port: int = 0, metrics_cooldown: float = 5.0) -> None:
        self.bot = bot
        self.host = host
        self.port = port
        self.start_time = time.time()
        self.app = web.Application()
        self.app.router.add_get('/health', self.health_check)
        self.app.router.add_get('/metrics', self.metrics)
        self._runner: Optional[web.AppRunner] = None
        self._last_metrics_time: float = 0
        self._metrics_cooldown: float = metrics_cooldown
        self._lock = asyncio.Lock()

    async def check_system_resources(self) -> Dict[str, Any]:
        """Check system resource usage
        
        Returns:
            Dictionary containing system metrics
            
        Raises:
            HealthCheckError: If resource check fails
        """
        try:
            return {
                "cpu_percent": psutil.cpu_percent(interval=0.1),
                "memory": {
                    "total": psutil.virtual_memory().total,
                    "available": psutil.virtual_memory().available,
                    "percent": psutil.virtual_memory().percent
                },
                "disk": {
                    "total": psutil.disk_usage('/').total,
                    "free": psutil.disk_usage('/').free,
                    "percent": psutil.disk_usage('/').percent
                }
            }
        except Exception as e:
            error_msg = f"Failed to check system resources: {e}"
            logger.error(error_msg)
            raise HealthCheckError(error_msg) from e

    @staticmethod
    async def _find_available_port(start_port: int = 8080, max_attempts: int = 10) -> int:
        """Find an available port starting from start_port
        
        Args:
            start_port: Port to start checking from
            max_attempts: Maximum number of ports to try
            
        Returns:
            Available port number
            
        Raises:
            HealthCheckError: If no available port is found
        """
        import socket
        
        for port in range(start_port, start_port + max_attempts):
            try:
                # Check if port is in use
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('0.0.0.0', port))
                    return port
            except OSError:
                continue
                
        raise HealthCheckError(f"No available ports found between {start_port} and {start_port + max_attempts - 1}")

    async def start(self) -> None:
        """Start the health check server
        
        Raises:
            HealthCheckError: If server fails to start
        """
        try:
            # If port is 0, find an available port
            if self.port == 0:
                try:
                    self.port = await self._find_available_port()
                except Exception as e:
                    raise HealthCheckError(f"Failed to find available port: {e}")
            
            runner = web.AppRunner(self.app)
            await runner.setup()
            self._runner = runner
            
            try:
                site = web.TCPSite(runner, self.host, self.port)
                await site.start()
                logger.info(f"Health check server started on {self.host}:{self.port}")
            except OSError as e:
                if e.errno == 98:  # Address already in use
                    # Try to find another port
                    try:
                        self.port = await self._find_available_port(self.port + 1)
                        site = web.TCPSite(runner, self.host, self.port)
                        await site.start()
                        logger.info(f"Health check server started on alternate port {self.host}:{self.port}")
                    except Exception as e2:
                        raise HealthCheckError(f"Failed to start on alternate port: {e2}")
                else:
                    raise
                    
        except Exception as e:
            error_msg = f"Failed to start health check server: {e}"
            logger.error(error_msg)
            if self._runner:
                await self._runner.cleanup()
                self._runner = None
            raise HealthCheckError(error_msg) from e

    async def stop(self) -> None:
        """Stop the health check server
        
        Ensures clean shutdown of the web server.
        """
        if self._runner:
            await self._runner.cleanup()
            self._runner = None
            logger.info("Health check server stopped")

    async def health_check(self, request: web.Request) -> web.Response:
        """Handle health check requests
        
        Performs various health checks including:
        - Discord connection status
        - Database connectivity
        - Memory usage
        - CPU usage
        
        Returns:
            HTTP response with health status
        """
        try:
            # Check Discord connection
            if not self.bot.is_ready():
                return web.Response(
                    status=503,
                    text="Bot not ready"
                )
            
            # Check database connection
            try:
                async with self.bot.db.transaction() as cursor:
                    await cursor.execute("SELECT 1")
            except Exception as e:
                logger.error(f"Database health check failed: {e}")
                return web.Response(
                    status=503,
                    text="Database connection failed"
                )
            
            # All checks passed
            return web.Response(
                status=200,
                text="OK"
            )
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return web.Response(
                status=500,
                text=f"Health check error: {str(e)}"
            )

    async def metrics(self, request: web.Request) -> web.Response:
        """Handle metrics requests
        
        Collects and returns various metrics about the bot and system.
        Rate limited to prevent excessive resource usage.
        
        Returns:
            JSON response with metrics data
        """
        try:
            # Check rate limit
            now = time.time()
            if now - self._last_metrics_time < self._metrics_cooldown:
                return web.Response(
                    status=429,
                    text=f"Rate limited. Try again in {self._metrics_cooldown - (now - self._last_metrics_time):.1f}s"
                )
            
            async with self._lock:
                # Get system metrics
                system_metrics = await self.check_system_resources()
                
                metrics = {
                        # Bot metrics
                        "uptime": time.time() - self.start_time,
                        "uptime_formatted": self.format_uptime(time.time() - self.start_time),
                        "guilds": len(self.bot.guilds),
                        "users": sum(g.member_count for g in self.bot.guilds),
                        "latency": round(self.bot.latency * 1000, 2),  # in ms
                        
                        # System metrics
                        **system_metrics,
                        
                        # Cache metrics
                        "cached_tickets": len(cast(Any, self.bot.get_cog("TicketCommands")).active_tickets) if self.bot.get_cog("TicketCommands") else 0,
                        "cached_prefixes": len(self.bot.prefixes),
                        
                        # Command metrics
                        "commands_used": self.bot.command_stats if hasattr(self.bot, 'command_stats') else {},
                        
                        # Error metrics
                        "error_count": self.bot.error_count if hasattr(self.bot, 'error_count') else 0,
                        
                        # Timestamp
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    
                self._last_metrics_time = now
                return web.json_response(metrics)
            
        except (MetricsError, HealthCheckError) as e:
            return web.Response(
                status=500,
                text=str(e)
            )
        except Exception as e:
            error_msg = f"Unexpected error in metrics collection: {e}"
            logger.error(error_msg)
            return web.Response(
                status=500,
                text=error_msg
            )

    @staticmethod
    def format_uptime(seconds: float) -> str:
        """Format uptime into human readable string
        
        Args:
            seconds: Number of seconds
            
        Returns:
            Formatted string like "5d 3h 2m 1s"
        """
        minutes, seconds = divmod(int(seconds), 60)
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)
        
        parts = []
        if days > 0:
            parts.append(f"{days}d")
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0:
            parts.append(f"{minutes}m")
        if seconds > 0 or not parts:
            parts.append(f"{seconds}s")
            
        return " ".join(parts)
