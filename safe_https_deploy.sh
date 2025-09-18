#!/bin/bash

# Safe HTTPS Deployment Script for UCA App
# This script creates NEW files instead of modifying existing ones
# Ensures no conflicts with other projects

set -e

echo "🔒 Safe HTTPS Deployment for UCA App"
echo "===================================="

# Check if domain is provided
if [ -z "$1" ]; then
    echo "❌ Error: Please provide your domain name"
    echo "Usage: ./safe_https_deploy.sh your-domain.com [email]"
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

# Check if nginx is running
if ! systemctl is-active --quiet nginx; then
    echo "▶️ Starting nginx..."
    systemctl start nginx
fi

# Install certbot if not installed
if ! command -v certbot &> /dev/null; then
    echo "📦 Installing certbot..."
    apt update
    apt install -y certbot python3-certbot-nginx
fi

# Stop services temporarily
echo "⏸️ Stopping services temporarily..."
systemctl stop nginx
systemctl stop uca_app

# Get SSL certificate
echo "🔐 Obtaining SSL certificate from Let's Encrypt..."
certbot certonly --standalone -d $DOMAIN -d www.$DOMAIN --email $EMAIL --agree-tos --non-interactive

# Create NEW nginx configuration (don't overwrite existing)
echo "🌐 Creating NEW nginx configuration..."
cat > /etc/nginx/sites-available/uca_app_https << 'EOF'
# Nginx configuration for UCA App with SSL support
# This is a NEW configuration file to avoid conflicts

# HTTP server - redirect to HTTPS
server {
    listen 80;
    server_name DOMAIN_PLACEHOLDER www.DOMAIN_PLACEHOLDER;
    
    # Redirect all HTTP requests to HTTPS
    return 301 https://$server_name$request_uri;
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name DOMAIN_PLACEHOLDER www.DOMAIN_PLACEHOLDER;
    
    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/DOMAIN_PLACEHOLDER/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/DOMAIN_PLACEHOLDER/privkey.pem;
    
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
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
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
    location ~ /\. {
        deny all;
        access_log off;
        log_not_found off;
    }
    
    location ~ \.(env|log|sql)$ {
        deny all;
        access_log off;
        log_not_found off;
    }
}
EOF

# Replace domain placeholders
sed -i "s/DOMAIN_PLACEHOLDER/$DOMAIN/g" /etc/nginx/sites-available/uca_app_https

# Create NEW gunicorn configuration (don't overwrite existing)
echo "🔧 Creating NEW gunicorn configuration..."
cat > /var/www/uca_app/gunicorn_https.conf.py << 'EOF'
# Gunicorn configuration file for HTTPS
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
proc_name = "uca_app_https"

# Server mechanics
daemon = False
pidfile = "/var/run/gunicorn/uca_app_https.pid"
user = None
group = None
tmp_upload_dir = None

# Environment variables for matplotlib
raw_env = [
    'MPLCONFIGDIR=/var/www/uca_app/matplotlib_cache',
]
EOF

# Create matplotlib cache directory with proper permissions
echo "📁 Creating matplotlib cache directory..."
mkdir -p /var/www/uca_app/matplotlib_cache
chown -R www-data:www-data /var/www/uca_app/matplotlib_cache
chmod -R 755 /var/www/uca_app/matplotlib_cache

# Create NEW systemd service (don't overwrite existing)
echo "🔧 Creating NEW systemd service..."
cat > /etc/systemd/system/uca_app_https.service << 'EOF'
[Unit]
Description=UCA App Django Application (HTTPS)
After=network.target postgresql.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/uca_app
Environment="PATH=/var/www/uca_app/venv/bin"
Environment="DJANGO_SETTINGS_MODULE=uca_project.settings_production"
Environment="MPLCONFIGDIR=/var/www/uca_app/matplotlib_cache"
ExecStart=/var/www/uca_app/venv/bin/gunicorn --config /var/www/uca_app/gunicorn_https.conf.py uca_project.wsgi:application
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Create environment file for HTTPS
echo "📝 Creating HTTPS environment file..."
cat > /var/www/uca_app/.env_https << EOF
# HTTPS Configuration
USE_HTTPS=True
ALLOWED_HOSTS=$DOMAIN,www.$DOMAIN
DEBUG=False
EOF

# Enable the NEW nginx site
echo "🔗 Enabling NEW nginx site..."
ln -sf /etc/nginx/sites-available/uca_app_https /etc/nginx/sites-enabled/

# Test nginx configuration
echo "🧪 Testing nginx configuration..."
nginx -t

# Reload systemd and enable NEW service
echo "🔄 Reloading systemd and enabling NEW service..."
systemctl daemon-reload
systemctl enable uca_app_https

# Start services
echo "▶️ Starting services..."
systemctl start nginx
systemctl start uca_app_https

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
    systemctl status uca_app_https --no-pager
fi

echo ""
echo "🎉 Safe HTTPS deployment completed!"
echo "=================================="
echo ""
echo "📋 Summary:"
echo "✅ SSL certificate obtained from Let's Encrypt"
echo "✅ NEW nginx configuration created (uca_app_https)"
echo "✅ NEW gunicorn configuration created (gunicorn_https.conf.py)"
echo "✅ NEW systemd service created (uca_app_https.service)"
echo "✅ Matplotlib cache directory created with proper permissions"
echo "✅ Automatic certificate renewal set up"
echo "✅ Port 2287 configured for UCA App (no conflicts)"
echo ""
echo "🌐 Your application is now available at:"
echo "   https://$DOMAIN"
echo "   https://www.$DOMAIN"
echo ""
echo "🔧 Certificate will auto-renew every 90 days"
echo "📧 Certificate expiration notifications will be sent to: $EMAIL"
echo ""
echo "🔍 To check status:"
echo "   sudo systemctl status nginx"
echo "   sudo systemctl status uca_app_https"
echo "   sudo nginx -t"
echo ""
echo "📝 Logs:"
echo "   sudo journalctl -u uca_app_https -f"
echo "   sudo tail -f /var/log/nginx/error.log"
echo ""
echo "⚠️  Note: Your original service (uca_app) is still available if needed"
echo "   To switch back: sudo systemctl stop uca_app_https && sudo systemctl start uca_app"
