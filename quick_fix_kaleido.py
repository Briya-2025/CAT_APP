#!/usr/bin/env python3
"""
Quick fix script to install Kaleido and test it on the server
Run this script on your server to fix the Kaleido issue
"""

import subprocess
import sys
import os

def run_command(command):
    """Run a command and return the result"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def main():
    print("🔧 Quick Kaleido Fix Script")
    print("=" * 50)
    
    # Check if we're in a virtual environment
    venv_path = os.environ.get('VIRTUAL_ENV')
    if venv_path:
        print(f"✅ Virtual environment detected: {venv_path}")
    else:
        print("⚠️  No virtual environment detected")
    
    # Install system dependencies
    print("\n📦 Installing system dependencies...")
    deps_command = "sudo apt-get update && sudo apt-get install -y libgl1-mesa-glx libglib2.0-0 libxrender1 libgomp1"
    success, stdout, stderr = run_command(deps_command)
    if success:
        print("✅ System dependencies installed successfully")
    else:
        print(f"❌ Failed to install system dependencies: {stderr}")
    
    # Uninstall and reinstall kaleido
    print("\n🔄 Reinstalling Kaleido...")
    
    # Uninstall
    uninstall_command = "pip uninstall -y kaleido"
    run_command(uninstall_command)
    
    # Install
    install_command = "pip install --no-cache-dir kaleido==0.2.1"
    success, stdout, stderr = run_command(install_command)
    if success:
        print("✅ Kaleido installed successfully")
    else:
        print(f"❌ Failed to install Kaleido: {stderr}")
        return False
    
    # Test kaleido
    print("\n🧪 Testing Kaleido...")
    test_code = """
import kaleido
import plotly.graph_objects as go
import plotly.io as pio
import tempfile
import os

try:
    # Create a simple test figure
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[1, 2, 3], y=[1, 2, 3], name='Test'))
    fig.update_layout(title="Kaleido Test")
    
    # Try to save as PNG
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
        pio.write_image(fig, tmp_file.name, width=400, height=300, format='png')
        
        if os.path.exists(tmp_file.name) and os.path.getsize(tmp_file.name) > 0:
            print("✅ Kaleido test successful!")
            os.unlink(tmp_file.name)
            exit(0)
        else:
            print("❌ Kaleido test failed - file not created")
            exit(1)
            
except Exception as e:
    print(f"❌ Kaleido test failed: {e}")
    exit(1)
"""
    
    # Write test code to temporary file
    with open('/tmp/test_kaleido.py', 'w') as f:
        f.write(test_code)
    
    # Run test
    success, stdout, stderr = run_command("python3 /tmp/test_kaleido.py")
    if success:
        print("✅ Kaleido is working properly!")
        print("🎉 Fix completed successfully!")
        return True
    else:
        print(f"❌ Kaleido test failed: {stderr}")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🚀 Next steps:")
        print("1. Restart your Django application: systemctl restart uca_app")
        print("2. Test the chart save functionality")
        print("3. Generate a PDF report")
    else:
        print("\n❌ Fix failed. Please check the error messages above.")
        sys.exit(1)
