# Manual PostgreSQL Database Setup Guide

This guide shows you how to manually create a PostgreSQL database on your server for the UCA app.

## 🐘 **Step 1: Connect to Your Server**

```bash
ssh your-username@your-server-ip
```

## 🔧 **Step 2: Install PostgreSQL (if not already installed)**

```bash
# Update system packages
sudo apt update

# Install PostgreSQL
sudo apt install -y postgresql postgresql-contrib

# Start and enable PostgreSQL service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Check if PostgreSQL is running
sudo systemctl status postgresql
```

## 🗄️ **Step 3: Create Database and User**

### **Option A: Using psql (Recommended)**

```bash
# Switch to postgres user
sudo -u postgres psql

# Create database
CREATE DATABASE UCA_APP;

# Create user with password
CREATE USER postgres WITH PASSWORD 'UCA_APP_BRIYA';

# Grant privileges
GRANT ALL PRIVILEGES ON DATABASE UCA_APP TO postgres;

# Give user ability to create databases (optional)
ALTER USER postgres CREATEDB;

# Exit psql
\q
```

### **Option B: Using Command Line**

```bash
# Create database
sudo -u postgres createdb flaship1

# Create user
sudo -u postgres createuser postgres

# Set password for user
sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'your-secure-password';"

# Grant privileges
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE flaship1 TO postgres;"
```

## 🧪 **Step 4: Test Database Connection**

```bash
# Test connection with password
PGPASSWORD=your-secure-password psql -h localhost -U postgres -d flaship1 -c "SELECT version();"

# Or test without password (if configured)
psql -h localhost -U postgres -d flaship1 -c "SELECT version();"
```

## ⚙️ **Step 5: Configure PostgreSQL (Optional)**

### **Edit PostgreSQL Configuration**

```bash
# Edit postgresql.conf
sudo nano /etc/postgresql/*/main/postgresql.conf

# Edit pg_hba.conf for authentication
sudo nano /etc/postgresql/*/main/pg_hba.conf
```

### **Common Configuration Changes**

```bash
# In postgresql.conf, you might want to change:
max_connections = 200
shared_buffers = 256MB
effective_cache_size = 1GB

# In pg_hba.conf, ensure you have:
local   all             postgres                                md5
host    all             all             127.0.0.1/32            md5
host    all             all             ::1/128                 md5
```

### **Restart PostgreSQL after changes**

```bash
sudo systemctl restart postgresql
```

## 🔐 **Step 6: Update GitHub Secrets**

After creating your database, update these GitHub secrets:

```
UCA_DB_NAME: flaship1
UCA_DB_USER: postgres
UCA_DB_PASSWORD: your-secure-password
UCA_DB_HOST: 127.0.0.1
UCA_DB_PORT: 5432
```

## 🚀 **Step 7: Test with Django**

```bash
# Navigate to your project directory
cd /var/www/uca_app

# Activate virtual environment
source venv/bin/activate

# Test Django database connection
python manage.py check --settings=uca_project.settings_production

# Run migrations
python manage.py migrate --settings=uca_project.settings_production
```

## 🔍 **Useful PostgreSQL Commands**

### **Database Management**
```bash
# List all databases
sudo -u postgres psql -c "\l"

# List all users
sudo -u postgres psql -c "\du"

# Connect to specific database
sudo -u postgres psql -d flaship1

# Drop database (if needed)
sudo -u postgres psql -c "DROP DATABASE flaship1;"

# Drop user (if needed)
sudo -u postgres psql -c "DROP USER postgres;"
```

### **Inside psql**
```sql
-- List databases
\l

-- List users
\du

-- Connect to database
\c flaship1

-- List tables
\dt

-- Describe table
\d table_name

-- Exit
\q
```

## 🛠️ **Troubleshooting**

### **Common Issues**

1. **"Peer authentication failed"**
   ```bash
   # Edit pg_hba.conf
   sudo nano /etc/postgresql/*/main/pg_hba.conf
   
   # Change this line:
   local   all             postgres                                peer
   # To this:
   local   all             postgres                                md5
   
   # Restart PostgreSQL
   sudo systemctl restart postgresql
   ```

2. **"Database does not exist"**
   ```bash
   # Create the database
   sudo -u postgres createdb flaship1
   ```

3. **"User does not exist"**
   ```bash
   # Create the user
   sudo -u postgres createuser postgres
   ```

4. **"Permission denied"**
   ```bash
   # Grant privileges
   sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE flaship1 TO postgres;"
   ```

### **Check PostgreSQL Status**
```bash
# Check if PostgreSQL is running
sudo systemctl status postgresql

# Check PostgreSQL version
sudo -u postgres psql -c "SELECT version();"

# Check active connections
sudo -u postgres psql -c "SELECT * FROM pg_stat_activity;"
```

## 📋 **Quick Setup Script**

Here's a complete script to set up your database:

```bash
#!/bin/bash
# Save this as setup_db.sh and run: chmod +x setup_db.sh && ./setup_db.sh

# Install PostgreSQL
sudo apt update
sudo apt install -y postgresql postgresql-contrib

# Start PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
sudo -u postgres psql -c "CREATE DATABASE flaship1;"
sudo -u postgres psql -c "CREATE USER postgres WITH PASSWORD 'your-secure-password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE flaship1 TO postgres;"
sudo -u postgres psql -c "ALTER USER postgres CREATEDB;"

# Test connection
PGPASSWORD=your-secure-password psql -h localhost -U postgres -d flaship1 -c "SELECT version();"

echo "Database setup completed!"
echo "Update your GitHub secrets with:"
echo "UCA_DB_NAME: flaship1"
echo "UCA_DB_USER: postgres"
echo "UCA_DB_PASSWORD: your-secure-password"
echo "UCA_DB_HOST: 127.0.0.1"
echo "UCA_DB_PORT: 5432"
```

## 🎯 **Next Steps**

1. **Create your database** using the steps above
2. **Update GitHub secrets** with your database credentials
3. **Deploy your app** - the GitHub Actions will handle the rest
4. **Test your application** to ensure everything works

Your database will be ready for the UCA app deployment! 🚀
