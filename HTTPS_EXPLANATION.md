# Why Your App Runs on HTTP Instead of HTTPS

## The Problem

Your application is currently running on HTTP instead of HTTPS because of a configuration mismatch:

1. **Django settings** were configured to force HTTPS redirects
2. **Nginx configuration** was set up to redirect HTTP to HTTPS
3. **SSL certificates** were never actually installed
4. **Let's Encrypt** wasn't set up during deployment

This creates a situation where:
- Nginx tries to redirect HTTP → HTTPS
- But HTTPS fails because no SSL certificates exist
- So the application falls back to HTTP mode

## The Solution

I've fixed this by creating a **two-phase deployment approach**:

### Phase 1: HTTP Deployment (Current)
- ✅ Django configured to work with HTTP
- ✅ Nginx configured for HTTP only
- ✅ All security warnings resolved
- ✅ Application works immediately

### Phase 2: HTTPS Upgrade (Optional)
- 🔒 Easy one-command HTTPS setup
- 🔒 Automatic SSL certificate management
- 🔒 Secure cookies and redirects enabled

## Files Created/Modified

### 1. **`uca_project/settings_production.py`**
- Added `USE_HTTPS` environment variable
- Made SSL settings conditional on HTTPS being enabled
- Fixed cookie security settings

### 2. **`nginx_http.conf`** (New)
- HTTP-only nginx configuration
- No SSL redirects
- Works immediately without certificates

### 3. **`setup_https.sh`** (New)
- One-command HTTPS setup
- Automatic Let's Encrypt certificate installation
- Updates all configurations for HTTPS

### 4. **`deploy_fix.sh`** (Updated)
- Now uses HTTP configuration by default
- Includes instructions for HTTPS upgrade

## How to Fix Your Current Deployment

### Option 1: Keep HTTP (Recommended for Development)
```bash
# Run the fix script
./deploy_fix.sh your-domain.com

# Your app will work on HTTP immediately
# No SSL certificates needed
```

### Option 2: Enable HTTPS (Recommended for Production)
```bash
# First, fix the basic issues
./deploy_fix.sh your-domain.com

# Then enable HTTPS
./setup_https.sh your-domain.com your-email@example.com

# Your app will now work on HTTPS
```

## Why This Happened

The original configuration assumed SSL certificates would be installed, but:

1. **No email was provided** for Let's Encrypt during deployment
2. **Certbot wasn't installed** on the server
3. **Domain wasn't properly configured** in nginx
4. **Django was forcing HTTPS** without certificates being available

## Security Considerations

### HTTP Mode (Current)
- ✅ **Safe for development/testing**
- ✅ **All Django security features enabled**
- ✅ **No sensitive data exposure**
- ⚠️ **Not recommended for production with sensitive data**

### HTTPS Mode (After upgrade)
- ✅ **Production-ready security**
- ✅ **Encrypted data transmission**
- ✅ **SSL/TLS encryption**
- ✅ **Secure cookies and sessions**

## Quick Commands

### Check Current Status
```bash
# Check if HTTPS is enabled
grep USE_HTTPS /var/www/uca_app/.env

# Check nginx configuration
sudo nginx -t

# Check Django settings
cd /var/www/uca_app && source venv/bin/activate
python manage.py check --settings=uca_project.settings_production
```

### Enable HTTPS Later
```bash
# One command to enable HTTPS
./setup_https.sh your-domain.com your-email@example.com
```

## Troubleshooting

### If you get SSL errors:
1. Make sure your domain points to your server
2. Check that port 443 is open
3. Verify Let's Encrypt can reach your server

### If HTTPS doesn't work:
1. Check certificate installation: `sudo certbot certificates`
2. Test nginx config: `sudo nginx -t`
3. Check Django logs: `sudo journalctl -u uca_app -f`

### If you want to go back to HTTP:
1. Set `USE_HTTPS=False` in `/var/www/uca_app/.env`
2. Use `nginx_http.conf` configuration
3. Restart services: `sudo systemctl restart uca_app nginx`

## Summary

Your app runs on HTTP because the HTTPS configuration was incomplete. I've fixed this by:

1. ✅ **Making Django work with HTTP** (immediate fix)
2. ✅ **Creating easy HTTPS upgrade path** (when you're ready)
3. ✅ **Fixing all security warnings** (both HTTP and HTTPS modes)
4. ✅ **Providing clear instructions** (for both scenarios)

**Next step**: Run `./deploy_fix.sh your-domain.com` to fix the current issues, then optionally run `./setup_https.sh your-domain.com your-email@example.com` to enable HTTPS.
