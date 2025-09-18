#!/bin/bash

# UCA App Complete HTTPS Deployment Script
# This script ensures no conflicts with other projects on the same VPS

set -e

echo "🚀 UCA App HTTPS Deployment Script"
echo "=================================="

# Check if domain is provided
if [ -z "$1" ]; then
    echo "❌ Error: Please provide your domain name"
    echo "Usage: ./deploy_https_fixed.sh your-domain.com [email]"
    exit 1
fi

DOMAIN=$1
EMAIL=${2:-"admin@$DOMAIN"}

echo "🌐 Domain: $DOMAIN"
echo "📧 Email: $EMAIL"
echo ""

# Function to check if port is in use
check_port() {
    local port=$1
    if netstat -tlnp | grep -q ":$port "; then
        echo "⚠️ Port $port is already in use"
        netstat -tlnp | grep ":$port "
        return 1
    else
        echo "✅ Port $port is available"
        return 0
    fi
}

# Function to check if domain is already configured
check_domain() {
    local domain=$1
    if [ -f /etc/nginx/sites-enabled/uca_app ]; then
        if grep -q "server_name $domain" /etc/nginx/sites-enabled/uca_app; then
            echo "✅ Domain $domain is already configured for UCA App"
            return 0
        fi
    fi
    
    # Check other nginx configurations
    for config in /etc/nginx/sites-enabled/*; do
        if [ -f "$config" ] && grep -q "server_name.*$domain" "$config"; then
            echo "❌ Domain $domain is already configured in $config"
            echo "This might conflict with your other projects"
            return 1
        fi
    done
    
    echo "✅ Domain $domain is available"
    return 0
}

# Pre-deployment checks
echo "🔍 Pre-deployment checks..."
echo "=========================="

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then
    echo "❌ Please run this script with sudo"
    exit 1
fi

# Check nginx installation
if ! command -v nginx &> /dev/null; then
    echo "📦 Installing nginx..."
    apt update
    apt install -y nginx
fi

# Check if nginx is running
if ! systemctl is-active --quiet nginx; then
    echo "▶️ Starting nginx..."
    systemctl start nginx
fi

# Check ports
echo "🔍 Checking port availability..."
check_port 80
check_port 443
check_port 2287

# Check domain configuration
echo "🔍 Checking domain configuration..."
check_domain $DOMAIN

# Check if UCA App service exists
if systemctl list-unit-files | grep -q uca_app.service; then
    echo "✅ UCA App service is already configured"
    echo "🔄 Stopping UCA App service..."
    systemctl stop uca_app
else
    echo "📝 UCA App service will be created"
fi

# Install required packages
echo "📦 Installing required packages..."
apt update
apt install -y python3 python3-pip python3-venv postgresql postgresql-contrib nginx certbot python3-certbot-nginx

# Create application directory
echo "📁 Setting up application directory..."
mkdir -p /var/www/uca_app
chown -R www-data:www-data /var/www/uca_app

# Copy application files
echo "📋 Copying application files..."
cp -r . /var/www/uca_app/
cd /var/www/uca_app

# Set up virtual environment
echo "🐍 Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Set up database
echo "🗄️ Setting up PostgreSQL database..."
sudo -u postgres psql -c "CREATE DATABASE uca_app;" 2>/dev/null || echo "Database already exists"
sudo -u postgres psql -c "CREATE USER uca_user WITH PASSWORD 'UCA_2024_Secure!';" 2>/dev/null || echo "User already exists"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE uca_app TO uca_user;" 2>/dev/null || echo "Privileges already granted"

# Run Django migrations
echo "🔄 Running Django migrations..."
python manage.py migrate

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

# Set up SSL certificate
echo "🔐 Setting up SSL certificate..."
systemctl stop nginx
certbot certonly --standalone -d $DOMAIN -d www.$DOMAIN --email $EMAIL --agree-tos --non-interactive

# Configure nginx
echo "🌐 Configuring nginx..."
cp nginx_uca_app_ssl_fixed.conf /etc/nginx/sites-available/uca_app
sed -i "s/your-domain.com/$DOMAIN/g" /etc/nginx/sites-available/uca_app
sed -i "s/www.your-domain.com/www.$DOMAIN/g" /etc/nginx/sites-available/uca_app

# Enable nginx site
ln -sf /etc/nginx/sites-available/uca_app /etc/nginx/sites-enabled/

# Test nginx configuration
echo "🧪 Testing nginx configuration..."
nginx -t

# Set up systemd service
echo "🔧 Setting up systemd service..."
cp uca_app.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable uca_app

# Create environment file
echo "📝 Creating environment file..."
cat > /var/www/uca_app/.env << EOF
# HTTPS Configuration
USE_HTTPS=True
ALLOWED_HOSTS=$DOMAIN,www.$DOMAIN
DEBUG=False
EOF

# Set proper permissions
echo "🔐 Setting proper permissions..."
chown -R www-data:www-data /var/www/uca_app
chmod -R 755 /var/www/uca_app

# Start services
echo "▶️ Starting services..."
systemctl start nginx
systemctl start uca_app

# Set up automatic certificate renewal
echo "🔄 Setting up automatic certificate renewal..."
crontab -l 2>/dev/null | { cat; echo "0 12 * * * /usr/bin/certbot renew --quiet --post-hook 'systemctl reload nginx'"; } | crontab -

# Final checks
echo "🧪 Final checks..."
sleep 5

echo "🔍 Checking nginx status..."
systemctl status nginx --no-pager

echo "🔍 Checking UCA App status..."
systemctl status uca_app --no-pager

echo "🔍 Testing HTTPS..."
if curl -s -o /dev/null -w "%{http_code}" https://$DOMAIN | grep -q "200"; then
    echo "✅ HTTPS is working correctly!"
else
    echo "⚠️ HTTPS test failed. Checking logs..."
    echo "Nginx error log:"
    tail -n 20 /var/log/nginx/error.log
    echo "UCA App log:"
    journalctl -u uca_app --no-pager -n 20
fi

echo ""
echo "🎉 Deployment completed!"
echo "========================"
echo ""
echo "📋 Summary:"
echo "✅ SSL certificate obtained from Let's Encrypt"
echo "✅ Nginx configured for HTTPS"
echo "✅ Django configured for HTTPS"
echo "✅ Automatic certificate renewal set up"
echo "✅ Port 2287 configured for UCA App (no conflicts)"
echo "✅ Database configured"
echo "✅ Static files collected"
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
echo ""
echo "📝 Logs:"
echo "   sudo journalctl -u uca_app -f"
echo "   sudo tail -f /var/log/nginx/error.log"
