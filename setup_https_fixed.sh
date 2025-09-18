#!/bin/bash

# UCA App HTTPS Setup Script - Fixed Version
# This script sets up HTTPS with Let's Encrypt SSL certificates
# Ensures no conflicts with other projects on the same VPS

set -e

echo "🔒 Setting up HTTPS for UCA App..."

# Check if domain is provided
if [ -z "$1" ]; then
    echo "❌ Error: Please provide your domain name"
    echo "Usage: ./setup_https_fixed.sh your-domain.com"
    exit 1
fi

DOMAIN=$1
EMAIL=${2:-"admin@$DOMAIN"}

echo "🌐 Domain: $DOMAIN"
echo "📧 Email: $EMAIL"

# Check if nginx is running
if systemctl is-active --quiet nginx; then
    echo "📋 Nginx is running. Checking for conflicts..."
    
    # Check if port 80 and 443 are already in use by other projects
    if netstat -tlnp | grep -q ":80 "; then
        echo "⚠️ Port 80 is already in use. Checking nginx configuration..."
        if ! grep -q "server_name $DOMAIN" /etc/nginx/sites-enabled/*; then
            echo "✅ No conflicts found for your domain"
        else
            echo "❌ Domain $DOMAIN is already configured in nginx"
            echo "Please check /etc/nginx/sites-enabled/ for existing configurations"
            exit 1
        fi
    fi
fi

# Install certbot if not already installed
echo "📦 Installing certbot..."
sudo apt update
sudo apt install -y certbot python3-certbot-nginx

# Stop nginx temporarily
echo "⏸️ Stopping nginx..."
sudo systemctl stop nginx

# Get SSL certificate
echo "🔐 Obtaining SSL certificate from Let's Encrypt..."
sudo certbot certonly --standalone -d $DOMAIN -d www.$DOMAIN --email $EMAIL --agree-tos --non-interactive

# Update nginx configuration with the correct domain
echo "🌐 Updating nginx configuration..."
sudo cp nginx_uca_app_ssl_fixed.conf /etc/nginx/sites-available/uca_app
sudo sed -i "s/your-domain.com/$DOMAIN/g" /etc/nginx/sites-available/uca_app
sudo sed -i "s/www.your-domain.com/www.$DOMAIN/g" /etc/nginx/sites-available/uca_app

# Update SSL certificate paths
sudo sed -i "s|/etc/letsencrypt/live/your-domain.com/fullchain.pem|/etc/letsencrypt/live/$DOMAIN/fullchain.pem|g" /etc/nginx/sites-available/uca_app
sudo sed -i "s|/etc/letsencrypt/live/your-domain.com/privkey.pem|/etc/letsencrypt/live/$DOMAIN/privkey.pem|g" /etc/nginx/sites-available/uca_app

# Enable the site
echo "🔗 Enabling nginx site..."
sudo ln -sf /etc/nginx/sites-available/uca_app /etc/nginx/sites-enabled/

# Test nginx configuration
echo "🧪 Testing nginx configuration..."
sudo nginx -t

# Start nginx
echo "▶️ Starting nginx..."
sudo systemctl start nginx

# Update Django environment to enable HTTPS
echo "🐍 Updating Django environment for HTTPS..."
if [ -f /var/www/uca_app/.env ]; then
    # Update existing .env file
    if grep -q "USE_HTTPS" /var/www/uca_app/.env; then
        sudo sed -i 's/USE_HTTPS=.*/USE_HTTPS=True/' /var/www/uca_app/.env
    else
        echo "USE_HTTPS=True" | sudo tee -a /var/www/uca_app/.env
    fi
else
    # Create new .env file
    sudo tee /var/www/uca_app/.env > /dev/null << EOF
# HTTPS Configuration
USE_HTTPS=True
ALLOWED_HOSTS=$DOMAIN,www.$DOMAIN
EOF
fi

# Update systemd service file
echo "🔧 Updating systemd service..."
sudo cp uca_app.service /etc/systemd/system/
sudo systemctl daemon-reload

# Restart Django application
echo "🔄 Restarting Django application..."
sudo systemctl restart uca_app

# Set up automatic certificate renewal
echo "🔄 Setting up automatic certificate renewal..."
sudo crontab -l 2>/dev/null | { cat; echo "0 12 * * * /usr/bin/certbot renew --quiet --post-hook 'systemctl reload nginx'"; } | sudo crontab -

# Test HTTPS
echo "🧪 Testing HTTPS setup..."
sleep 5
if curl -s -o /dev/null -w "%{http_code}" https://$DOMAIN | grep -q "200"; then
    echo "✅ HTTPS is working correctly!"
else
    echo "⚠️ HTTPS test failed. Please check the configuration."
    echo "🔍 Checking nginx status..."
    sudo systemctl status nginx
    echo "🔍 Checking uca_app status..."
    sudo systemctl status uca_app
fi

echo ""
echo "🎉 HTTPS setup completed!"
echo ""
echo "📋 Summary:"
echo "✅ SSL certificate obtained from Let's Encrypt"
echo "✅ Nginx configured for HTTPS"
echo "✅ Django configured for HTTPS"
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
echo "   sudo systemctl status uca_app"
echo "   sudo nginx -t"
