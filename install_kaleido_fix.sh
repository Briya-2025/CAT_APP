#!/bin/bash

# Install Kaleido Fix Script
# This script installs the kaleido package to fix the Plotly image export error

echo "=== Installing Kaleido Package Fix ==="

# Check if we're in a virtual environment
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "Virtual environment detected: $VIRTUAL_ENV"
    PIP_CMD="pip"
else
    echo "No virtual environment detected, using system pip"
    PIP_CMD="pip3"
fi

# Install kaleido package
echo "Installing kaleido package..."
python3 -m pip install --upgrade kaleido==0.2.1

# Verify installation
echo "Verifying kaleido installation..."
python3 -c "import kaleido; print('Kaleido successfully installed and imported')" 2>/dev/null

if [ $? -eq 0 ]; then
    echo "✅ Kaleido installation successful!"
    echo "The Plotly image export error should now be resolved."
else
    echo "❌ Kaleido installation failed or verification failed."
    echo "Please check the error messages above."
    exit 1
fi

# Also install/upgrade plotly to ensure compatibility
echo "Ensuring plotly compatibility..."
python3 -m pip install --upgrade plotly==5.17.0

echo "=== Installation Complete ==="
echo "You can now restart your Django application to use the fixed functionality."
