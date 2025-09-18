# GitHub Secrets Configuration Guide

This guide explains how to set up GitHub secrets for automated SSH deployment of your UCA App.

## Required GitHub Secrets

Go to your GitHub repository → Settings → Secrets and variables → Actions → New repository secret

### 1. SSH Connection Secrets

| Secret Name | Description | Example Value |
|-------------|-------------|---------------|
| `SSH_HOST` | Your server's IP address or domain | `192.168.1.100` or `your-server.com` |
| `SSH_USERNAME` | SSH username for your server | `ubuntu` or `root` |
| `SSH_PRIVATE_KEY` | Your private SSH key content | `-----BEGIN OPENSSH PRIVATE KEY-----...` |
| `SSH_PORT` | SSH port (usually 22) | `22` |
| `PROJECT_PATH` | Path to your project on the server | `/var/www/uca_app` |

### 2. Django Application Secrets

| Secret Name | Description | Example Value |
|-------------|-------------|---------------|
| `SECRET_KEY` | Django secret key | `django-insecure-your-very-long-secret-key-here` |
| `DEBUG` | Debug mode (should be False) | `False` |
| `ALLOWED_HOSTS` | Comma-separated list of allowed hosts | `your-domain.com,www.your-domain.com` |
| `DATABASE_URL` | PostgreSQL database URL | `postgresql://uca_app_user:password@localhost:5432/uca_app_db` |

### 3. Email Configuration (Optional)

| Secret Name | Description | Example Value |
|-------------|-------------|---------------|
| `EMAIL_HOST` | SMTP server | `smtp.gmail.com` |
| `EMAIL_PORT` | SMTP port | `587` |
| `EMAIL_USE_TLS` | Use TLS | `True` |
| `EMAIL_HOST_USER` | Your email | `your-email@gmail.com` |
| `EMAIL_HOST_PASSWORD` | App password | `your-app-password` |

## How to Generate Required Values

### 1. Generate Django Secret Key

```python
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
```

Or use this online generator: https://djecrety.ir/

### 2. Generate SSH Key Pair

```bash
# Generate SSH key pair
ssh-keygen -t rsa -b 4096 -C "your-email@example.com"

# Copy public key to server
ssh-copy-id -i ~/.ssh/id_rsa.pub username@your-server.com

# Copy private key content for GitHub secret
cat ~/.ssh/id_rsa
```

### 3. Database URL Format

```
postgresql://username:password@host:port/database_name
```

Example:
```
postgresql://uca_app_user:my_secure_password@localhost:5432/uca_app_db
```

## Setting Up GitHub Secrets

1. **Go to your GitHub repository**
2. **Click on "Settings" tab**
3. **Navigate to "Secrets and variables" → "Actions"**
4. **Click "New repository secret"**
5. **Add each secret one by one using the table above**

## Security Best Practices

### ✅ Do's
- Use strong, unique passwords
- Generate a new Django secret key for production
- Use SSH key authentication instead of passwords
- Regularly rotate your secrets
- Use environment-specific values

### ❌ Don'ts
- Don't use the same secret key for development and production
- Don't commit secrets to your repository
- Don't use weak passwords
- Don't share secrets in plain text

## Testing Your Setup

After setting up all secrets:

1. **Push a commit to the main branch**
2. **Check the Actions tab in GitHub**
3. **Monitor the deployment logs**
4. **Verify your application is running**

## Troubleshooting

### Common Issues

1. **SSH Connection Failed**
   - Verify SSH_HOST and SSH_PORT are correct
   - Check if SSH key is properly added to server
   - Ensure SSH service is running on server

2. **Permission Denied**
   - Check SSH_USERNAME is correct
   - Verify SSH_PRIVATE_KEY is complete (including headers)
   - Ensure user has proper permissions on PROJECT_PATH

3. **Database Connection Failed**
   - Verify DATABASE_URL format
   - Check if PostgreSQL is running
   - Ensure database and user exist

4. **Static Files Not Loading**
   - Check if collectstatic ran successfully
   - Verify STATIC_ROOT path in settings
   - Check nginx configuration

### Debug Commands

```bash
# Check service status
sudo systemctl status uca_app
sudo systemctl status nginx

# Check logs
sudo journalctl -u uca_app -f
sudo tail -f /var/log/nginx/error.log

# Test Django
cd /var/www/uca_app
source venv/bin/activate
python manage.py check --settings=uca_project.settings_production
```

## Next Steps

1. Set up all GitHub secrets
2. Run the initial server setup script
3. Configure your domain and SSL certificates
4. Test the deployment workflow
5. Monitor your application

For more help, check the main deployment guide or contact support.
