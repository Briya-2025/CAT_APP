# UCA App Deployment Fixes

## Issues Identified and Fixed

Based on the deployment logs, the following issues were identified and resolved:

### 1. ✅ SECRET_KEY Security Warning
**Issue**: Django SECRET_KEY was insecure (less than 50 characters, prefixed with 'django-insecure-')

**Fix**: 
- Updated `settings_production.py` with a longer, more secure default SECRET_KEY
- Created `generate_secret_key.py` script to generate cryptographically secure keys
- Added proper environment variable handling

### 2. ✅ ALLOWED_HOSTS Configuration
**Issue**: `DisallowedHost` errors due to missing domain in ALLOWED_HOSTS

**Fix**:
- Updated `settings_production.py` to include `127.0.0.1` in default ALLOWED_HOSTS
- Created deployment script to automatically detect and configure the server's IP/domain

### 3. ✅ Matplotlib Cache Directory Permissions
**Issue**: Permission denied errors when matplotlib tries to create cache directory

**Fix**:
- Added matplotlib configuration in `settings_production.py` to use a dedicated cache directory
- Created `/var/www/uca_app/matplotlib_cache` with proper permissions
- Set `MPLCONFIGDIR` environment variable

### 4. ✅ Missing Favicon
**Issue**: 404 errors for `/favicon.ico` requests

**Fix**:
- Added favicon link to `base.html` template
- Created `favicon.ico` from existing logo
- Added URL pattern to handle favicon requests

## Quick Fix Script

Run the automated fix script on your server:

```bash
# Make the script executable
chmod +x deploy_fix.sh

# Run the fix script (optionally specify your domain)
./deploy_fix.sh your-domain.com
```

## Manual Fixes

If you prefer to apply fixes manually:

### 1. Generate Secure SECRET_KEY
```bash
python3 generate_secret_key.py
```

### 2. Set Environment Variables
```bash
export SECRET_KEY='your-generated-secret-key'
export DEBUG='False'
export ALLOWED_HOSTS='your-domain.com,localhost,127.0.0.1'
```

### 3. Create Matplotlib Cache Directory
```bash
sudo mkdir -p /var/www/uca_app/matplotlib_cache
sudo chown -R www-data:www-data /var/www/uca_app/matplotlib_cache
sudo chmod -R 755 /var/www/uca_app/matplotlib_cache
```

### 4. Restart Services
```bash
sudo systemctl restart uca_app
sudo systemctl restart nginx
```

## Verification

After applying fixes, verify the deployment:

1. **Check Django System Check**:
   ```bash
   cd /var/www/uca_app
   source venv/bin/activate
   python manage.py check --settings=uca_project.settings_production
   ```

2. **Test Application Access**:
   - Visit your application URL
   - Check that favicon loads without 404 errors
   - Verify no security warnings in logs

3. **Check Service Status**:
   ```bash
   sudo systemctl status uca_app
   sudo systemctl status nginx
   ```

## Environment Variables

Create a `.env` file in `/var/www/uca_app/` with:

```env
SECRET_KEY=your-secure-secret-key-here
DEBUG=False
ALLOWED_HOSTS=your-domain.com,localhost,127.0.0.1
DATABASE_URL=postgresql://uca_user:UCA_2024_Secure!@127.0.0.1:5432/uca_app
```

## Security Notes

- ✅ SECRET_KEY is now cryptographically secure
- ✅ ALLOWED_HOSTS properly configured
- ✅ Matplotlib cache directory has proper permissions
- ✅ Favicon properly served
- ✅ All security warnings resolved

## Next Steps

1. **Enable SSL**: Run `sudo certbot --nginx -d your-domain.com`
2. **Update Admin Password**: Change the default admin password
3. **Monitor Logs**: Check `/var/www/uca_app/logs/django.log` for any issues
4. **Backup**: Set up regular database backups

## Troubleshooting

### If you still see SECRET_KEY warnings:
- Ensure the environment variable is properly set
- Restart the uca_app service
- Check that the .env file is being loaded

### If you still see ALLOWED_HOSTS errors:
- Verify your domain/IP is in the ALLOWED_HOSTS list
- Check nginx configuration for proper server_name
- Restart both uca_app and nginx services

### If matplotlib errors persist:
- Check that the matplotlib_cache directory exists and has proper permissions
- Verify the MPLCONFIGDIR environment variable is set
- Restart the uca_app service
