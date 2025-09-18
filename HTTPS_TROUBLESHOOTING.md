# HTTPS Troubleshooting Guide for UCA App

## Issues Fixed

### 1. Port Mismatch
- **Problem**: Nginx was configured for port 2287 but service was running on port 3498
- **Solution**: Updated both `uca_app.service` and `gunicorn.conf.py` to use port 2287

### 2. HTTPS Environment Variable
- **Problem**: `USE_HTTPS` was not set to `True` in Django settings
- **Solution**: Created `.env` file with `USE_HTTPS=True`

### 3. SSL Certificate Configuration
- **Problem**: SSL certificate paths were not properly configured
- **Solution**: Updated nginx configuration with correct Let's Encrypt paths

### 4. Domain Configuration
- **Problem**: Nginx was configured for `ihsstores.com` instead of your actual domain
- **Solution**: Created template configuration that gets updated with your domain

## Deployment Options

### Option 1: Quick Fix (Recommended if app is already deployed)
```bash
sudo ./quick_https_fix.sh your-domain.com
```

### Option 2: Complete Setup (For fresh deployment)
```bash
sudo ./deploy_https_fixed.sh your-domain.com your-email@domain.com
```

### Option 3: HTTPS Only Setup (If app is deployed but HTTPS is broken)
```bash
sudo ./setup_https_fixed.sh your-domain.com your-email@domain.com
```

## Port Configuration to Avoid Conflicts

Your UCA App is configured to use:
- **Port 2287**: Django/Gunicorn application
- **Port 80**: HTTP (redirects to HTTPS)
- **Port 443**: HTTPS

This ensures no conflicts with your other 5 projects.

## Verification Steps

### 1. Check Service Status
```bash
sudo systemctl status nginx
sudo systemctl status uca_app
```

### 2. Check Port Usage
```bash
sudo netstat -tlnp | grep -E ":(80|443|2287) "
```

### 3. Test HTTPS
```bash
curl -I https://your-domain.com
```

### 4. Check SSL Certificate
```bash
sudo certbot certificates
```

### 5. Check Nginx Configuration
```bash
sudo nginx -t
```

## Common Issues and Solutions

### Issue: "Port already in use"
**Solution**: Check what's using the port and either stop that service or change the port in your configuration.

### Issue: "SSL certificate not found"
**Solution**: Run the certbot command manually:
```bash
sudo certbot certonly --standalone -d your-domain.com -d www.your-domain.com
```

### Issue: "Nginx configuration test failed"
**Solution**: Check the nginx configuration syntax:
```bash
sudo nginx -t
sudo tail -f /var/log/nginx/error.log
```

### Issue: "Django not responding"
**Solution**: Check the Django service:
```bash
sudo journalctl -u uca_app -f
```

### Issue: "Mixed content warnings"
**Solution**: Ensure `USE_HTTPS=True` is set in your environment and Django is configured properly.

## Environment Variables

Create or update `/var/www/uca_app/.env`:
```bash
USE_HTTPS=True
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
DEBUG=False
```

## Nginx Configuration

The nginx configuration includes:
- HTTP to HTTPS redirect
- SSL security headers
- Static file serving
- Proxy configuration for Django
- Security measures (deny access to sensitive files)

## Automatic Certificate Renewal

Certificates are set to auto-renew every 90 days via cron job:
```bash
0 12 * * * /usr/bin/certbot renew --quiet --post-hook 'systemctl reload nginx'
```

## Log Files

- **Nginx Access Log**: `/var/log/nginx/access.log`
- **Nginx Error Log**: `/var/log/nginx/error.log`
- **Django Log**: `/var/www/uca_app/logs/django.log`
- **UCA App Service Log**: `sudo journalctl -u uca_app`

## Security Features

- HSTS (HTTP Strict Transport Security)
- X-Frame-Options
- X-Content-Type-Options
- X-XSS-Protection
- Referrer-Policy
- SSL/TLS 1.2 and 1.3 only
- Strong cipher suites

## Testing Your Setup

1. **HTTP Redirect Test**:
   ```bash
   curl -I http://your-domain.com
   # Should return 301 redirect to HTTPS
   ```

2. **HTTPS Test**:
   ```bash
   curl -I https://your-domain.com
   # Should return 200 OK
   ```

3. **SSL Test**:
   ```bash
   openssl s_client -connect your-domain.com:443 -servername your-domain.com
   ```

## Support

If you encounter issues:
1. Check the logs mentioned above
2. Verify your domain DNS is pointing to your server
3. Ensure ports 80 and 443 are open in your firewall
4. Check that your domain is not already configured in other nginx sites
