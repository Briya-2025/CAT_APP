#!/bin/bash

# UCA App Deployment Script with HTTPS
# This script deploys the UCA app with HTTPS support without conflicts with other projects

set -e

echo "🚀 Deploying UCA App with HTTPS..."

# Project configuration
PROJECT_DIR="/var/www/uca_app"
SERVICE_NAME="uca_app.service"
NGINX_SITE="uca_app_https"
DOMAIN="ihsstores.com"
EMAIL="dotsincsolutions@gmail.com"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root"
   exit 1
fi

print_status "🌐 Domain: $DOMAIN"
print_status "📧 Email: $EMAIL"

# Stop existing service
print_status "Stopping existing service..."
sudo systemctl stop $SERVICE_NAME 2>/dev/null || print_warning "Service not running"

# Update code
print_status "Updating code..."
cd $PROJECT_DIR
git pull origin main

# Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
print_status "Installing dependencies..."
pip install -r requirements.txt
pip install --upgrade kaleido


# Run migrations
print_status "Running migrations..."
export DJANGO_SETTINGS_MODULE=uca_project.settings_production
python manage.py migrate

# Collect static files
print_status "Collecting static files..."
python manage.py collectstatic --noinput

# Set permissions
print_status "Setting permissions..."
sudo chown -R www-data:www-data $PROJECT_DIR
sudo chmod -R 755 $PROJECT_DIR

# HTTPS Setup - Create matplotlib cache directory
print_status "Setting up matplotlib cache directory..."
sudo mkdir -p $PROJECT_DIR/matplotlib_cache
sudo chown -R www-data:www-data $PROJECT_DIR/matplotlib_cache
sudo chmod -R 755 $PROJECT_DIR/matplotlib_cache

# HTTPS Setup - Create gunicorn config file
print_status "Creating gunicorn configuration..."
sudo tee $PROJECT_DIR/gunicorn_uca_app.conf.py > /dev/null << 'EOF'
# Gunicorn configuration file for UCA App
import multiprocessing
import os

# Server socket
bind = "127.0.0.1:2287"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Restart workers after this many requests, to help prevent memory leaks
max_requests = 1000
max_requests_jitter = 50

# Logging - use stdout/stderr for systemd
accesslog = "-"
errorlog = "-"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process naming
proc_name = "uca_app"

# Server mechanics
daemon = False
pidfile = "/var/run/gunicorn/uca_app.pid"
user = None
group = None
tmp_upload_dir = None

# Environment variables for matplotlib
raw_env = [
    'MPLCONFIGDIR=/var/www/uca_app/matplotlib_cache',
]
EOF

# HTTPS Setup - Create environment file
print_status "Creating HTTPS environment file..."
sudo tee $PROJECT_DIR/.env > /dev/null << EOF
# HTTPS Configuration
USE_HTTPS=True
ALLOWED_HOSTS=$DOMAIN,www.$DOMAIN
DEBUG=False
EOF

# HTTPS Setup - Install certbot if not installed
print_status "Installing certbot..."
sudo apt update
sudo apt install -y certbot python3-certbot-nginx

# HTTPS Setup - Get SSL certificate
print_status "Obtaining SSL certificate from Let's Encrypt..."
sudo systemctl stop nginx
sudo certbot certonly --standalone -d $DOMAIN -d www.$DOMAIN --email $EMAIL --agree-tos --non-interactive

# HTTPS Setup - Create nginx configuration
print_status "Creating nginx configuration for HTTPS..."
sudo tee /etc/nginx/sites-available/$NGINX_SITE > /dev/null << EOF
# Nginx configuration for UCA App with SSL support
# This is separate from other projects

# HTTP server - redirect to HTTPS
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;
    
    # Redirect all HTTP requests to HTTPS
    return 301 https://\$server_name\$request_uri;
}

# HTTPS server
server {
    listen 443 ssl;
    server_name $DOMAIN www.$DOMAIN;
    
    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;
    
    # SSL Security Settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    
    # Static files
    location /static/ {
        alias $PROJECT_DIR/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    # Media files
    location /media/ {
        alias $PROJECT_DIR/media/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    # Main application
    location / {
        proxy_pass http://127.0.0.1:2287;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # Timeout settings
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
        
        # Buffer settings
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
    }
    
    # Health check endpoint
    location /health/ {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
    
    # Deny access to sensitive files
    location ~ /\\. {
        deny all;
        access_log off;
        log_not_found off;
    }
    
    location ~ \\.(env|log|sql)$ {
        deny all;
        access_log off;
        log_not_found off;
    }
}
EOF

# Copy systemd service file
print_status "Copying systemd service file..."
sudo cp uca_app.service /etc/systemd/system/

# Enable Nginx site
print_status "Configuring Nginx..."
sudo ln -sf /etc/nginx/sites-available/$NGINX_SITE /etc/nginx/sites-enabled/

# Test nginx configuration
print_status "Testing Nginx configuration..."
sudo nginx -t

# Start nginx
print_status "Starting Nginx..."
sudo systemctl start nginx

# Reload systemd and start service
print_status "Starting service..."
sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME
sudo systemctl start $SERVICE_NAME

# Set up automatic certificate renewal
print_status "Setting up automatic certificate renewal..."
sudo crontab -l 2>/dev/null | { cat; echo "0 12 * * * /usr/bin/certbot renew --quiet --post-hook 'systemctl reload nginx'"; } | sudo crontab -

# Check service status
print_status "Checking service status..."
sleep 5
sudo systemctl status $SERVICE_NAME --no-pager -l

# Check if port is listening
print_status "Checking port 2287..."
if sudo netstat -tlnp | grep -q ":2287 "; then
    print_status "✅ Port 2287 is listening"
else
    print_error "❌ Port 2287 is not listening"
    print_status "Service logs:"
    sudo journalctl -u $SERVICE_NAME --no-pager -l --lines=20
    exit 1
fi

# Test HTTPS
print_status "Testing HTTPS setup..."
sleep 5
if curl -s -o /dev/null -w "%{http_code}" https://$DOMAIN | grep -q "200"; then
    print_status "✅ HTTPS is working correctly!"
else
    print_warning "⚠️ HTTPS test failed. Checking status..."
    sudo systemctl status nginx --no-pager
    sudo systemctl status $SERVICE_NAME --no-pager
fi

print_status "🎉 Deployment with HTTPS completed successfully!"
print_status "Your UCA app is now available at:"
print_status "  🔒 https://$DOMAIN"
print_status "  🔒 https://www.$DOMAIN"
print_status ""
print_status "📋 What was configured:"
print_status "✅ SSL certificate obtained from Let's Encrypt"
print_status "✅ Nginx configured for HTTPS with security headers"
print_status "✅ Django configured for HTTPS"
print_status "✅ Matplotlib cache directory created with proper permissions"
print_status "✅ Automatic certificate renewal set up"
print_status "✅ Port 2287 configured (no conflicts with other projects)"
print_status ""
print_status "Useful commands:"
print_status "  Check service: sudo systemctl status $SERVICE_NAME"
print_status "  View logs: sudo journalctl -u $SERVICE_NAME -f"
print_status "  Restart service: sudo systemctl restart $SERVICE_NAME"
print_status "  Check port: sudo netstat -tlnp | grep 2287"
print_status "  Test HTTPS: curl -I https://$DOMAIN"
