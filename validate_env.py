#!/usr/bin/env python3
import os
import sys
from dotenv import load_dotenv

def validate_id(value, name):
    """Validate that a value is a valid Discord ID"""
    try:
        if value is None:
            print(f"❌ Error: {name} is not set in .env file")
            return False
        int(value)
        return True
    except ValueError:
        print(f"❌ Error: {name} must be a number, got '{value}'")
        return False

def validate_env():
    """Validate all environment variables"""
    load_dotenv()
    
    success = True
    
    # Required IDs
    required_ids = [
        'GUILD_ID',
        'ROLE_ID_TO_GIVE',
        'ROLE_ID_REMOVE_ALLOWED',
        'ROLE_ACTIVITY_LOG_CHANNEL_ID',
        'AUDIT_LOG_CHANNEL_ID',
        'WELCOME_CHANNEL_ID',
        'TICKET_STAFF_ROLE_ID',
        'TICKET_CATEGORY_ID',
        'TICKET_LOG_CHANNEL_ID',
        'PLAYER_REPORT_ROLE_ID',
        'HEALTH_DEPT_ROLE_ID',
        'INTERIOR_DEPT_ROLE_ID',
        'FEEDBACK_ROLE_ID'
    ]
    
    # Check token
    token = os.getenv('TOKEN')
    if not token:
        print("❌ Error: Discord bot token not set in .env file")
        print("   Get your bot token from Discord Developer Portal:")
        print("   1. Go to https://discord.com/developers/applications")
        print("   2. Click on your application (or create new)")
        print("   3. Go to Bot section")
        print("   4. Click 'Reset Token' or 'Copy' under TOKEN")
        success = False
    elif len(token) < 50 or not token.strip().replace('.', '').isalnum():
        print("❌ Error: Invalid Discord bot token format")
        print("   Token should be a long string of letters, numbers, and dots")
        print("   Example format: MTIzNDU2Nzg5MDEyMzQ1Njc4.ABCDEF.ghijklmnopqrstuvwxyz123456")
        print("   Get a new token from Discord Developer Portal")
        success = False
    else:
        print("✅ Bot token format is valid")
    
    # Validate all required IDs
    for var_name in required_ids:
        value = os.getenv(var_name)
        if not validate_id(value, var_name):
            success = False
        else:
            print(f"✅ {var_name} is valid")
    
    # Validate comma-separated role IDs
    role_ids = os.getenv('ROLE_IDS_ALLOWED', '').split(',')
    if not role_ids or role_ids == ['']:
        print("❌ Error: ROLE_IDS_ALLOWED is not set in .env file")
        success = False
    else:
        valid_roles = True
        for role_id in role_ids:
            try:
                int(role_id.strip())
            except ValueError:
                print(f"❌ Error: Invalid role ID in ROLE_IDS_ALLOWED: '{role_id}'")
                valid_roles = False
                success = False
        if valid_roles:
            print("✅ ROLE_IDS_ALLOWED are valid")
    
    # Validate role rewards JSON
    role_rewards = os.getenv('ROLE_REWARDS', '{}')
    try:
        import json
        rewards = json.loads(role_rewards)
        valid_rewards = True
        for level, role_id in rewards.items():
            try:
                int(level)
                int(role_id)
            except ValueError:
                print(f"❌ Error: Invalid level or role ID in ROLE_REWARDS: Level {level} -> Role {role_id}")
                valid_rewards = False
                success = False
        if valid_rewards and rewards:
            print("✅ ROLE_REWARDS are valid")
    except json.JSONDecodeError:
        print("❌ Error: ROLE_REWARDS is not valid JSON")
        success = False
    
    # Final result
    if success:
        print("\n✅ All environment variables are valid!")
        return 0
    else:
        print("\n❌ Environment validation failed. Please fix the errors above.")
        if not token or len(token) < 50:
            print("\nℹ️  To get a valid bot token:")
            print("1. Go to https://discord.com/developers/applications")
            print("2. Select your bot (or create new)")
            print("3. Go to Bot section")
            print("4. Click 'Reset Token' or 'Copy'")
            print("5. Add the token to your .env file:")
            print("   TOKEN=your.token.here")
        return 1

if __name__ == "__main__":
    sys.exit(validate_env())
