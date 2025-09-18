#!/bin/bash

# Simple PostgreSQL Setup Script for UCA App
# Run this script on your SSH server to set up PostgreSQL with your specific database

set -e

echo "🐘 Setting up PostgreSQL for UCA App with database 'flaship1'..."

# Update system packages
echo "📦 Updating system packages..."
sudo apt update

# Install PostgreSQL
echo "🔧 Installing PostgreSQL..."
sudo apt install -y postgresql postgresql-contrib

# Start and enable PostgreSQL service
echo "🔄 Starting PostgreSQL service..."
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create the database 'flaship1'
echo "🗄️ Creating database 'flaship1'..."
sudo -u postgres psql -c "CREATE DATABASE flaship1;"

# Set password for postgres user
echo "🔐 Setting password for postgres user..."
sudo -u postgres psql -c "ALTER USER postgres PASSWORD '1234';"

# Grant all privileges on the database
echo "🔑 Granting privileges..."
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE flaship1 TO postgres;"

# Configure PostgreSQL for better performance
echo "⚙️ Configuring PostgreSQL..."
sudo -u postgres psql -c "ALTER SYSTEM SET max_connections = 200;"
sudo -u postgres psql -c "ALTER SYSTEM SET shared_buffers = '256MB';"
sudo -u postgres psql -c "ALTER SYSTEM SET effective_cache_size = '1GB';"

# Restart PostgreSQL to apply changes
echo "🔄 Restarting PostgreSQL..."
sudo systemctl restart postgresql

# Test connection
echo "🧪 Testing database connection..."
PGPASSWORD=1234 psql -h 127.0.0.1 -p 5432 -U postgres -d flaship1 -c "SELECT version();"

echo "✅ PostgreSQL setup completed!"
echo ""
echo "📋 Database Information:"
echo "Database Name: flaship1"
echo "Database User: postgres"
echo "Database Password: 1234"
echo "Database Host: 127.0.0.1"
echo "Database Port: 5432"
echo ""
echo "🔧 Next steps:"
echo "1. Run: python manage.py migrate --settings=uca_project.settings_production"
echo "2. Create superuser: python manage.py createsuperuser --settings=uca_project.settings_production"
echo "3. Test your application"
echo ""
echo "📊 PostgreSQL management commands:"
echo "sudo systemctl status postgresql"
echo "sudo systemctl restart postgresql"
echo "PGPASSWORD=1234 psql -h 127.0.0.1 -U postgres -d flaship1"
