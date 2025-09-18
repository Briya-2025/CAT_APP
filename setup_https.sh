#!/bin/bash

# UCA App HTTPS Setup Script
# This script sets up HTTPS with Let's Encrypt SSL certificates

set -e

echo "🔒 Setting up HTTPS for UCA App..."

# Check if domain is provided
if [ -z "$1" ]; then
    echo "❌ Error: Please provide your domain name"
    echo "Usage: ./setup_https.sh your-domain.com"
    exit 1
fi

DOMAIN=$1
EMAIL=${2:-"admin@$DOMAIN"}

echo "🌐 Domain: $DOMAIN"
echo "📧 Email: $EMAIL"

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
sudo cp nginx.conf /etc/nginx/sites-available/uca_app
sudo sed -i "s/your-domain.com/$DOMAIN/g" /etc/nginx/sites-available/uca_app
sudo sed -i "s/www.your-domain.com/www.$DOMAIN/g" /etc/nginx/sites-available/uca_app

# Update SSL certificate paths
sudo sed -i "s|/etc/ssl/certs/your-domain.crt|/etc/letsencrypt/live/$DOMAIN/fullchain.pem|g" /etc/nginx/sites-available/uca_app
sudo sed -i "s|/etc/ssl/private/your-domain.key|/etc/letsencrypt/live/$DOMAIN/privkey.pem|g" /etc/nginx/sites-available/uca_app

# Test nginx configuration
echo "🧪 Testing nginx configuration..."
sudo nginx -t

# Start nginx
echo "▶️ Starting nginx..."
sudo systemctl start nginx

# Update Django environment to enable HTTPS
echo "🐍 Updating Django environment for HTTPS..."
cat >> /var/www/uca_app/.env << EOF

# HTTPS Configuration
USE_HTTPS=True
EOF

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
fi

echo ""
echo "🎉 HTTPS setup completed!"
echo ""
echo "📋 Summary:"
echo "✅ SSL certificate obtained from Let's Encrypt"
echo "✅ Nginx configured for HTTPS"
echo "✅ Django configured for HTTPS"
echo "✅ Automatic certificate renewal set up"
echo ""
echo "🌐 Your application is now available at:"
echo "   https://$DOMAIN"
echo "   https://www.$DOMAIN"
echo ""
echo "🔧 Certificate will auto-renew every 90 days"
echo "📧 Certificate expiration notifications will be sent to: $EMAIL"
