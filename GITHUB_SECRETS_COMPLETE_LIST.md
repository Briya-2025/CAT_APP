# Complete GitHub Secrets List for UCA App

This guide provides the complete list of all GitHub secrets required for your UCA app deployment.

## 🔐 **All Required GitHub Secrets**

### **1. Server Connection (4 Required)**
| Secret Name | Description | Example Value |
|-------------|-------------|---------------|
| `SERVER_HOST` | Your server's IP address or domain | `192.168.1.100` or `your-server.com` |
| `SERVER_USER` | SSH username for your server | `ubuntu` or `root` |
| `SERVER_PASSWORD` | SSH password for your server | `your-server-password` |
| `SERVER_PORT` | SSH port (usually 22) | `22` |

### **2. Django Application (3 Required)**
| Secret Name | Description | Example Value |
|-------------|-------------|---------------|
| `UCA_SECRET_KEY` | Django secret key | `@fb$xo@)5s=&gwjpdk76ii*tl_6)z=s3lf1)8h+2sw1!)(iu&z` |
| `UCA_ALLOWED_HOSTS` | Comma-separated list of allowed hosts | `www.ihsstores.com,ihsstores.com` |
| `UCA_DOMAIN` | Your domain for SSL certificate | `ihsstores.com` |

### **3. Database Configuration (5 Required)**
| Secret Name | Description | Example Value |
|-------------|-------------|---------------|
| `UCA_DB_NAME` | PostgreSQL database name | `flaship1` |
| `UCA_DB_USER` | PostgreSQL username | `postgres` |
| `UCA_DB_PASSWORD` | PostgreSQL password | `your-secure-db-password` |
| `UCA_DB_HOST` | Database host | `127.0.0.1` or `localhost` |
| `UCA_DB_PORT` | Database port | `5432` |

### **4. Email Configuration (2 Optional)**
| Secret Name | Description | Example Value |
|-------------|-------------|---------------|
| `UCA_EMAIL_HOST_USER` | Your email address | `admin@ihsstores.com` |
| `UCA_EMAIL_HOST_PASSWORD` | Email app password | `your-gmail-app-password` |

## 📋 **Complete Example Configuration**

Here's what all your secrets should look like:

```
# Server Connection
SERVER_HOST: 192.168.1.100
SERVER_USER: ubuntu
SERVER_PASSWORD: MySecurePassword123!
SERVER_PORT: 22

# Django Application
UCA_SECRET_KEY: @fb$xo@)5s=&gwjpdk76ii*tl_6)z=s3lf1)8h+2sw1!)(iu&z
UCA_ALLOWED_HOSTS: www.ihsstores.com,ihsstores.com
UCA_DOMAIN: ihsstores.com

# Database Configuration
UCA_DB_NAME: flaship1
UCA_DB_USER: postgres
UCA_DB_PASSWORD: MySecureDBPassword123!
UCA_DB_HOST: 127.0.0.1
UCA_DB_PORT: 5432

# Email Configuration (Optional)
UCA_EMAIL_HOST_USER: admin@ihsstores.com
UCA_EMAIL_HOST_PASSWORD: your-gmail-app-password
```

## 🚀 **How to Set Up GitHub Secrets**

1. **Go to your repository**: https://github.com/shaheertariq89/briya-UCA_APP
2. **Click**: Settings → Secrets and variables → Actions
3. **Click**: "New repository secret"
4. **Add each secret** one by one using the table above

## 🔒 **Security Best Practices**

### **Database Security**
- ✅ Use strong, unique passwords
- ✅ Don't use default usernames like `postgres`
- ✅ Use different passwords for different environments
- ✅ Regularly rotate database passwords

### **Server Security**
- ✅ Use strong SSH passwords
- ✅ Consider using SSH keys instead of passwords
- ✅ Regularly update server packages
- ✅ Use non-root users when possible

### **Application Security**
- ✅ Generate unique secret keys for each environment
- ✅ Use HTTPS in production
- ✅ Keep secrets in GitHub, not in code
- ✅ Regularly rotate all secrets

## 🎯 **Quick Setup Checklist**

**Required Secrets (12 total):**
- [ ] SERVER_HOST
- [ ] SERVER_USER
- [ ] SERVER_PASSWORD
- [ ] SERVER_PORT
- [ ] UCA_SECRET_KEY
- [ ] UCA_ALLOWED_HOSTS
- [ ] UCA_DOMAIN
- [ ] UCA_DB_NAME
- [ ] UCA_DB_USER
- [ ] UCA_DB_PASSWORD
- [ ] UCA_DB_HOST
- [ ] UCA_DB_PORT

**Optional Secrets (2 total):**
- [ ] UCA_EMAIL_HOST_USER
- [ ] UCA_EMAIL_HOST_PASSWORD

## 🧪 **Testing Your Setup**

After setting up all secrets:

1. **Push a commit** to your main branch
2. **Check GitHub Actions** for deployment progress
3. **Monitor the logs** for any errors
4. **Test your application** at your domain

## 🔧 **Troubleshooting**

### **Common Issues**
- **Database connection failed**: Check UCA_DB_* secrets
- **SSH connection failed**: Check SERVER_* secrets
- **SSL certificate failed**: Check UCA_DOMAIN and DNS settings
- **Permission denied**: Check SERVER_USER and SERVER_PASSWORD

### **Debug Commands**
```bash
# Test database connection
PGPASSWORD=your-db-password psql -h your-db-host -U your-db-user -d your-db-name -c "SELECT version();"

# Test SSH connection
ssh your-user@your-server

# Check service status
sudo systemctl status uca_app
sudo systemctl status postgresql
```

## 📞 **Need Help?**

If you encounter issues:
1. Check the deployment logs in GitHub Actions
2. Verify all secrets are set correctly
3. Test connections manually
4. Check server firewall and DNS settings

Your UCA app will be fully automated once all secrets are configured! 🎉
