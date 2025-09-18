#!/usr/bin/env python3
"""
Quick fix script to resolve the USE_HTTPS NameError in settings_production.py
"""

import os
import sys

def fix_settings_file():
    """Fix the USE_HTTPS variable order in settings_production.py"""
    
    settings_file = '/var/www/uca_app/uca_project/settings_production.py'
    
    if not os.path.exists(settings_file):
        print(f"❌ Settings file not found: {settings_file}")
        return False
    
    # Read the current file
    with open(settings_file, 'r') as f:
        content = f.read()
    
    # Check if the fix is already applied
    if 'USE_HTTPS = os.environ.get(\'USE_HTTPS\', \'False\').lower() == \'true\'' in content:
        # Count occurrences to see if it's duplicated
        count = content.count('USE_HTTPS = os.environ.get(\'USE_HTTPS\', \'False\').lower() == \'true\'')
        if count == 1:
            print("✅ USE_HTTPS variable is already properly defined")
            return True
        elif count > 1:
            print("⚠️ Multiple USE_HTTPS definitions found, cleaning up...")
    
    # Apply the fix
    lines = content.split('\n')
    fixed_lines = []
    use_https_defined = False
    
    for i, line in enumerate(lines):
        # Skip duplicate USE_HTTPS definitions
        if 'USE_HTTPS = os.environ.get(\'USE_HTTPS\', \'False\').lower() == \'true\'' in line:
            if not use_https_defined:
                fixed_lines.append(line)
                use_https_defined = True
            continue
        
        # Add the USE_HTTPS definition after DEBUG if not already defined
        if 'DEBUG = os.environ.get(\'DEBUG\', \'False\').lower() == \'true\'' in line and not use_https_defined:
            fixed_lines.append(line)
            fixed_lines.append('')
            fixed_lines.append('# SSL/HTTPS Configuration - Set based on environment')
            fixed_lines.append('USE_HTTPS = os.environ.get(\'USE_HTTPS\', \'False\').lower() == \'true\'')
            use_https_defined = True
        else:
            fixed_lines.append(line)
    
    # Write the fixed content back
    with open(settings_file, 'w') as f:
        f.write('\n'.join(fixed_lines))
    
    print("✅ Fixed USE_HTTPS variable definition order")
    return True

def test_django_settings():
    """Test if Django settings can be loaded"""
    try:
        # Set environment variables for testing
        os.environ.setdefault('USE_HTTPS', 'False')
        os.environ.setdefault('SECRET_KEY', 'test-key-for-validation')
        os.environ.setdefault('DEBUG', 'False')
        os.environ.setdefault('ALLOWED_HOSTS', 'localhost,127.0.0.1')
        
        # Change to the Django project directory
        os.chdir('/var/www/uca_app')
        
        # Import Django settings
        import django
        from django.conf import settings
        django.setup()
        
        print("✅ Django settings loaded successfully")
        print(f"   USE_HTTPS: {getattr(settings, 'USE_HTTPS', 'Not defined')}")
        print(f"   SECURE_SSL_REDIRECT: {getattr(settings, 'SECURE_SSL_REDIRECT', 'Not defined')}")
        print(f"   SESSION_COOKIE_SECURE: {getattr(settings, 'SESSION_COOKIE_SECURE', 'Not defined')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Django settings test failed: {e}")
        return False

def restart_services():
    """Restart the Django application service"""
    import subprocess
    
    try:
        print("🔄 Restarting uca_app service...")
        result = subprocess.run(['sudo', 'systemctl', 'restart', 'uca_app'], 
                              capture_output=True, text=True, check=True)
        print("✅ uca_app service restarted successfully")
        
        # Check service status
        status_result = subprocess.run(['sudo', 'systemctl', 'status', 'uca_app', '--no-pager'], 
                                     capture_output=True, text=True)
        if 'Active: active (running)' in status_result.stdout:
            print("✅ Service is running")
        else:
            print("⚠️ Service status check failed")
            print(status_result.stdout)
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to restart service: {e}")
        print(f"   Error output: {e.stderr}")
        return False

if __name__ == '__main__':
    print("🔧 Quick Fix for USE_HTTPS NameError")
    print("=" * 50)
    
    # Step 1: Fix the settings file
    if not fix_settings_file():
        print("❌ Failed to fix settings file")
        sys.exit(1)
    
    # Step 2: Test Django settings
    if not test_django_settings():
        print("❌ Django settings test failed")
        sys.exit(1)
    
    # Step 3: Restart services
    if not restart_services():
        print("❌ Failed to restart services")
        sys.exit(1)
    
    print("\n🎉 Quick fix completed successfully!")
    print("Your Django application should now be running without the USE_HTTPS error.")
