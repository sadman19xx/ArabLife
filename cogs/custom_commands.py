import discord
from discord.ext import commands
from discord import app_commands
import logging
import json
import aiosqlite
from typing import Optional
from utils.database import db

logger = logging.getLogger('discord')

class CustomCommands(commands.Cog):
    """Cog for handling custom commands"""
    
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="addcommand",
        description="Add a custom command"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def add_command(
        self,
        interaction: discord.Interaction,
        name: str,
        response: str
    ):
        """Add a custom command"""
        try:
            # Validate command name
            if len(name) > 32:
                await interaction.response.send_message(
                    "*اسم الأمر طويل جداً. يجب أن يكون 32 حرفاً أو أقل.*",
                    ephemeral=True
                )
                return
                
            name = name.lower()
            if name in [c.name for c in self.bot.commands]:
                await interaction.response.send_message(
                    "*هذا الأمر موجود بالفعل كأمر أساسي.*",
                    ephemeral=True
                )
                return
            
            # Add command to database
            async with aiosqlite.connect(db.db_path) as conn:
                try:
                    await conn.execute("""
                        INSERT INTO custom_commands (guild_id, name, response, created_by)
                        VALUES (?, ?, ?, ?)
                    """, (str(interaction.guild_id), name, response, str(interaction.user.id)))
                    await conn.commit()
                    
                    await interaction.response.send_message(
                        f"*تم إضافة الأمر `{name}` بنجاح.*"
                    )
                except aiosqlite.IntegrityError:
                    await interaction.response.send_message(
                        "*هذا الأمر موجود بالفعل.*",
                        ephemeral=True
                    )
                    
        except Exception as e:
            logger.error(f"Failed to add command: {str(e)}")
            await interaction.response.send_message(
                "*حدث خطأ أثناء إضافة الأمر.*",
                ephemeral=True
            )

    @app_commands.command(
        name="editcommand",
        description="Edit a custom command"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def edit_command(
        self,
        interaction: discord.Interaction,
        name: str,
        response: str
    ):
        """Edit a custom command"""
        try:
            name = name.lower()
            
            # Update command in database
            async with aiosqlite.connect(db.db_path) as conn:
                cursor = await conn.execute("""
                    UPDATE custom_commands
                    SET response = ?
                    WHERE guild_id = ? AND name = ?
                """, (response, str(interaction.guild_id), name))
                await conn.commit()
                
                if cursor.rowcount == 0:
                    await interaction.response.send_message(
                        "*لم يتم العثور على الأمر.*",
                        ephemeral=True
                    )
                else:
                    await interaction.response.send_message(
                        f"*تم تحديث الأمر `{name}` بنجاح.*"
                    )
                    
        except Exception as e:
            logger.error(f"Failed to edit command: {str(e)}")
            await interaction.response.send_message(
                "*حدث خطأ أثناء تحديث الأمر.*",
                ephemeral=True
            )

    @app_commands.command(
        name="removecommand",
        description="Remove a custom command"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def remove_command(
        self,
        interaction: discord.Interaction,
        name: str
    ):
        """Remove a custom command"""
        try:
            name = name.lower()
            
            # Remove command from database
            async with aiosqlite.connect(db.db_path) as conn:
                cursor = await conn.execute("""
                    DELETE FROM custom_commands
                    WHERE guild_id = ? AND name = ?
                """, (str(interaction.guild_id), name))
                await conn.commit()
                
                if cursor.rowcount == 0:
                    await interaction.response.send_message(
                        "*لم يتم العثور على الأمر.*",
                        ephemeral=True
                    )
                else:
                    await interaction.response.send_message(
                        f"*تم حذف الأمر `{name}` بنجاح.*"
                    )
                    
        except Exception as e:
            logger.error(f"Failed to remove command: {str(e)}")
            await interaction.response.send_message(
                "*حدث خطأ أثناء حذف الأمر.*",
                ephemeral=True
            )

    @app_commands.command(
        name="listcommands",
        description="List all custom commands"
    )
    async def list_commands(self, interaction: discord.Interaction):
        """List all custom commands"""
        try:
            async with aiosqlite.connect(db.db_path) as conn:
                async with conn.execute("""
                    SELECT name, response
                    FROM custom_commands
                    WHERE guild_id = ?
                    ORDER BY name
                """, (str(interaction.guild_id),)) as cursor:
                    commands = await cursor.fetchall()
            
            if not commands:
                await interaction.response.send_message(
                    "*لا توجد أوامر مخصصة.*",
                    ephemeral=True
                )
                return
                
            # Create embed with command list
            embed = discord.Embed(
                title="الأوامر المخصصة",
                color=discord.Color.blue()
            )
            
            # Add commands to embed in chunks to avoid hitting character limits
            current_field = ""
            for name, response in commands:
                command_text = f"`{name}`: {response[:50]}{'...' if len(response) > 50 else ''}\n"
                
                if len(current_field) + len(command_text) > 1024:
                    embed.add_field(
                        name="‎",  # Zero-width space
                        value=current_field,
                        inline=False
                    )
                    current_field = command_text
                else:
                    current_field += command_text
            
            if current_field:
                embed.add_field(
                    name="‎",  # Zero-width space
                    value=current_field,
                    inline=False
                )
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            logger.error(f"Failed to list commands: {str(e)}")
            await interaction.response.send_message(
                "*حدث خطأ أثناء عرض الأوامر.*",
                ephemeral=True
            )

    @app_commands.command(
        name="commandinfo",
        description="Get information about a custom command"
    )
    async def command_info(
        self,
        interaction: discord.Interaction,
        name: str
    ):
        """Get information about a custom command"""
        try:
            name = name.lower()
            
            async with aiosqlite.connect(db.db_path) as conn:
                conn.row_factory = aiosqlite.Row
                async with conn.execute("""
                    SELECT name, response, created_by, created_at
                    FROM custom_commands
                    WHERE guild_id = ? AND name = ?
                """, (str(interaction.guild_id), name)) as cursor:
                    command = await cursor.fetchone()
            
            if not command:
                await interaction.response.send_message(
                    "*لم يتم العثور على الأمر.*",
                    ephemeral=True
                )
                return
                
            # Create embed with command info
            embed = discord.Embed(
                title=f"معلومات الأمر: {command['name']}",
                color=discord.Color.blue()
            )
            
            # Add creator info
            creator = interaction.guild.get_member(int(command['created_by']))
            creator_name = creator.display_name if creator else "Unknown"
            
            embed.add_field(
                name="الاستجابة",
                value=command['response'],
                inline=False
            )
            embed.add_field(
                name="تم إنشاؤه بواسطة",
                value=creator_name,
                inline=True
            )
            embed.add_field(
                name="تاريخ الإنشاء",
                value=command['created_at'].split('.')[0].replace('T', ' '),
                inline=True
            )
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            logger.error(f"Failed to get command info: {str(e)}")
            await interaction.response.send_message(
                "*حدث خطأ أثناء عرض معلومات الأمر.*",
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(CustomCommands(bot))
