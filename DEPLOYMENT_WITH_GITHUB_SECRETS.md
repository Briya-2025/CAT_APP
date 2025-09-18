# 🚀 UCA App Deployment with GitHub Secrets

## 📋 **Complete Deployment Guide**

Your UCA application is ready for deployment! Here's everything you need to know.

## 🔐 **Required GitHub Secrets**

Go to your GitHub repository → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

### **1. Server Connection Secrets**

| Secret Name | Description | Example Value |
|-------------|-------------|---------------|
| `SERVER_HOST` | Your server's IP address or domain | `192.168.1.100` or `your-server.com` |
| `SERVER_USER` | SSH username | `ubuntu`, `root`, or `debian` |
| `SERVER_PASSWORD` | SSH password | `YourSecurePassword123!` |
| `SERVER_PORT` | SSH port (usually 22) | `22` |

### **2. Django Application Secrets**

| Secret Name | Description | Example Value |
|-------------|-------------|---------------|
| `UCA_SECRET_KEY` | Django secret key | `django-insecure-abc123...` |
| `UCA_ALLOWED_HOSTS` | Allowed domains/IPs | `your-domain.com,www.your-domain.com` |
| `UCA_DOMAIN` | Domain for SSL certificate | `your-domain.com` |

### **3. Email Configuration (Optional)**

| Secret Name | Description | Example Value |
|-------------|-------------|---------------|
| `UCA_EMAIL_HOST_USER` | Your email address | `admin@your-domain.com` |
| `UCA_EMAIL_HOST_PASSWORD` | Email app password | `your-gmail-app-password` |

## 🛠️ **Step-by-Step Deployment Process**

### **Step 1: Generate Django Secret Key**

```python
# Run this in Python to generate a secret key:
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
```

### **Step 2: Set Up Your Server**

Your server needs:
- Ubuntu/Debian Linux
- Root or sudo access
- Internet connection
- Domain pointing to server IP (optional)

### **Step 3: Configure GitHub Secrets**

1. Go to your GitHub repository
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Add each secret from the table above

### **Step 4: Deploy**

1. Push any commit to the `main` branch
2. Go to **Actions** tab in GitHub
3. Watch the deployment process
4. Your app will be available at your domain/IP

## 🔧 **What the Deployment Does Automatically**

✅ **Installs all dependencies** (Python, PostgreSQL, Nginx, etc.)  
✅ **Sets up PostgreSQL database** with user and permissions  
✅ **Configures Django** with production settings  
✅ **Sets up Gunicorn** as WSGI server  
✅ **Configures Nginx** as reverse proxy  
✅ **Generates SSL certificate** (if domain provided)  
✅ **Creates systemd service** for auto-start  
✅ **Sets up logging** and monitoring  

## 📊 **Application Features**

Your deployed UCA app includes:

- **Course Management**: Create and manage courses
- **Section Management**: Handle multiple sections per course
- **Assessment Tracking**: Track quizzes, assignments, exams
- **Statistical Analysis**: Interactive charts and reports
- **PDF Report Generation**: Professional PDF reports
- **Grade Distribution**: Visual grade analysis
- **Admin Interface**: Full Django admin access

## 🌐 **Access Your Application**

After deployment:

- **Main App**: `http://your-domain.com` or `http://your-server-ip`
- **Admin Panel**: `http://your-domain.com/admin/`
- **Default Admin**: username=`admin`, password=`admin123`

## 🔒 **Security Features**

✅ **HTTPS/SSL** (automatic with Let's Encrypt)  
✅ **CSRF Protection**  
✅ **Secure Session Cookies**  
✅ **Security Headers**  
✅ **Environment Variables** for sensitive data  
✅ **Production Database** (PostgreSQL)  

## 📝 **Post-Deployment Tasks**

1. **Change Admin Password**:
   ```bash
   # SSH into your server
   cd /var/www/uca_app
   source venv/bin/activate
   python manage.py changepassword admin
   ```

2. **Create Additional Users**:
   - Go to `/admin/` → Users → Add user

3. **Configure Email** (if needed):
   - Update email settings in Django admin

4. **Monitor Logs**:
   ```bash
   sudo journalctl -u uca_app -f
   ```

## 🚨 **Troubleshooting**

### **Common Issues:**

1. **Deployment Fails**:
   - Check all GitHub secrets are set correctly
   - Verify server SSH access
   - Check server has internet connection

2. **App Not Loading**:
   - Check service status: `sudo systemctl status uca_app`
   - Check Nginx: `sudo systemctl status nginx`
   - Check logs: `sudo journalctl -u uca_app -f`

3. **SSL Certificate Issues**:
   - Verify domain points to server IP
   - Wait for DNS propagation (up to 24 hours)
   - Check firewall allows ports 80 and 443

### **Useful Commands:**

```bash
# Check service status
sudo systemctl status uca_app
sudo systemctl status nginx

# Restart services
sudo systemctl restart uca_app
sudo systemctl restart nginx

# View logs
sudo journalctl -u uca_app -f
sudo tail -f /var/log/nginx/error.log

# Test Django
cd /var/www/uca_app
source venv/bin/activate
python manage.py check --settings=uca_project.settings_production
```

## 🔄 **Updating Your Application**

To update your app:

1. **Make changes** to your code
2. **Commit and push** to main branch
3. **GitHub Actions** will automatically redeploy
4. **Monitor** the deployment in Actions tab

## 📞 **Support**

If you encounter issues:

1. **Check GitHub Actions logs** for deployment errors
2. **Verify all secrets** are configured correctly
3. **Test SSH connection** to your server manually
4. **Check server resources** (CPU, memory, disk space)

## 🎯 **Quick Checklist**

Before deploying, ensure you have:

- [ ] Server with Ubuntu/Debian and root access
- [ ] Domain pointing to server IP (optional)
- [ ] All GitHub secrets configured
- [ ] Django secret key generated
- [ ] Email app password (if using email features)

**Your UCA application is production-ready!** 🚀
