#!/bin/bash

# Fix Existing Issues Script for UCA App
# This script fixes the specific issues found in the logs

set -e

echo "🔧 Fixing Existing Issues for UCA App"
echo "====================================="

# Check if domain is provided
if [ -z "$1" ]; then
    echo "❌ Error: Please provide your domain name"
    echo "Usage: ./fix_existing_issues.sh your-domain.com [email]"
    echo "Default email: dotsincsolutions@gmail.com"
    exit 1
fi

DOMAIN=$1
EMAIL=${2:-"dotsincsolutions@gmail.com"}

echo "🌐 Domain: $DOMAIN"
echo "📧 Email: $EMAIL"
echo ""

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then
    echo "❌ Please run this script with sudo"
    exit 1
fi

# Fix 1: Create matplotlib cache directory with proper permissions
echo "📁 Fixing matplotlib cache directory permissions..."
mkdir -p /var/www/uca_app/matplotlib_cache
chown -R www-data:www-data /var/www/uca_app/matplotlib_cache
chmod -R 755 /var/www/uca_app/matplotlib_cache

# Fix 2: Create correct gunicorn config file
echo "🔧 Creating correct gunicorn configuration..."
cat > /var/www/uca_app/gunicorn_uca_app.conf.py << 'EOF'
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

# Fix 3: Create environment file for HTTPS
echo "📝 Creating environment file for HTTPS..."
cat > /var/www/uca_app/.env << EOF
# HTTPS Configuration
USE_HTTPS=True
ALLOWED_HOSTS=$DOMAIN,www.$DOMAIN
DEBUG=False
EOF

# Fix 4: Install certbot and get SSL certificate
echo "📦 Installing certbot..."
apt update
apt install -y certbot python3-certbot-nginx

# Stop nginx temporarily
echo "⏸️ Stopping nginx temporarily..."
systemctl stop nginx

# Get SSL certificate
echo "🔐 Obtaining SSL certificate from Let's Encrypt..."
certbot certonly --standalone -d $DOMAIN -d www.$DOMAIN --email $EMAIL --agree-tos --non-interactive

# Fix 5: Create nginx configuration for HTTPS
echo "🌐 Creating nginx configuration for HTTPS..."
cat > /etc/nginx/sites-available/uca_app_https << EOF
# Nginx configuration for UCA App with SSL support

# HTTP server - redirect to HTTPS
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;
    
    # Redirect all HTTP requests to HTTPS
    return 301 https://\$server_name\$request_uri;
}

# HTTPS server
server {
    listen 443 ssl http2;
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
        alias /var/www/uca_app/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    # Media files
    location /media/ {
        alias /var/www/uca_app/media/;
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

# Enable the nginx site
echo "🔗 Enabling nginx site..."
ln -sf /etc/nginx/sites-available/uca_app_https /etc/nginx/sites-enabled/

# Test nginx configuration
echo "🧪 Testing nginx configuration..."
nginx -t

# Start nginx
echo "▶️ Starting nginx..."
systemctl start nginx

# Restart UCA App service
echo "🔄 Restarting UCA App service..."
systemctl restart uca_app

# Set up automatic certificate renewal
echo "🔄 Setting up automatic certificate renewal..."
crontab -l 2>/dev/null | { cat; echo "0 12 * * * /usr/bin/certbot renew --quiet --post-hook 'systemctl reload nginx'"; } | crontab -

# Test HTTPS
echo "🧪 Testing HTTPS setup..."
sleep 5
if curl -s -o /dev/null -w "%{http_code}" https://$DOMAIN | grep -q "200"; then
    echo "✅ HTTPS is working correctly!"
else
    echo "⚠️ HTTPS test failed. Checking status..."
    systemctl status nginx --no-pager
    systemctl status uca_app --no-pager
fi

echo ""
echo "🎉 Issues fixed successfully!"
echo "============================"
echo ""
echo "📋 Fixed Issues:"
echo "✅ Matplotlib cache directory permissions"
echo "✅ Created correct gunicorn configuration file"
echo "✅ SSL certificate obtained from Let's Encrypt"
echo "✅ Nginx configured for HTTPS"
echo "✅ Environment file created for HTTPS"
echo "✅ Automatic certificate renewal set up"
echo ""
echo "🌐 Your application is now available at:"
echo "   https://$DOMAIN"
echo "   https://www.$DOMAIN"
echo ""
echo "🔍 To check status:"
echo "   sudo systemctl status nginx"
echo "   sudo systemctl status uca_app"
echo "   sudo nginx -t"
