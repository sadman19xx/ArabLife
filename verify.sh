#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check system dependencies
echo -e "${YELLOW}Checking system dependencies...${NC}"
DEPS=("python3" "pip" "git" "ffmpeg" "screen")
MISSING_DEPS=()

for dep in "${DEPS[@]}"; do
    if ! command_exists "$dep"; then
        MISSING_DEPS+=("$dep")
    fi
done

if [ ${#MISSING_DEPS[@]} -eq 0 ]; then
    echo -e "${GREEN}✓ All system dependencies are installed${NC}"
else
    echo -e "${RED}✗ Missing dependencies: ${MISSING_DEPS[*]}${NC}"
fi

# Check Python environment
echo -e "\n${YELLOW}Checking Python environment...${NC}"
if [ -d "venv" ]; then
    echo -e "${GREEN}✓ Virtual environment exists${NC}"
    source venv/bin/activate
    if pip freeze | grep -q "discord.py"; then
        echo -e "${GREEN}✓ Discord.py is installed${NC}"
    else
        echo -e "${RED}✗ Discord.py is not installed${NC}"
    fi
else
    echo -e "${RED}✗ Virtual environment not found${NC}"
fi

# Check configuration
echo -e "\n${YELLOW}Checking configuration...${NC}"
if [ -f ".env" ]; then
    echo -e "${GREEN}✓ .env file exists${NC}"
    # Check required variables without displaying values
    REQUIRED_VARS=("TOKEN" "GUILD_ID" "ROLE_IDS_ALLOWED" "ROLE_ID_TO_GIVE" "ROLE_ID_REMOVE_ALLOWED" "ROLE_ACTIVITY_LOG_CHANNEL_ID" "AUDIT_LOG_CHANNEL_ID" "VISA_IMAGE_URL")
    MISSING_VARS=()
    
    for var in "${REQUIRED_VARS[@]}"; do
        if ! grep -q "^${var}=" .env; then
            MISSING_VARS+=("$var")
        fi
    done
    
    if [ ${#MISSING_VARS[@]} -eq 0 ]; then
        echo -e "${GREEN}✓ All required environment variables are set${NC}"
    else
        echo -e "${RED}✗ Missing environment variables: ${MISSING_VARS[*]}${NC}"
    fi
else
    echo -e "${RED}✗ .env file not found${NC}"
fi

# Check bot files
echo -e "\n${YELLOW}Checking bot files...${NC}"
REQUIRED_FILES=("bot.py" "config.py" "start.sh")
MISSING_FILES=()

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓ $file exists${NC}"
    else
        MISSING_FILES+=("$file")
    fi
done

if [ ${#MISSING_FILES[@]} -ne 0 ]; then
    echo -e "${RED}✗ Missing files: ${MISSING_FILES[*]}${NC}"
fi

# Check cogs
echo -e "\n${YELLOW}Checking cogs...${NC}"
if [ -d "cogs" ]; then
    echo -e "${GREEN}✓ Cogs directory exists${NC}"
    COGS_COUNT=$(ls -1 cogs/*.py 2>/dev/null | wc -l)
    echo -e "${GREEN}✓ Found $COGS_COUNT cog files${NC}"
else
    echo -e "${RED}✗ Cogs directory not found${NC}"
fi

# Check screen session
echo -e "\n${YELLOW}Checking bot status...${NC}"
if screen -list | grep -q "arablife"; then
    echo -e "${GREEN}✓ Bot is currently running${NC}"
else
    echo -e "${YELLOW}! Bot is not running${NC}"
fi

echo -e "\n${YELLOW}Verification complete!${NC}"
