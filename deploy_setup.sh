#!/bin/bash

# UCA App Server Setup Script
# Run this script on your SSH server to prepare it for deployment

set -e

echo "🚀 Setting up UCA App on your server..."

# Update system packages
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install required packages
echo "🔧 Installing required packages..."
sudo apt install -y python3 python3-pip python3-venv nginx postgresql postgresql-contrib git supervisor

# Create application directory
echo "📁 Creating application directory..."
sudo mkdir -p /var/www/uca_app
sudo chown $USER:$USER /var/www/uca_app

# Create virtual environment
echo "🐍 Setting up Python virtual environment..."
cd /var/www/uca_app
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "📚 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories
echo "📂 Creating necessary directories..."
mkdir -p logs
mkdir -p media
mkdir -p staticfiles

# Set up PostgreSQL database
echo "🗄️ Setting up PostgreSQL database..."
sudo -u postgres createdb uca_app_db
sudo -u postgres createuser uca_app_user
sudo -u postgres psql -c "ALTER USER uca_app_user PASSWORD 'your_secure_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE uca_app_db TO uca_app_user;"

# Create systemd service files
echo "⚙️ Setting up systemd services..."
sudo cp uca_app.service /etc/systemd/system/
sudo cp uca_app.socket /etc/systemd/system/

# Create nginx configuration
echo "🌐 Setting up Nginx configuration..."
sudo cp nginx.conf /etc/nginx/sites-available/uca_app
sudo ln -sf /etc/nginx/sites-available/uca_app /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Create log directories
echo "📝 Setting up log directories..."
sudo mkdir -p /var/log/gunicorn
sudo mkdir -p /run/gunicorn
sudo chown www-data:www-data /var/log/gunicorn
sudo chown www-data:www-data /run/gunicorn

# Set proper permissions
echo "🔐 Setting proper permissions..."
sudo chown -R www-data:www-data /var/www/uca_app
sudo chmod -R 755 /var/www/uca_app

# Enable and start services
echo "🔄 Enabling and starting services..."
sudo systemctl daemon-reload
sudo systemctl enable uca_app.socket
sudo systemctl start uca_app.socket
sudo systemctl enable uca_app.service
sudo systemctl start uca_app.service
sudo systemctl enable nginx
sudo systemctl restart nginx

# Test nginx configuration
echo "🧪 Testing Nginx configuration..."
sudo nginx -t

# Create .env file template
echo "📄 Creating .env file template..."
cat > .env.template << EOF
# Django Production Settings
SECRET_KEY=your-super-secret-key-here-change-this-in-production
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
DATABASE_URL=postgresql://uca_app_user:your_secure_password@localhost:5432/uca_app_db

# Email settings (optional)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
EOF

echo "✅ Server setup completed!"
echo ""
echo "📋 Next steps:"
echo "1. Copy your SSL certificates to /etc/ssl/certs/ and /etc/ssl/private/"
echo "2. Update nginx.conf with your domain name"
echo "3. Create .env file with your actual values"
echo "4. Run: python manage.py migrate --settings=uca_project.settings_production"
echo "5. Run: python manage.py collectstatic --noinput --settings=uca_project.settings_production"
echo "6. Create superuser: python manage.py createsuperuser --settings=uca_project.settings_production"
echo ""
echo "🔧 Service management commands:"
echo "sudo systemctl status uca_app"
echo "sudo systemctl restart uca_app"
echo "sudo systemctl status nginx"
echo "sudo systemctl restart nginx"
