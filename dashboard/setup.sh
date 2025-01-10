#!/bin/bash

# Exit on error
set -e

echo "Setting up ArabLife Dashboard..."

# Install Node.js and npm if not installed
if ! command -v node &> /dev/null; then
    echo "Installing Node.js and npm..."
    curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
    sudo apt install -y nodejs
fi

# Install Python dependencies for backend
echo "Setting up backend..."
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create backend service
sudo tee /etc/systemd/system/arablife-dashboard-api.service > /dev/null << EOL
[Unit]
Description=ArabLife Dashboard API
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
Environment=PATH=$(pwd)/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
ExecStart=$(pwd)/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOL

# Set up frontend
echo "Setting up frontend..."
cd ../frontend

# Install dependencies
npm install

# Build frontend
npm run build

# Install nginx if not installed
if ! command -v nginx &> /dev/null; then
    echo "Installing nginx..."
    sudo apt install -y nginx
fi

# Create nginx configuration
sudo tee /etc/nginx/sites-available/arablife-dashboard << EOL
server {
    listen 80;
    server_name dashboard.arablife.com;  # Change this to your domain

    # Frontend
    location / {
        root $(pwd)/build;
        try_files \$uri \$uri/ /index.html;
        add_header Cache-Control "no-cache";
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
    }
}
EOL

# Enable site
sudo ln -sf /etc/nginx/sites-available/arablife-dashboard /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test nginx config
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx

# Start services
sudo systemctl daemon-reload
sudo systemctl enable arablife-dashboard-api
sudo systemctl start arablife-dashboard-api

echo "Dashboard setup complete!"
echo "Please update the following files with your settings:"
echo "1. frontend/.env with your API URL"
echo "2. backend/.env with your database and Discord settings"
echo ""
echo "To manage the services:"
echo "Backend API: sudo systemctl {start|stop|restart} arablife-dashboard-api"
echo "Frontend: served through nginx at http://dashboard.arablife.com"
echo ""
echo "Don't forget to:"
echo "1. Set up your domain DNS to point to this server"
echo "2. Set up SSL with certbot: sudo certbot --nginx -d dashboard.arablife.com"
