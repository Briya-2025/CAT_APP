#!/bin/bash

# UCA App Deployment Script
# This script helps deploy the UCA app without conflicts with other projects

set -e

echo "🚀 Deploying UCA App..."

# Project configuration
PROJECT_DIR="/var/www/uca_app"
SERVICE_NAME="uca_app.service"
NGINX_SITE="uca_app"
DOMAIN="ihsstores.com"

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

# Copy configuration files
print_status "Copying configuration files..."
sudo cp nginx_uca_app.conf /etc/nginx/sites-available/$NGINX_SITE
sudo cp uca_app.service /etc/systemd/system/

# Enable Nginx site
print_status "Configuring Nginx..."
sudo ln -sf /etc/nginx/sites-available/$NGINX_SITE /etc/nginx/sites-enabled/
sudo nginx -t

# Reload systemd and start service
print_status "Starting service..."
sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME
sudo systemctl start $SERVICE_NAME

# Restart Nginx
print_status "Restarting Nginx..."
sudo systemctl restart nginx

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

# Test Nginx configuration
print_status "Testing Nginx configuration..."
if sudo nginx -t; then
    print_status "✅ Nginx configuration is valid"
else
    print_error "❌ Nginx configuration has errors"
    exit 1
fi

print_status "🎉 Deployment completed successfully!"
print_status "Your UCA app should be accessible at: http://$DOMAIN"
print_status "Admin credentials: username=admin, password=admin123"
print_status ""
print_status "Useful commands:"
print_status "  Check service: sudo systemctl status $SERVICE_NAME"
print_status "  View logs: sudo journalctl -u $SERVICE_NAME -f"
print_status "  Restart service: sudo systemctl restart $SERVICE_NAME"
print_status "  Check port: sudo netstat -tlnp | grep 2287"
