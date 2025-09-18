#!/bin/bash

# Quick HTTPS Fix for UCA App
# Use this if you already have the app deployed and just need to fix HTTPS

set -e

echo "🔧 Quick HTTPS Fix for UCA App"
echo "=============================="

# Check if domain is provided
if [ -z "$1" ]; then
    echo "❌ Error: Please provide your domain name"
    echo "Usage: ./quick_https_fix.sh your-domain.com"
    exit 1
fi

DOMAIN=$1
EMAIL="dotsincsolutions@gmail.com"


echo "🌐 Domain: $DOMAIN"
echo ""

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then
    echo "❌ Please run this script with sudo"
    exit 1
fi

# Stop services
echo "⏸️ Stopping services..."
systemctl stop nginx
systemctl stop uca_app

# Install certbot if not installed
if ! command -v certbot &> /dev/null; then
    echo "📦 Installing certbot..."
    apt update
    apt install -y certbot python3-certbot-nginx
fi

# Get SSL certificate
echo "🔐 Obtaining SSL certificate..."
certbot certonly --standalone -d $DOMAIN -d www.$DOMAIN --email admin@$DOMAIN --agree-tos --non-interactive

# Update nginx configuration
echo "🌐 Updating nginx configuration..."
cp nginx_uca_app_ssl_fixed.conf /etc/nginx/sites-available/uca_app
sed -i "s/your-domain.com/$DOMAIN/g" /etc/nginx/sites-available/uca_app
sed -i "s/www.your-domain.com/www.$DOMAIN/g" /etc/nginx/sites-available/uca_app

# Enable nginx site
ln -sf /etc/nginx/sites-available/uca_app /etc/nginx/sites-enabled/

# Update systemd service
echo "🔧 Updating systemd service..."
cp uca_app.service /etc/systemd/system/
systemctl daemon-reload

# Update environment for HTTPS
echo "🐍 Updating Django environment for HTTPS..."
if [ -f /var/www/uca_app/.env ]; then
    if grep -q "USE_HTTPS" /var/www/uca_app/.env; then
        sed -i 's/USE_HTTPS=.*/USE_HTTPS=True/' /var/www/uca_app/.env
    else
        echo "USE_HTTPS=True" >> /var/www/uca_app/.env
    fi
    
    if grep -q "ALLOWED_HOSTS" /var/www/uca_app/.env; then
        sed -i "s/ALLOWED_HOSTS=.*/ALLOWED_HOSTS=$DOMAIN,www.$DOMAIN/" /var/www/uca_app/.env
    else
        echo "ALLOWED_HOSTS=$DOMAIN,www.$DOMAIN" >> /var/www/uca_app/.env
    fi
else
    cat > /var/www/uca_app/.env << EOF
USE_HTTPS=True
ALLOWED_HOSTS=$DOMAIN,www.$DOMAIN
DEBUG=False
EOF
fi

# Test nginx configuration
echo "🧪 Testing nginx configuration..."
nginx -t

# Start services
echo "▶️ Starting services..."
systemctl start nginx
systemctl start uca_app

# Set up automatic certificate renewal
echo "🔄 Setting up automatic certificate renewal..."
crontab -l 2>/dev/null | { cat; echo "0 12 * * * /usr/bin/certbot renew --quiet --post-hook 'systemctl reload nginx'"; } | crontab -

# Test HTTPS
echo "🧪 Testing HTTPS..."
sleep 5
if curl -s -o /dev/null -w "%{http_code}" https://$DOMAIN | grep -q "200"; then
    echo "✅ HTTPS is working correctly!"
else
    echo "⚠️ HTTPS test failed. Checking status..."
    systemctl status nginx --no-pager
    systemctl status uca_app --no-pager
fi

echo ""
echo "🎉 Quick HTTPS fix completed!"
echo "============================="
echo ""
echo "🌐 Your application should now be available at:"
echo "   https://$DOMAIN"
echo "   https://www.$DOMAIN"
echo ""
echo "🔍 To check status:"
echo "   sudo systemctl status nginx"
echo "   sudo systemctl status uca_app"
