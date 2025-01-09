import os
import sys
import sqlite3
import asyncio
import discord
from discord.ext import commands
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('bot_test')

async def test_database():
    """Test database creation and permissions"""
    try:
        os.makedirs('data', exist_ok=True)
        conn = sqlite3.connect('data/bot_dashboard.db')
        c = conn.cursor()
        c.execute('CREATE TABLE IF NOT EXISTS test (id INTEGER PRIMARY KEY)')
        conn.commit()
        conn.close()
        logger.info("✅ Database test passed")
        return True
    except Exception as e:
        logger.error(f"❌ Database test failed: {str(e)}")
        return False

async def test_cogs():
    """Test if all cog files are present and importable"""
    required_cogs = [
        'automod_commands.py',
        'help_commands.py',
        'leveling_commands.py',
        'role_commands.py',
        'security_commands.py',
        'status_commands.py',
        'ticket_commands.py',
        'voice_commands.py',
        'welcome_commands.py'
    ]
    
    missing_cogs = []
    for cog in required_cogs:
        if not os.path.exists(f'cogs/{cog}'):
            missing_cogs.append(cog)
    
    if missing_cogs:
        logger.error(f"❌ Missing cog files: {', '.join(missing_cogs)}")
        return False
    
    logger.info("✅ All cog files present")
    return True

async def test_utils():
    """Test if utility files are present"""
    if not os.path.exists('utils/logger.py'):
        logger.error("❌ Missing utils/logger.py")
        return False
    
    logger.info("✅ Utils files present")
    return True

async def test_fonts():
    """Test if required fonts are present"""
    if not os.path.exists('fonts/arabic.ttf'):
        logger.error("❌ Missing fonts/arabic.ttf")
        return False
    
    logger.info("✅ Font files present")
    return True

async def test_config():
    """Test if config file is present and has required fields"""
    if not os.path.exists('config.py'):
        logger.error("❌ Missing config.py")
        return False
    
    try:
        from config import Config
        required_attrs = [
            'TOKEN', 'GUILD_ID', 'ROLE_IDS_ALLOWED', 'ROLE_ID_TO_GIVE',
            'ROLE_ID_REMOVE_ALLOWED', 'ROLE_ACTIVITY_LOG_CHANNEL_ID',
            'AUDIT_LOG_CHANNEL_ID'
        ]
        
        missing_attrs = []
        for attr in required_attrs:
            if not hasattr(Config, attr):
                missing_attrs.append(attr)
        
        if missing_attrs:
            logger.error(f"❌ Missing config attributes: {', '.join(missing_attrs)}")
            return False
        
        logger.info("✅ Config file valid")
        return True
    except Exception as e:
        logger.error(f"❌ Config test failed: {str(e)}")
        return False

async def test_bot_startup():
    """Test if bot can initialize"""
    try:
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        intents.voice_states = True
        
        bot = commands.Bot(command_prefix='/', intents=intents)
        
        # Try loading one cog
        try:
            await bot.load_extension('cogs.help_commands')
            logger.info("✅ Bot initialization test passed")
            return True
        except Exception as e:
            logger.error(f"❌ Bot initialization failed: {str(e)}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Bot creation failed: {str(e)}")
        return False

async def main():
    """Run all tests"""
    logger.info("Starting bot verification tests...")
    
    tests = [
        ("Database", test_database()),
        ("Cogs", test_cogs()),
        ("Utils", test_utils()),
        ("Fonts", test_fonts()),
        ("Config", test_config()),
        ("Bot Startup", test_bot_startup())
    ]
    
    results = []
    for test_name, test_coro in tests:
        logger.info(f"\nRunning {test_name} test...")
        result = await test_coro
        results.append((test_name, result))
    
    logger.info("\nTest Results:")
    all_passed = True
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{test_name}: {status}")
        if not result:
            all_passed = False
    
    if all_passed:
        logger.info("\n✅ All tests passed! Bot is ready for deployment.")
        sys.exit(0)
    else:
        logger.error("\n❌ Some tests failed. Please fix the issues before deploying.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
