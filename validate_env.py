#!/usr/bin/env python3
import os
import sys
from dotenv import load_dotenv

def validate_env():
    """Validate environment variables"""
    load_dotenv()
    
    missing = []
    
    # Required variables
    required_vars = {
        'TOKEN': 'Bot token from Discord Developer Portal -> Bot -> Token',
        'GUILD_ID': 'Server ID (Enable Developer Mode -> Right click server -> Copy ID)',
        'APPLICATION_ID': 'Application ID from Discord Developer Portal -> General Information -> Application ID'
    }
    
    # Check required variables
    for var, desc in required_vars.items():
        if not os.getenv(var):
            missing.append(f"{var} - {desc}")
    
    # Optional variables with defaults
    optional_vars = {
        'WELCOME_VOICE_CHANNEL_ID': '1309595750878937240',
        'WELCOME_SOUND_PATH': 'welcome.mp3',
        'DEFAULT_VOLUME': '0.5',
        'AUTOMOD_ENABLED': '1',
        'AUTOMOD_ACTION': 'warn',
        'AUTOMOD_SPAM_THRESHOLD': '5',
        'AUTOMOD_SPAM_INTERVAL': '5',
        'AUTOMOD_RAID_THRESHOLD': '10',
        'AUTOMOD_RAID_INTERVAL': '10',
        'XP_PER_MESSAGE': '15',
        'XP_COOLDOWN': '60',
        'HEALTH_CHECK_HOST': '127.0.0.1',
        'HEALTH_CHECK_PORT': '8080',
        'HEALTH_CHECK_METRICS_COOLDOWN': '60'
    }
    
    # Print current configuration
    print("\nCurrent Configuration:")
    print("=====================")
    
    # Print required variables
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Mask token
            if var == 'TOKEN':
                masked = value[:10] + '*' * (len(value) - 10)
                print(f"{var}: {masked}")
            else:
                print(f"{var}: {value}")
        else:
            print(f"{var}: Not set")
    
    # Print optional variables
    print("\nOptional Settings:")
    print("=================")
    for var, default in optional_vars.items():
        value = os.getenv(var, default)
        print(f"{var}: {value}")
    
    # Report missing required variables
    if missing:
        print("\nMissing Required Variables:")
        print("==========================")
        for var in missing:
            print(f"❌ {var}")
        print("\nHow to fix:")
        print("1. Copy .env.example to .env")
        print("2. Fill in the missing values in .env")
        print("3. For the Application ID:")
        print("   - Go to Discord Developer Portal (https://discord.com/developers/applications)")
        print("   - Select your bot application")
        print("   - Copy the Application ID from General Information")
        print("4. Run this script again to verify")
        sys.exit(1)
    else:
        print("\n✅ All required variables are set!")
        
        # Check optional files
        print("\nChecking Optional Files:")
        print("=======================")
        
        # Check welcome sound
        welcome_sound = os.getenv('WELCOME_SOUND_PATH', 'welcome.mp3')
        if os.path.exists(welcome_sound):
            print(f"✅ Welcome sound found: {welcome_sound}")
        else:
            print(f"⚠️  Welcome sound not found: {welcome_sound}")
            print("   Voice welcome features will not work until you add this file")
        
        # Check Arabic font
        font_path = os.path.join('fonts', 'arabic.ttf')
        if os.path.exists(font_path):
            print(f"✅ Arabic font found: {font_path}")
        else:
            print(f"⚠️  Arabic font not found: {font_path}")
            print("   Arabic text rendering will not work until you add this file")

if __name__ == '__main__':
    validate_env()
