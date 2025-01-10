# Discord Bot Setup Guide

This guide will walk you through setting up your bot on Discord and getting the necessary token and permissions.

## Step 1: Create a Discord Application

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application" in the top right
3. Enter a name for your bot (e.g., "ArabLife Bot")
4. Click "Create"

## Step 2: Create a Bot User

1. Click on "Bot" in the left sidebar
2. Click "Add Bot"
3. Confirm by clicking "Yes, do it!"
4. Under the bot's username, you'll see several options:
   - Enable "Public Bot" if you want others to invite your bot
   - Enable "Presence Intent" under "Privileged Gateway Intents"
   - Enable "Server Members Intent"
   - Enable "Message Content Intent"

## Step 3: Get Your Bot Token

1. In the "Bot" section, click "Reset Token" or "Copy" under the token section
2. Save this token - you'll need it for your .env file
   - ⚠️ IMPORTANT: Never share your token! If exposed, reset it immediately
   - The token should look like: `MTIzNDU2Nzg5MDEyMzQ1Njc4.ABCDEF.ghijklmnopqrstuvwxyz123456`

## Step 4: Set Bot Permissions

1. Click on "OAuth2" in the left sidebar
2. Click on "URL Generator"
3. In "Scopes", select:
   - [x] `bot`
   - [x] `applications.commands`

4. In "Bot Permissions", select:
   - General Permissions:
     - [x] View Channels
     - [x] Manage Channels
     - [x] Manage Roles
     - [x] View Audit Log
     - [x] Manage Webhooks
     - [x] Manage Server

   - Membership Permissions:
     - [x] Create Invite
     - [x] Change Nickname
     - [x] Manage Nicknames
     - [x] Kick Members
     - [x] Ban Members
     - [x] Moderate Members

   - Text Channel Permissions:
     - [x] Send Messages
     - [x] Send Messages in Threads
     - [x] Create Public Threads
     - [x] Create Private Threads
     - [x] Embed Links
     - [x] Attach Files
     - [x] Add Reactions
     - [x] Use External Emojis
     - [x] Use External Stickers
     - [x] Mention Everyone
     - [x] Manage Messages
     - [x] Manage Threads
     - [x] Read Message History
     - [x] Send TTS Messages
     - [x] Use Application Commands

   - Voice Channel Permissions:
     - [x] Connect
     - [x] Speak
     - [x] Stream
     - [x] Use Voice Activity
     - [x] Priority Speaker
     - [x] Mute Members
     - [x] Deafen Members
     - [x] Move Members

## Step 5: Invite Bot to Your Server

1. After selecting permissions, scroll down to find the generated URL
2. Copy the URL
3. Open the URL in a new browser tab
4. Select your server from the dropdown
5. Click "Continue"
6. Review permissions and click "Authorize"
7. Complete the CAPTCHA if prompted

## Step 6: Configure Bot Settings

1. Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

2. Edit `.env` with your bot's token:
```env
TOKEN=your_bot_token_here
```

3. Get your server (guild) ID:
   - Enable Developer Mode in Discord:
     1. Open Discord Settings
     2. Go to App Settings → Advanced
     3. Enable Developer Mode
   - Right-click your server name
   - Click "Copy ID"
   - Add to .env:
     ```env
     GUILD_ID=your_server_id_here
     ```

4. Get role IDs:
   - Right-click each role
   - Click "Copy ID"
   - Add to .env:
     ```env
     ROLE_IDS_ALLOWED=role_id1,role_id2
     ROLE_ID_TO_GIVE=role_id
     ROLE_ID_REMOVE_ALLOWED=role_id
     ```

5. Get channel IDs:
   - Right-click each channel
   - Click "Copy ID"
   - Add to .env:
     ```env
     ROLE_ACTIVITY_LOG_CHANNEL_ID=channel_id
     AUDIT_LOG_CHANNEL_ID=channel_id
     WELCOME_CHANNEL_ID=channel_id
     ```

## Step 7: Start the Bot

1. Install dependencies:
```bash
./setup.sh
```

2. Start the bot:
```bash
sudo systemctl start arablife-bot
```

3. Verify the bot is running:
```bash
sudo systemctl status arablife-bot
```

## Troubleshooting

1. If the bot token is invalid:
   - Go back to Discord Developer Portal
   - Reset the token and update .env

2. If permissions are missing:
   - Check the bot role in your server
   - Ensure it's placed higher than roles it needs to manage
   - Verify channel permissions

3. If the bot isn't responding:
   - Check the logs: `sudo journalctl -u arablife-bot -f`
   - Verify all IDs in .env are correct
   - Ensure all required intents are enabled in the Developer Portal

## Security Notes

- Never share your bot token
- Reset token if accidentally exposed
- Regularly check audit logs for unauthorized actions
- Keep bot code and dependencies updated
- Regularly backup your bot's data
