# 🚀 Hostinger VPS Setup for UCA App on cat.xri-lab.com

## 🎯 **Your Setup Overview**

- **Server**: Hostinger VPS with Kali Linux
- **Domain**: www.xri-lab.com
- **Subdomain**: cat.xri-lab.com
- **App**: UCA Django Application

## 📋 **Step 1: Hostinger VPS Configuration**

### **Initial Server Setup**

```bash
# Connect to your Hostinger VPS
ssh root@your-hostinger-ip

# Update Kali Linux (similar to Ubuntu but uses apt)
apt update && apt upgrade -y

# Install essential packages for Kali Linux
apt install -y python3 python3-pip python3-venv python3-dev nginx postgresql postgresql-contrib git curl certbot python3-certbot-nginx build-essential libpq-dev

# Install Node.js (for Kaleido dependencies)
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt install nodejs -y

# Create project directory
mkdir -p /var/www/uca_app
chown www-data:www-data /var/www/uca_app
```

### **PostgreSQL Setup**

```bash
# Start PostgreSQL service
systemctl start postgresql
systemctl enable postgresql

# Create database and user
sudo -u postgres psql -c "CREATE DATABASE uca_app;"
sudo -u postgres psql -c "CREATE USER uca_user WITH PASSWORD 'UCA_2024_Secure!';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE uca_app TO uca_user;"
sudo -u postgres psql -c "ALTER USER uca_user CREATEDB;"
```

## 🌐 **Step 2: Subdomain Configuration**

### **DNS Configuration in Hostinger**

1. **Login to Hostinger Control Panel**
2. **Go to DNS Zone Editor**
3. **Add these DNS records**:

```
Type: A
Name: cat
Value: YOUR_HOSTINGER_VPS_IP
TTL: 300

Type: A
Name: www.cat
Value: YOUR_HOSTINGER_VPS_IP
TTL: 300
```

### **Verify DNS Propagation**

```bash
# Check if subdomain resolves
nslookup cat.xri-lab.com
nslookup www.cat.xri-lab.com

# Should return your Hostinger VPS IP
```

## 🔧 **Step 3: Nginx Configuration for Subdomain**

Create Nginx configuration for your subdomain:

```bash
# Create Nginx configuration
nano /etc/nginx/sites-available/cat.xri-lab.com
```

Add this configuration:

```nginx
server {
    listen 80;
    server_name cat.xri-lab.com www.cat.xri-lab.com;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
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
```

Enable the site:

```bash
# Enable the site
ln -s /etc/nginx/sites-available/cat.xri-lab.com /etc/nginx/sites-enabled/

# Remove default site
rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
nginx -t

# Restart Nginx
systemctl restart nginx
systemctl enable nginx
```

## 🔐 **Step 4: GitHub Secrets Configuration**

Go to your GitHub repository → **Settings** → **Secrets and variables** → **Actions**

Add these secrets:

| Secret Name | Value | Description |
|-------------|-------|-------------|
| `SERVER_HOST` | `YOUR_HOSTINGER_VPS_IP` | Your Hostinger VPS IP address |
| `SERVER_USER` | `root` | SSH username (usually root for VPS) |
| `SERVER_PASSWORD` | `YOUR_VPS_PASSWORD` | Your VPS password |
| `SERVER_PORT` | `22` | SSH port (usually 22) |
| `UCA_SECRET_KEY` | `GENERATED_SECRET_KEY` | Django secret key |
| `UCA_ALLOWED_HOSTS` | `cat.xri-lab.com,www.cat.xri-lab.com` | Your subdomain |
| `UCA_DOMAIN` | `cat.xri-lab.com` | Domain for SSL certificate |
| `UCA_EMAIL_HOST_USER` | `your-email@gmail.com` | Your email (optional) |
| `UCA_EMAIL_HOST_PASSWORD` | `your-app-password` | Email app password (optional) |

### **Generate Django Secret Key**

```python
# Run this in Python to generate a secret key:
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
```

## 🚀 **Step 5: Deploy Your Application**

### **Method 1: Automatic Deployment (Recommended)**

1. **Push any commit** to your main branch
2. **Go to Actions tab** in GitHub
3. **Watch the deployment process**
4. **Your app will be available at**: `http://cat.xri-lab.com`

### **Method 2: Manual Deployment**

```bash
# Clone your repository
cd /var/www/uca_app
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git .

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cat > .env << EOF
SECRET_KEY=your-generated-secret-key
DEBUG=False
ALLOWED_HOSTS=cat.xri-lab.com,www.cat.xri-lab.com
EOF

# Run migrations
python manage.py migrate --settings=uca_project.settings_production

# Collect static files
python manage.py collectstatic --noinput --settings=uca_project.settings_production

# Create superuser
python manage.py createsuperuser --settings=uca_project.settings_production
```

## 🔒 **Step 6: SSL Certificate Setup**

```bash
# Generate SSL certificate for your subdomain
certbot --nginx -d cat.xri-lab.com -d www.cat.xri-lab.com

# Auto-renewal setup
crontab -e
# Add this line:
0 12 * * * /usr/bin/certbot renew --quiet
```

## 🔧 **Step 7: Gunicorn Service Setup**

Create systemd service:

```bash
# Create service file
nano /etc/systemd/system/uca_app.service
```

Add this content:

```ini
[Unit]
Description=UCA App Django Application
After=network.target postgresql.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/uca_app
Environment="PATH=/var/www/uca_app/venv/bin"
Environment="DJANGO_SETTINGS_MODULE=uca_project.settings_production"
ExecStart=/var/www/uca_app/venv/bin/gunicorn --config /var/www/uca_app/gunicorn_uca_app.conf.py uca_project.wsgi:application
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Enable and start service:

```bash
# Enable service
systemctl daemon-reload
systemctl enable uca_app
systemctl start uca_app

# Check status
systemctl status uca_app
```

## 🔥 **Step 8: Firewall Configuration**

```bash
# Enable UFW firewall
ufw enable

# Allow necessary ports
ufw allow ssh
ufw allow 80
ufw allow 443

# Check status
ufw status
```

## 🎯 **Step 9: Test Your Deployment**

1. **Visit your subdomain**: `http://cat.xri-lab.com`
2. **Check admin panel**: `http://cat.xri-lab.com/admin/`
3. **Default login**: username=`admin`, password=`admin123`
4. **Test SSL**: `https://cat.xri-lab.com` (after SSL setup)

## 🚨 **Troubleshooting**

### **Common Issues:**

1. **Subdomain not resolving**:
   ```bash
   # Check DNS propagation
   nslookup cat.xri-lab.com
   
   # Wait up to 24 hours for DNS propagation
   ```

2. **Nginx not starting**:
   ```bash
   # Check configuration
   nginx -t
   
   # Check logs
   tail -f /var/log/nginx/error.log
   ```

3. **Django app not loading**:
   ```bash
   # Check service status
   systemctl status uca_app
   
   # Check logs
   journalctl -u uca_app -f
   ```

4. **Database connection issues**:
   ```bash
   # Check PostgreSQL status
   systemctl status postgresql
   
   # Test connection
   sudo -u postgres psql -c "SELECT version();"
   ```

### **Useful Commands:**

```bash
# Restart services
systemctl restart uca_app
systemctl restart nginx
systemctl restart postgresql

# Check logs
journalctl -u uca_app -f
tail -f /var/log/nginx/error.log

# Check processes
ps aux | grep gunicorn
netstat -tlnp | grep 2287
```

## 📊 **Monitoring Your App**

### **Check Application Status**

```bash
# Service status
systemctl status uca_app
systemctl status nginx
systemctl status postgresql

# Application logs
journalctl -u uca_app --since "1 hour ago"

# Nginx logs
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

### **Performance Monitoring**

```bash
# System resources
htop
df -h
free -h

# Network connections
netstat -tlnp
ss -tlnp
```

## 🎉 **Success!**

Your UCA application should now be running at:
- **HTTP**: `http://cat.xri-lab.com`
- **HTTPS**: `https://cat.xri-lab.com` (after SSL setup)
- **Admin**: `https://cat.xri-lab.com/admin/`

## 📞 **Need Help?**

If you encounter issues:

1. **Check GitHub Actions logs** for deployment errors
2. **Verify all GitHub secrets** are set correctly
3. **Test SSH connection** to your Hostinger VPS
4. **Check DNS propagation** for your subdomain
5. **Review service logs** for specific errors

Your UCA app is now deployed on your subdomain! 🚀
