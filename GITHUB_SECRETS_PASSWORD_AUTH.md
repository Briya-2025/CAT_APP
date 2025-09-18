# GitHub Secrets Configuration Guide - Password Authentication

This guide explains how to set up GitHub secrets for automated deployment using password authentication instead of SSH keys.

## Required GitHub Secrets

Go to your GitHub repository → Settings → Secrets and variables → Actions → New repository secret

### 1. Server Connection Secrets

| Secret Name | Description | Example Value |
|-------------|-------------|---------------|
| `SERVER_HOST` | Your server's IP address or domain | `192.168.1.100` or `your-server.com` |
| `SERVER_USER` | SSH username for your server | `ubuntu` or `root` |
| `SERVER_PASSWORD` | SSH password for your server | `your-server-password` |
| `SERVER_PORT` | SSH port (usually 22) | `22` |

### 2. Django Application Secrets

| Secret Name | Description | Example Value |
|-------------|-------------|---------------|
| `UCA_SECRET_KEY` | Django secret key | `django-insecure-your-very-long-secret-key-here` |
| `UCA_ALLOWED_HOSTS` | Comma-separated list of allowed hosts | `your-domain.com,www.your-domain.com` |
| `UCA_DOMAIN` | Your domain name for SSL | `your-domain.com` |

### 3. Email Configuration (Optional)

| Secret Name | Description | Example Value |
|-------------|-------------|---------------|
| `UCA_EMAIL_HOST_USER` | Your email | `your-email@gmail.com` |
| `UCA_EMAIL_HOST_PASSWORD` | App password | `your-app-password` |

## Database Configuration

The deployment automatically sets up PostgreSQL with these fixed settings:
- **Database Name**: `flaship1`
- **Database User**: `postgres`
- **Database Password**: `1234`
- **Database Host**: `localhost`
- **Database Port**: `5432`

## How to Generate Required Values

### 1. Generate Django Secret Key

```python
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
```

Or use this online generator: https://djecrety.ir/

### 2. Get Your Server Details

- **SERVER_HOST**: Your server's IP address (e.g., `192.168.1.100`) or domain name
- **SERVER_USER**: The username you use to SSH into your server
- **SERVER_PASSWORD**: The password for that user
- **SERVER_PORT**: Usually `22` (default SSH port)

## Setting Up GitHub Secrets

1. **Go to your GitHub repository**
2. **Click on "Settings" tab**
3. **Navigate to "Secrets and variables" → "Actions"**
4. **Click "New repository secret"**
5. **Add each secret one by one using the table above**

## What the Deployment Does

The GitHub Actions workflow will automatically:

1. **Connect to your server** using password authentication
2. **Install all required packages** (Python, Nginx, PostgreSQL, etc.)
3. **Clone your repository** to `/var/www/uca_app`
4. **Set up PostgreSQL database** `flaship1` with user `postgres`
5. **Install Python dependencies** and create virtual environment
6. **Run Django migrations** and collect static files
7. **Create admin user** (username: `admin`, password: `admin123`)
8. **Configure Nginx** as reverse proxy
9. **Set up SSL certificate** with Let's Encrypt (if domain is configured)
10. **Start all services** (Gunicorn + Nginx)

## Security Best Practices

### ✅ Do's
- Use strong, unique passwords for your server
- Generate a new Django secret key for production
- Use a strong password for the admin user
- Regularly update your server packages

### ❌ Don'ts
- Don't use weak passwords
- Don't share server credentials
- Don't commit passwords to your repository
- Don't use the same secret key for development and production

## Testing Your Setup

After setting up all secrets:

1. **Push a commit to the main branch**
2. **Check the Actions tab in GitHub**
3. **Monitor the deployment logs**
4. **Visit your domain** to verify the application is running

## Troubleshooting

### Common Issues

1. **Connection Failed**
   - Verify SERVER_HOST and SERVER_PORT are correct
   - Check if SSH service is running on server
   - Ensure SERVER_USER and SERVER_PASSWORD are correct

2. **Permission Denied**
   - Check if SERVER_USER has sudo privileges
   - Verify the user can create directories in `/var/www/`

3. **Database Connection Failed**
   - Check if PostgreSQL is running
   - Verify database `flaship1` was created successfully

4. **SSL Certificate Failed**
   - Ensure your domain points to your server's IP
   - Check if ports 80 and 443 are open
   - Verify SERVER_DOMAIN is correct

### Debug Commands

```bash
# Check service status
sudo systemctl status uca_app
sudo systemctl status nginx
sudo systemctl status postgresql

# Check logs
sudo journalctl -u uca_app -f
sudo tail -f /var/log/nginx/error.log

# Test database connection
sudo -u postgres psql -d flaship1 -c "SELECT version();"
```

## Post-Deployment

After successful deployment:

1. **Access your application** at `http://your-domain.com`
2. **Login with admin credentials** (username: `admin`, password: `admin123`)
3. **Change the admin password** for security
4. **Test all application features**
5. **Monitor server resources** and logs

## Next Steps

1. Set up all GitHub secrets
2. Push a commit to trigger deployment
3. Monitor the deployment process
4. Test your application
5. Configure additional features as needed

For more help, check the main deployment guide or contact support.
