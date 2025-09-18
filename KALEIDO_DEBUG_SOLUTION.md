# Kaleido Debug Solution

## Problem Analysis
Based on your server logs, the issue is:
- Kaleido is being imported successfully
- But `pio.write_image()` is failing silently
- The system falls back to HTML format
- PDFs cannot include HTML files, so charts don't appear

## Enhanced Debugging Solution

### 1. **Improved Kaleido Testing**
I've added a comprehensive test function that:
- Tests Kaleido import
- Tests actual PNG creation with a simple chart
- Verifies the file is created and has content
- Provides clear success/failure feedback

### 2. **Enhanced Error Logging**
The updated code now logs:
- Detailed Kaleido test results
- Step-by-step PNG creation process
- File size verification
- Specific error types and messages

### 3. **Management Command for Testing**
Created a Django management command to test Kaleido:
```bash
python manage.py test_kaleido
```

## Testing Steps

### Step 1: Test Kaleido from Command Line
```bash
# On your server
cd /var/www/uca_app
source venv/bin/activate  # if using virtual environment
python manage.py test_kaleido
```

### Step 2: Test Chart Saving
1. Go to course analysis page
2. Click "Save Chart for PDF Report"
3. Check server logs for detailed debugging output

### Step 3: Check Logs
Look for these new debug messages:
```
DEBUG: Testing Kaleido functionality...
✅ Kaleido imported successfully
✅ Kaleido PNG creation successful
DEBUG: Kaleido is working properly, will save as PNG
DEBUG: About to call pio.write_image with kaleido
Chart saved successfully to: /path/to/chart.png
DEBUG: Chart file created successfully with content
```

## Common Kaleido Issues and Solutions

### Issue 1: Kaleido Import Works but PNG Creation Fails
**Symptoms:**
- "Kaleido imported successfully" but "Kaleido PNG creation failed"
- Usually indicates missing system dependencies

**Solution:**
```bash
# Install system dependencies for Kaleido
sudo apt-get update
sudo apt-get install -y libgl1-mesa-glx libglib2.0-0 libxrender1 libgomp1
```

### Issue 2: Permission Issues
**Symptoms:**
- File creation fails due to permissions

**Solution:**
```bash
# Fix permissions
sudo chown -R www-data:www-data /var/www/uca_app/media/
sudo chmod -R 755 /var/www/uca_app/media/
```

### Issue 3: Virtual Environment Issues
**Symptoms:**
- Kaleido installed in wrong environment

**Solution:**
```bash
# Ensure you're in the correct virtual environment
source venv/bin/activate
pip list | grep kaleido
pip install --upgrade kaleido==0.2.1
```

### Issue 4: Server Architecture Mismatch
**Symptoms:**
- Kaleido installed but not compatible with server architecture

**Solution:**
```bash
# Reinstall with correct architecture
pip uninstall kaleido
pip install --no-cache-dir kaleido==0.2.1
```

## Alternative Solution: Force PNG Creation

If Kaleido continues to fail, I can modify the code to use an alternative method:

### Option 1: Use matplotlib as fallback
```python
# Convert Plotly to matplotlib and save as PNG
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
```

### Option 2: Use selenium with headless browser
```python
# Use selenium to render HTML and take screenshot
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
```

## Files Modified

1. **`uca_app/views.py`**
   - Added `test_kaleido_functionality()` function
   - Enhanced error logging in `save_chart_with_toggle_states()`
   - Added comprehensive debugging output

2. **`uca_app/management/commands/test_kaleido.py`**
   - New management command for testing Kaleido

## Next Steps

1. **Deploy the updated code** to your server
2. **Run the test command**: `python manage.py test_kaleido`
3. **Test the chart saving** and check logs
4. **Report the specific error messages** you see

The enhanced debugging will show us exactly where Kaleido is failing, and we can then apply the appropriate fix.
