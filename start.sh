#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get the directory of the script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Function to check if screen session exists
check_screen() {
    screen -list | grep -q "arablife"
}

# Function to start the bot
start_bot() {
    echo -e "${YELLOW}Starting ArabLife bot...${NC}"
    cd "${DIR}"
    source venv/bin/activate
    screen -dmS arablife python3 bot.py
    sleep 2
    if check_screen; then
        echo -e "${GREEN}Bot started successfully in screen session 'arablife'${NC}"
        echo -e "${YELLOW}To view the bot console:${NC}"
        echo -e "1. Type: ${GREEN}screen -r arablife${NC}"
        echo -e "2. To detach from console: Press ${GREEN}Ctrl+A${NC} then ${GREEN}D${NC}"
    else
        echo -e "${RED}Failed to start bot. Check logs for errors.${NC}"
    fi
}

# Function to stop the bot
stop_bot() {
    echo -e "${YELLOW}Stopping ArabLife bot...${NC}"
    screen -S arablife -X quit 2>/dev/null || true
    echo -e "${GREEN}Bot stopped${NC}"
}

# Check command line arguments
case "$1" in
    start)
        if check_screen; then
            echo -e "${RED}Bot is already running!${NC}"
            echo -e "To view console: ${GREEN}screen -r arablife${NC}"
        else
            start_bot
        fi
        ;;
    stop)
        if check_screen; then
            stop_bot
        else
            echo -e "${RED}Bot is not running!${NC}"
        fi
        ;;
    restart)
        if check_screen; then
            stop_bot
        fi
        sleep 2
        start_bot
        ;;
    status)
        if check_screen; then
            echo -e "${GREEN}Bot is running!${NC}"
            echo -e "To view console: ${GREEN}screen -r arablife${NC}"
        else
            echo -e "${RED}Bot is not running!${NC}"
        fi
        ;;
    *)
        echo -e "Usage: $0 {start|stop|restart|status}"
        echo -e "\nCommands:"
        echo -e "  ${GREEN}start${NC}   - Start the bot"
        echo -e "  ${GREEN}stop${NC}    - Stop the bot"
        echo -e "  ${GREEN}restart${NC} - Restart the bot"
        echo -e "  ${GREEN}status${NC}  - Check bot status"
        exit 1
esac

exit 0
