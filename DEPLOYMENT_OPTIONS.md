# UCA App HTTPS Deployment Options

Based on your server logs, I've identified the specific issues and created multiple deployment options to fix them safely.

## Issues Identified from Your Logs:

1. ❌ **SSL certificate not generated** - "No email provided for SSL certificate"
2. ❌ **Wrong gunicorn config file** - Service is using `gunicorn_uca_app.conf.py` (which doesn't exist)
3. ❌ **Matplotlib permission issues** - Cache directory permissions problem
4. ❌ **Service running on port 2287** - But nginx might not be configured for HTTPS

## Deployment Options:

### Option 1: Fix Existing Issues (Recommended)
**Use this if you want to fix the current setup without creating new files**

```bash
sudo ./fix_existing_issues.sh your-domain.com your-email@domain.com
```

**What it does:**
- ✅ Creates the missing `gunicorn_uca_app.conf.py` file
- ✅ Fixes matplotlib cache directory permissions
- ✅ Gets SSL certificate from Let's Encrypt
- ✅ Creates nginx configuration for HTTPS
- ✅ Sets up environment variables for HTTPS
- ✅ Keeps your existing service running

### Option 2: Safe Deployment (Creates New Files)
**Use this if you want to create new configurations without touching existing ones**

```bash
sudo ./safe_https_deploy.sh your-domain.com your-email@domain.com
```

**What it does:**
- ✅ Creates NEW nginx configuration (`uca_app_https`)
- ✅ Creates NEW gunicorn configuration (`gunicorn_https.conf.py`)
- ✅ Creates NEW systemd service (`uca_app_https.service`)
- ✅ Keeps your original service intact
- ✅ Gets SSL certificate from Let's Encrypt
- ✅ Fixes all permission issues

### Option 3: Quick Fix (Minimal Changes)
**Use this for a minimal fix to existing setup**

```bash
sudo ./quick_https_fix.sh your-domain.com
```

## What Each Script Creates/Fixes:

### fix_existing_issues.sh
- Creates: `/var/www/uca_app/gunicorn_uca_app.conf.py`
- Creates: `/var/www/uca_app/.env`
- Creates: `/etc/nginx/sites-available/uca_app_https`
- Creates: `/var/www/uca_app/matplotlib_cache/` (with proper permissions)
- Gets: SSL certificate from Let's Encrypt

### safe_https_deploy.sh
- Creates: `/etc/nginx/sites-available/uca_app_https`
- Creates: `/var/www/uca_app/gunicorn_https.conf.py`
- Creates: `/etc/systemd/system/uca_app_https.service`
- Creates: `/var/www/uca_app/.env_https`
- Creates: `/var/www/uca_app/matplotlib_cache/` (with proper permissions)
- Gets: SSL certificate from Let's Encrypt

## Port Configuration:

All scripts ensure your UCA App uses **port 2287** to avoid conflicts with your other 5 projects:
- Port 80: HTTP (redirects to HTTPS)
- Port 443: HTTPS
- Port 2287: Django/Gunicorn application

## Environment Variables Set:

```bash
USE_HTTPS=True
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
DEBUG=False
MPLCONFIGDIR=/var/www/uca_app/matplotlib_cache
```

## After Deployment:

### Check Status:
```bash
sudo systemctl status nginx
sudo systemctl status uca_app  # or uca_app_https if using safe deployment
sudo nginx -t
```

### Check Logs:
```bash
sudo journalctl -u uca_app -f  # or uca_app_https
sudo tail -f /var/log/nginx/error.log
```

### Test HTTPS:
```bash
curl -I https://your-domain.com
```

## Troubleshooting:

### If HTTPS still doesn't work:
1. Check if SSL certificate exists:
   ```bash
   sudo certbot certificates
   ```

2. Check nginx configuration:
   ```bash
   sudo nginx -t
   sudo systemctl status nginx
   ```

3. Check if port 2287 is listening:
   ```bash
   sudo netstat -tlnp | grep 2287
   ```

4. Check Django logs:
   ```bash
   sudo journalctl -u uca_app -f
   ```

### If you get permission errors:
```bash
sudo chown -R www-data:www-data /var/www/uca_app
sudo chmod -R 755 /var/www/uca_app
```

## Recommendation:

**Use Option 1 (fix_existing_issues.sh)** as it addresses all the specific issues found in your logs and creates the missing files your service is looking for.

Run this command on your server:
```bash
sudo ./fix_existing_issues.sh your-domain.com your-email@domain.com
```

This will fix all the issues and get HTTPS working properly! 🚀
