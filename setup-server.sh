#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Please run as root or with sudo${NC}"
    exit 1
fi

echo -e "${YELLOW}Installing system dependencies...${NC}"

# Update package list
apt-get update || {
    echo -e "${RED}Failed to update package list${NC}"
    exit 1
}

# Install required packages
apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    curl \
    git \
    nginx \
    screen \
    build-essential || {
    echo -e "${RED}Failed to install system dependencies${NC}"
    exit 1
}

# Install Node.js 18.x
echo -e "${YELLOW}Installing Node.js...${NC}"
curl -fsSL https://deb.nodesource.com/setup_18.x | bash - || {
    echo -e "${RED}Failed to setup Node.js repository${NC}"
    exit 1
}
apt-get install -y nodejs || {
    echo -e "${RED}Failed to install Node.js${NC}"
    exit 1
}

# Verify installations
echo -e "${YELLOW}Verifying installations...${NC}"
python3 --version
node --version
npm --version
nginx -v

# Configure nginx
echo -e "${YELLOW}Configuring nginx...${NC}"
cat > /etc/nginx/sites-available/arablife << EOL
server {
    listen 80;
    server_name 45.76.83.149;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }

    location /docs {
        proxy_pass http://localhost:8000/docs;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
    }

    location /redoc {
        proxy_pass http://localhost:8000/redoc;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
    }
}
EOL

# Enable the site and remove default
ln -sf /etc/nginx/sites-available/arablife /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test nginx configuration
nginx -t || {
    echo -e "${RED}Nginx configuration test failed${NC}"
    exit 1
}

# Restart nginx
systemctl restart nginx || {
    echo -e "${RED}Failed to restart nginx${NC}"
    exit 1
}

# Set permissions for running on port 80
echo -e "${YELLOW}Setting up port permissions...${NC}"
apt-get install -y libcap2-bin || {
    echo -e "${RED}Failed to install libcap2-bin${NC}"
    exit 1
}
setcap 'cap_net_bind_service=+ep' $(which node)

# Create required directories
echo -e "${YELLOW}Creating required directories...${NC}"
mkdir -p dashboard/frontend/public
mkdir -p dashboard/backend/venv

# Set proper permissions
echo -e "${YELLOW}Setting file permissions...${NC}"
chown -R $SUDO_USER:$SUDO_USER . || {
    echo -e "${RED}Failed to set file permissions${NC}"
    exit 1
}

echo -e "${GREEN}Server setup completed successfully!${NC}"
echo -e "You can now run ${YELLOW}./dev.sh${NC} to start the development servers"
echo -e "The dashboard will be available at: ${GREEN}http://45.76.83.149${NC}"
echo -e "API documentation will be available at: ${GREEN}http://45.76.83.149/docs${NC}"
