Fahad, a beacon shining bright,
Strength and kindness in your light.
```

# ArabLife Bot
*Developed by Fahad and Sadman*

## Quick Start Guide
Follow the [Basic Setup Guide](README_BASIC.md) first for Python, FFmpeg, and core bot setup.

## Security Features

1. **Anti-Raid Protection**
   - Automatic raid detection (10 joins/30 seconds)
   - Auto-enables highest verification level
   - Auto-disables after 10 minutes
   - New account detection (< 7 days)

2. **Spam Detection**
   - Message frequency monitoring
   - Similar message detection
   - Mass mention protection
   - Configurable thresholds
   - Automatic warnings

3. **Link Control**
   - Configurable allowed domains
   - Discord invite filtering
   - URL scanning
   - Automatic removal

4. **Warning System**
   - Progressive warnings
   - Automatic timeouts
   - Warning history
   - Admin commands:
     - `/warnings @user` - Check warnings
     - `/clearwarnings @user` - Clear warnings

5. **Configurable Settings**
```env
# Security Settings
MAX_MENTIONS=5
RAID_PROTECTION=true
MIN_ACCOUNT_AGE=7
ALLOWED_DOMAINS=discord.com,discord.gg
SPAM_DETECTION=true
AUTO_TIMEOUT_DURATION=3600
BLACKLISTED_WORDS=word1,word2,word3
```

## Other Features

### Role Management
- `/مقبول @user` - Give role
- `/مرفوض @user` - Remove role

### Voice System
- `/testsound` - Test welcome sound
- `/volume 0.5` - Adjust volume

### Ticket System
- `/setup-tickets` - Create ticket panel
- `/close` - Close current ticket

### Help
- `/help` - Show all commands

## Logging

All security events are logged to your audit channel:
- Raid detections
- Spam warnings
- Link removals
- User timeouts
- Warning changes

## Security Best Practices

1. **Server Settings**
   - Enable 2FA requirement for moderation
   - Set up role hierarchy properly
   - Configure verification level
   - Set up explicit content filter

2. **Bot Permissions**
   - Use minimal required permissions
   - Set up proper role hierarchy
   - Configure audit logging
   - Enable member intents

3. **Monitoring**
   - Check audit logs regularly
   - Review warning patterns
   - Monitor raid attempts
   - Track spam incidents

4. **Maintenance**
   - Update allowed domains regularly
   - Review blacklisted words
   - Adjust thresholds as needed
   - Clear old warnings periodically

---
*Bot developed and maintained by Fahad and Sadman*
