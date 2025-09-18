# Complete GitHub Secrets Setup Guide for UCA App

This guide provides detailed information about all the GitHub secrets you need to configure for your UCA app deployment.

## 🔐 How to Add GitHub Secrets

1. **Go to your GitHub repository**
2. **Click on "Settings" tab** (at the top of your repository)
3. **In the left sidebar, click "Secrets and variables"**
4. **Click "Actions"**
5. **Click "New repository secret"**
6. **Enter the secret name and value**
7. **Click "Add secret"**

## 📋 Required Secrets List

### 1. **SERVER_HOST**
- **Description**: Your server's IP address or domain name
- **Example Values**: 
  - `192.168.1.100` (if using IP address)
  - `your-server.com` (if using domain name)
  - `vps.example.com` (if using VPS domain)
- **How to find**: 
  - Check your server provider's dashboard
  - Run `curl ifconfig.me` on your server
  - Check your domain's DNS settings

### 2. **SERVER_USER**
- **Description**: SSH username for your server
- **Example Values**:
  - `ubuntu` (common for Ubuntu servers)
  - `root` (if you have root access)
  - `debian` (for Debian servers)
  - `centos` (for CentOS servers)
- **How to find**: This is the username you use to SSH into your server

### 3. **SERVER_PASSWORD**
- **Description**: SSH password for your server user
- **Example Values**: Your actual server password
- **Security Note**: Use a strong password with letters, numbers, and symbols
- **How to find**: This is the password you use to SSH into your server

### 4. **SERVER_PORT**
- **Description**: SSH port number
- **Example Values**:
  - `22` (default SSH port)
  - `2222` (if you changed the default port)
  - `2200` (custom SSH port)
- **How to find**: Check your SSH configuration or server provider settings

### 5. **UCA_SECRET_KEY**
- **Description**: Django secret key for security
- **Example Values**: A long random string
- **How to generate**:
  ```python
  from django.core.management.utils import get_random_secret_key
  print(get_random_secret_key())
  ```
  Or use online generator: https://djecrety.ir/
- **Example**: `django-insecure-abc123def456ghi789jkl012mno345pqr678stu901vwx234yz567890`

### 6. **UCA_ALLOWED_HOSTS**
- **Description**: Comma-separated list of allowed hostnames
- **Example Values**:
  - `your-domain.com,www.your-domain.com` (if you have a domain)
  - `192.168.1.100` (if using IP address)
  - `your-domain.com,www.your-domain.com,192.168.1.100` (multiple hosts)
- **How to find**: Your domain name or server IP address

### 7. **UCA_DOMAIN**
- **Description**: Your domain name for SSL certificate
- **Example Values**:
  - `your-domain.com`
  - `uca-app.com`
  - `my-uca-app.net`
- **How to find**: The domain name you want to use for your application
- **Note**: This domain must point to your server's IP address

### 8. **UCA_EMAIL_HOST_USER** (Optional)
- **Description**: Your email address for notifications
- **Example Values**:
  - `your-email@gmail.com`
  - `admin@your-domain.com`
  - `notifications@your-company.com`
- **How to find**: Your email address

### 9. **UCA_EMAIL_HOST_PASSWORD** (Optional)
- **Description**: App password for your email
- **Example Values**: Your email app password
- **How to find**: 
  - For Gmail: Generate an app password in Google Account settings
  - For other providers: Check their app password settings
- **Note**: This is NOT your regular email password

## 🛠️ Step-by-Step Setup Process

### Step 1: Gather Your Server Information
```bash
# On your server, run these commands to get information:
hostname -I  # Get IP address
whoami      # Get current user
echo $SSH_PORT  # Get SSH port (if set)
```

### Step 2: Generate Django Secret Key
```python
# Run this Python code to generate a secret key:
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
```

### Step 3: Set Up Domain (if using one)
- Point your domain's A record to your server's IP address
- Wait for DNS propagation (can take up to 24 hours)

### Step 4: Add Secrets to GitHub
1. Go to your repository → Settings → Secrets and variables → Actions
2. Add each secret one by one using the information above

## 🔍 Example Secret Values

Here's an example of what your secrets might look like:

```
SERVER_HOST: 192.168.1.100
SERVER_USER: ubuntu
SERVER_PASSWORD: MySecurePassword123!
SERVER_PORT: 22
UCA_SECRET_KEY: django-insecure-abc123def456ghi789jkl012mno345pqr678stu901vwx234yz567890
UCA_ALLOWED_HOSTS: my-uca-app.com,www.my-uca-app.com
UCA_DOMAIN: my-uca-app.com
UCA_EMAIL_HOST_USER: admin@my-uca-app.com
UCA_EMAIL_HOST_PASSWORD: my-gmail-app-password
```

## ⚠️ Security Best Practices

### ✅ Do's
- Use strong, unique passwords
- Generate a new secret key for production
- Use app passwords for email (not regular passwords)
- Regularly rotate your secrets
- Use environment-specific values

### ❌ Don'ts
- Don't use weak passwords
- Don't share secrets in plain text
- Don't commit secrets to your repository
- Don't use the same secret key for development and production
- Don't use your regular email password for SMTP

## 🧪 Testing Your Secrets

After setting up all secrets:

1. **Push a commit** to your main branch
2. **Go to Actions tab** in your GitHub repository
3. **Click on the running workflow**
4. **Monitor the deployment logs**
5. **Check for any errors** related to secrets

## 🔧 Troubleshooting Common Issues

### Issue: "Connection refused"
- **Check**: SERVER_HOST and SERVER_PORT are correct
- **Solution**: Verify your server is running and accessible

### Issue: "Authentication failed"
- **Check**: SERVER_USER and SERVER_PASSWORD are correct
- **Solution**: Test SSH connection manually

### Issue: "SSL certificate generation failed"
- **Check**: UCA_DOMAIN points to your server's IP
- **Solution**: Verify DNS settings and wait for propagation

### Issue: "Database connection failed"
- **Check**: PostgreSQL is running on your server
- **Solution**: The deployment script will set this up automatically

## 📞 Need Help?

If you encounter issues:

1. **Check the deployment logs** in GitHub Actions
2. **Verify all secrets are set correctly**
3. **Test SSH connection manually** to your server
4. **Check your server's firewall settings**
5. **Verify your domain DNS settings**

## 🎯 Quick Checklist

Before deploying, make sure you have:

- [ ] SERVER_HOST (your server IP or domain)
- [ ] SERVER_USER (SSH username)
- [ ] SERVER_PASSWORD (SSH password)
- [ ] SERVER_PORT (SSH port, usually 22)
- [ ] UCA_SECRET_KEY (generated Django secret key)
- [ ] UCA_ALLOWED_HOSTS (your domain or IP)
- [ ] UCA_DOMAIN (for SSL certificate)
- [ ] UCA_EMAIL_HOST_USER (optional, your email)
- [ ] UCA_EMAIL_HOST_PASSWORD (optional, email app password)

Once all secrets are configured, your deployment will be fully automated!
