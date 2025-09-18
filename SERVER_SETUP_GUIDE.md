# 🖥️ Server Setup Guide for UCA App

## 🎯 **Server Options**

### **1. Cloud Providers (Recommended)**

#### **DigitalOcean**
- **Cost**: $5-12/month
- **Specs**: 1GB RAM, 1 CPU, 25GB SSD
- **Setup**: Ubuntu 22.04 LTS
- **Pros**: Simple, reliable, good documentation
- **Link**: [digitalocean.com](https://digitalocean.com)

#### **Vultr**
- **Cost**: $3.50-6/month
- **Specs**: 1GB RAM, 1 CPU, 25GB SSD
- **Setup**: Ubuntu 22.04 LTS
- **Pros**: Fast, affordable, multiple locations
- **Link**: [vultr.com](https://vultr.com)

#### **Linode**
- **Cost**: $5-10/month
- **Specs**: 1GB RAM, 1 CPU, 25GB SSD
- **Setup**: Ubuntu 22.04 LTS
- **Pros**: Reliable, good performance
- **Link**: [linode.com](https://linode.com)

#### **AWS EC2**
- **Cost**: $8-15/month (t2.micro)
- **Specs**: 1GB RAM, 1 CPU
- **Setup**: Ubuntu 22.04 LTS
- **Pros**: Scalable, enterprise-grade
- **Link**: [aws.amazon.com](https://aws.amazon.com)

### **2. VPS Providers**

#### **Hetzner**
- **Cost**: €3-6/month
- **Specs**: 2GB RAM, 1 CPU, 20GB SSD
- **Setup**: Ubuntu 22.04 LTS
- **Pros**: Excellent price/performance
- **Link**: [hetzner.com](https://hetzner.com)

#### **Contabo**
- **Cost**: €4-8/month
- **Specs**: 4GB RAM, 2 CPU, 50GB SSD
- **Setup**: Ubuntu 22.04 LTS
- **Pros**: High specs for low price
- **Link**: [contabo.com](https://contabo.com)

## 📋 **Server Requirements**

### **Minimum Requirements**
- **OS**: Ubuntu 20.04+ or Debian 10+
- **RAM**: 1GB (2GB recommended)
- **CPU**: 1 core (2 cores recommended)
- **Storage**: 20GB SSD
- **Network**: 1TB bandwidth/month
- **Root Access**: Required

### **Recommended Specifications**
- **OS**: Ubuntu 22.04 LTS
- **RAM**: 2GB
- **CPU**: 2 cores
- **Storage**: 40GB SSD
- **Network**: Unlimited bandwidth
- **Root Access**: Yes

## 🚀 **Step-by-Step Server Setup**

### **Step 1: Create Server**

1. **Choose a provider** from the list above
2. **Create account** and add payment method
3. **Create new server/VPS**:
   - **OS**: Ubuntu 22.04 LTS
   - **Size**: 1GB RAM minimum
   - **Location**: Choose closest to your users
   - **SSH Key**: Add your SSH key (recommended)

### **Step 2: Initial Server Configuration**

```bash
# Connect to your server
ssh root@your-server-ip

# Update system
apt update && apt upgrade -y

# Install essential packages
apt install -y curl wget git vim htop

# Create non-root user (recommended)
adduser ubuntu
usermod -aG sudo ubuntu

# Switch to new user
su - ubuntu
```

### **Step 3: SSH Key Setup (Recommended)**

```bash
# On your local machine, generate SSH key if you don't have one
ssh-keygen -t rsa -b 4096 -C "your-email@example.com"

# Copy public key to server
ssh-copy-id ubuntu@your-server-ip

# Test SSH connection
ssh ubuntu@your-server-ip
```

### **Step 4: Firewall Configuration**

```bash
# Enable UFW firewall
sudo ufw enable

# Allow SSH
sudo ufw allow ssh

# Allow HTTP and HTTPS
sudo ufw allow 80
sudo ufw allow 443

# Check status
sudo ufw status
```

### **Step 5: Domain Setup (Optional)**

If you have a domain:

1. **Point your domain** to server IP:
   - **A Record**: `@` → `your-server-ip`
   - **A Record**: `www` → `your-server-ip`

2. **Wait for DNS propagation** (up to 24 hours)

## 🔧 **Server Preparation Script**

Create this script to prepare your server:

```bash
#!/bin/bash
# Server preparation script for UCA App

echo "🚀 Preparing server for UCA App deployment..."

# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3 python3-pip python3-venv python3-dev nginx postgresql postgresql-contrib git curl certbot python3-certbot-nginx build-essential libpq-dev

# Install Node.js (for Kaleido dependencies)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install nodejs -y

# Create project directory
sudo mkdir -p /var/www/uca_app
sudo chown $USER:$USER /var/www/uca_app

# Set up PostgreSQL
sudo -u postgres psql -c "CREATE DATABASE uca_app;"
sudo -u postgres psql -c "CREATE USER uca_user WITH PASSWORD 'UCA_2024_Secure!';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE uca_app TO uca_user;"
sudo -u postgres psql -c "ALTER USER uca_user CREATEDB;"

# Configure Nginx
sudo rm -f /etc/nginx/sites-enabled/default

# Create logs directory
sudo mkdir -p /var/log/gunicorn
sudo chown www-data:www-data /var/log/gunicorn

echo "✅ Server preparation complete!"
echo "📝 Next steps:"
echo "1. Set up GitHub secrets"
echo "2. Deploy your application"
echo "3. Configure your domain"
```

## 🌐 **Domain Configuration**

### **If You Have a Domain:**

1. **Buy a domain** from providers like:
   - Namecheap
   - GoDaddy
   - Cloudflare
   - Google Domains

2. **Configure DNS**:
   ```
   Type: A
   Name: @
   Value: your-server-ip
   TTL: 300
   
   Type: A
   Name: www
   Value: your-server-ip
   TTL: 300
   ```

3. **Wait for propagation** (check with `nslookup your-domain.com`)

### **If You Don't Have a Domain:**

- Your app will be accessible via IP address
- Example: `http://192.168.1.100`
- SSL certificates won't work without a domain

## 🔐 **Security Best Practices**

### **1. SSH Security**
```bash
# Disable root login
sudo nano /etc/ssh/sshd_config
# Set: PermitRootLogin no

# Change SSH port (optional)
# Set: Port 2222

# Restart SSH
sudo systemctl restart ssh
```

### **2. Firewall Rules**
```bash
# Allow only necessary ports
sudo ufw allow 22    # SSH
sudo ufw allow 80    # HTTP
sudo ufw allow 443   # HTTPS
sudo ufw deny 3306   # MySQL (if not needed)
sudo ufw deny 5432   # PostgreSQL (if not needed)
```

### **3. Regular Updates**
```bash
# Set up automatic security updates
sudo apt install unattended-upgrades
sudo dpkg-reconfigure unattended-upgrades
```

## 📊 **Server Monitoring**

### **Basic Monitoring Commands**
```bash
# Check system resources
htop
df -h
free -h

# Check running services
sudo systemctl status nginx
sudo systemctl status postgresql

# Check logs
sudo journalctl -u uca_app -f
sudo tail -f /var/log/nginx/error.log
```

### **Monitoring Tools**
- **htop**: Process monitoring
- **iotop**: Disk I/O monitoring
- **nethogs**: Network monitoring
- **glances**: System overview

## 💰 **Cost Comparison**

| Provider | Monthly Cost | RAM | CPU | Storage | Bandwidth |
|----------|-------------|-----|-----|---------|-----------|
| DigitalOcean | $5 | 1GB | 1 | 25GB | 1TB |
| Vultr | $3.50 | 1GB | 1 | 25GB | 1TB |
| Hetzner | €3 | 2GB | 1 | 20GB | 20TB |
| Contabo | €4 | 4GB | 2 | 50GB | Unlimited |
| AWS EC2 | $8 | 1GB | 1 | 8GB | 1GB |

## 🎯 **Quick Setup Checklist**

Before deploying your UCA app:

- [ ] **Server created** with Ubuntu 22.04 LTS
- [ ] **SSH access** configured
- [ ] **Firewall** configured (ports 22, 80, 443)
- [ ] **Domain** pointing to server IP (optional)
- [ ] **GitHub secrets** configured
- [ ] **Server preparation** script run

## 🚨 **Troubleshooting**

### **Common Issues:**

1. **Can't SSH to server**:
   - Check firewall settings
   - Verify SSH key is added
   - Check server provider's security groups

2. **Domain not resolving**:
   - Wait for DNS propagation
   - Check DNS settings
   - Use `nslookup` to test

3. **Server out of resources**:
   - Upgrade server plan
   - Optimize application
   - Add swap space

### **Emergency Commands:**
```bash
# Restart services
sudo systemctl restart nginx
sudo systemctl restart postgresql

# Check disk space
df -h

# Check memory usage
free -h

# Kill processes if needed
sudo pkill -f gunicorn
```

## 📞 **Support**

If you need help:

1. **Check server provider documentation**
2. **Use their support channels**
3. **Check application logs**
4. **Verify all configurations**

Your server is now ready for UCA app deployment! 🚀
