import discord
from discord.ext import commands
from discord import app_commands
from discord.ext.commands import Cog
import logging
from aiohttp import web
import asyncio
from typing import Optional
from config import Config

class FiveMCommands(Cog):
    """Cog for FiveM integration and whitelist management"""
    
    def __init__(self, bot):
        self.bot = bot
        self.web_app = web.Application()
        self.web_app.router.add_get('/api/roles/{discord_id}', self.handle_role_check)
        self.runner = web.AppRunner(self.web_app)
        self.site = None
        # Start web server
        asyncio.create_task(self.start_server())
        
    async def start_server(self):
        """Start the web server for FiveM integration"""
        try:
            await self.runner.setup()
            self.site = web.TCPSite(self.runner, '127.0.0.1', 3033)
            await self.site.start()
            print(f"FiveM integration API running on http://127.0.0.1:3033")
        except Exception as e:
            logging.error(f"Failed to start FiveM integration API: {e}")

    async def handle_role_check(self, request):
        """Handle role check requests from FiveM server"""
        try:
            discord_id = request.match_info['discord_id']
            # Extract pure Discord ID if it contains FiveM identifier
            if ":" in discord_id:
                discord_id = discord_id.split(":")[1]
                
            # Get guild from config
            guild = self.bot.get_guild(Config.GUILD_ID)
            if not guild:
                return web.json_response({"error": "Guild not found"}, status=404)
                
            # Get member
            member = await guild.fetch_member(int(discord_id))
            if not member:
                return web.json_response({"error": "Member not found"}, status=404)
                
            # Get member roles
            roles = [str(role.id) for role in member.roles]
            
            return web.json_response({
                "roles": roles,
                "name": member.display_name,
                "id": str(member.id)
            })
            
        except discord.NotFound:
            return web.json_response({"error": "Member not found"}, status=404)
        except discord.Forbidden:
            return web.json_response({"error": "Missing permissions"}, status=403)
        except Exception as e:
            logging.error(f"Error checking roles: {e}")
            return web.json_response({"error": "Internal server error"}, status=500)

    @app_commands.command(
        name="whitelist",
        description="Add or remove a user from the FiveM whitelist"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def whitelist(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        action: str
    ):
        """Manage FiveM whitelist through Discord"""
        whitelist_role = discord.utils.get(interaction.guild.roles, id=1309555494586683474)
        if not whitelist_role:
            await interaction.response.send_message(
                "*دور القائمة البيضاء غير موجود.*",
                ephemeral=True
            )
            return
            
        if action.lower() == "add":
            if whitelist_role in member.roles:
                await interaction.response.send_message(
                    f"*{member.mention} موجود بالفعل في القائمة البيضاء.*",
                    ephemeral=True
                )
                return
                
            await member.add_roles(whitelist_role)
            await interaction.response.send_message(
                f"*تمت إضافة {member.mention} إلى القائمة البيضاء.*"
            )
            
        elif action.lower() == "remove":
            if whitelist_role not in member.roles:
                await interaction.response.send_message(
                    f"*{member.mention} ليس في القائمة البيضاء.*",
                    ephemeral=True
                )
                return
                
            await member.remove_roles(whitelist_role)
            await interaction.response.send_message(
                f"*تمت إزالة {member.mention} من القائمة البيضاء.*"
            )
            
        else:
            await interaction.response.send_message(
                "*إجراء غير صالح. استخدم 'add' أو 'remove'.*",
                ephemeral=True
            )

    async def cog_unload(self):
        """Cleanup when cog is unloaded"""
        if self.site:
            await self.site.stop()
        if self.runner:
            await self.runner.cleanup()

async def setup(bot):
    """Setup function for loading the cog"""
    await bot.add_cog(FiveMCommands(bot))
