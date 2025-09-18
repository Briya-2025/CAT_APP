#!/bin/bash

echo "🚀 Deploying Kaleido Fix to Server"
echo "=================================="

# Check if we're in the right directory
if [ ! -f "uca_app/views.py" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

# Commit and push changes
echo "📝 Committing changes..."
git add .
git commit -m "Fix Kaleido issue with matplotlib fallback"

echo "📤 Pushing to repository..."
git push origin main

echo "✅ Code pushed to repository"
echo ""
echo "🔧 Next steps on your server:"
echo "1. SSH into your server: ssh root@148.230.99.91"
echo "2. Navigate to app directory: cd /var/www/uca_app"
echo "3. Pull latest changes: git pull origin main"
echo "4. Run the quick fix: python3 quick_fix_kaleido.py"
echo "5. Restart the service: systemctl restart uca_app"
echo "6. Test the chart save functionality"
echo ""
echo "📋 Or run these commands on your server:"
echo "cd /var/www/uca_app"
echo "git pull origin main"
echo "python3 quick_fix_kaleido.py"
echo "systemctl restart uca_app"