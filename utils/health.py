import asyncio
import logging
from aiohttp import web
from typing import Dict, Any
import psutil
import time

logger = logging.getLogger('discord')

class HealthCheck:
    """Health check server for the bot"""
    
    def __init__(self, bot):
        self.bot = bot
        self.start_time = time.time()
        self.app = web.Application()
        self.app.router.add_get('/health', self.health_check)
        self.app.router.add_get('/metrics', self.metrics)
        self._runner = None
        
    async def start(self):
        """Start the health check server"""
        try:
            runner = web.AppRunner(self.app)
            await runner.setup()
            self._runner = runner
            site = web.TCPSite(runner, '0.0.0.0', 8080)
            await site.start()
            logger.info("Health check server started on port 8080")
        except Exception as e:
            logger.error(f"Failed to start health check server: {e}")
            raise

    async def stop(self):
        """Stop the health check server"""
        if self._runner:
            await self._runner.cleanup()
            self._runner = None
            logger.info("Health check server stopped")

    async def health_check(self, request: web.Request) -> web.Response:
        """Handle health check requests"""
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
        """Handle metrics requests"""
        try:
            metrics = {
                # Bot metrics
                "uptime": time.time() - self.start_time,
                "guilds": len(self.bot.guilds),
                "users": sum(g.member_count for g in self.bot.guilds),
                "latency": round(self.bot.latency * 1000, 2),  # in ms
                
                # System metrics
                "cpu_percent": psutil.cpu_percent(),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage('/').percent,
                
                # Cache metrics
                "cached_tickets": len(self.bot.get_cog("TicketCommands").active_tickets),
                "cached_prefixes": len(self.bot.prefixes),
                
                # Command metrics
                "commands_used": self.bot.command_stats if hasattr(self.bot, 'command_stats') else {},
                
                # Error metrics
                "error_count": self.bot.error_count if hasattr(self.bot, 'error_count') else 0
            }
            
            return web.json_response(metrics)
            
        except Exception as e:
            logger.error(f"Metrics collection failed: {e}")
            return web.Response(
                status=500,
                text=f"Metrics error: {str(e)}"
            )

    @staticmethod
    def format_uptime(seconds: float) -> str:
        """Format uptime into human readable string"""
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
