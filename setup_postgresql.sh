#!/bin/bash

# PostgreSQL Setup Script for UCA App
# Run this script on your SSH server to set up PostgreSQL

set -e

echo "🐘 Setting up PostgreSQL for UCA App..."

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

# Get database credentials from user
echo "🔐 Setting up database credentials..."
read -p "Enter database name (default: uca_app_db): " DB_NAME
DB_NAME=${DB_NAME:-uca_app_db}

read -p "Enter database username (default: uca_app_user): " DB_USER
DB_USER=${DB_USER:-uca_app_user}

read -s -p "Enter database password: " DB_PASSWORD
echo

read -p "Enter database host (default: localhost): " DB_HOST
DB_HOST=${DB_HOST:-localhost}

read -p "Enter database port (default: 5432): " DB_PORT
DB_PORT=${DB_PORT:-5432}

# Create database and user
echo "🗄️ Creating database and user..."
sudo -u postgres psql -c "CREATE DATABASE $DB_NAME;"
sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"
sudo -u postgres psql -c "ALTER USER $DB_USER CREATEDB;"

# Configure PostgreSQL for better performance
echo "⚙️ Configuring PostgreSQL..."
sudo -u postgres psql -c "ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements';"
sudo -u postgres psql -c "ALTER SYSTEM SET max_connections = 200;"
sudo -u postgres psql -c "ALTER SYSTEM SET shared_buffers = '256MB';"
sudo -u postgres psql -c "ALTER SYSTEM SET effective_cache_size = '1GB';"
sudo -u postgres psql -c "ALTER SYSTEM SET maintenance_work_mem = '64MB';"
sudo -u postgres psql -c "ALTER SYSTEM SET checkpoint_completion_target = 0.9;"
sudo -u postgres psql -c "ALTER SYSTEM SET wal_buffers = '16MB';"
sudo -u postgres psql -c "ALTER SYSTEM SET default_statistics_target = 100;"

# Restart PostgreSQL to apply changes
echo "🔄 Restarting PostgreSQL..."
sudo systemctl restart postgresql

# Test connection
echo "🧪 Testing database connection..."
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "SELECT version();"

# Create .env file with database configuration
echo "📄 Creating .env file..."
cat > .env << EOF
# Django Production Settings
SECRET_KEY=your-super-secret-key-here-change-this-in-production
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
DATABASE_URL=postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME

# Email settings (optional)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
EOF

echo "✅ PostgreSQL setup completed!"
echo ""
echo "📋 Database Information:"
echo "Database Name: $DB_NAME"
echo "Database User: $DB_USER"
echo "Database Host: $DB_HOST"
echo "Database Port: $DB_PORT"
echo "Database URL: postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME"
echo ""
echo "🔧 Next steps:"
echo "1. Update your GitHub secrets with the DATABASE_URL above"
echo "2. Run: python manage.py migrate --settings=uca_project.settings_production"
echo "3. Create superuser: python manage.py createsuperuser --settings=uca_project.settings_production"
echo ""
echo "📊 PostgreSQL management commands:"
echo "sudo systemctl status postgresql"
echo "sudo systemctl restart postgresql"
echo "sudo -u postgres psql -c '\\l'  # List databases"
echo "sudo -u postgres psql -c '\\du' # List users"
