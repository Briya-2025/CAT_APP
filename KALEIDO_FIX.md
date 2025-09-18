# Kaleido Package Fix for Plotly Image Export

## Problem
The application was throwing a `ValueError` when trying to export images using Plotly's Kaleido engine:

```
ValueError at /course/4/analysis/
Image export using the "kaleido" engine requires the Kaleido package,
which can be installed using pip:
    $ pip install --upgrade kaleido
```

## Root Cause
The `kaleido` package was missing from the production environment, but the application was trying to use `plotly.io.write_image()` which requires kaleido for PNG/JPEG export.

## Solution Applied

### 1. Added Kaleido to Requirements Files
- Added `kaleido==0.2.1` to `requirements.txt`
- Added `kaleido>=0.2.1` to `requirements_server.txt`
- `requirements_render.txt` already had kaleido included

### 2. Improved Error Handling
Updated two functions in `uca_app/views.py`:

#### `save_chart_with_toggle_states()`
- Added kaleido availability check before attempting image export
- Graceful fallback to HTML format when kaleido is not available
- Better error messages and logging

#### `save_section_statistics_images()`
- Added kaleido availability check before attempting image export
- Graceful fallback to HTML format when kaleido is not available
- Better error messages and logging

### 3. Installation Script
Created `install_kaleido_fix.sh` script for easy deployment:
```bash
./install_kaleido_fix.sh
```

## Deployment Instructions

### Option 1: Using the Installation Script
```bash
# Make script executable (if not already)
chmod +x install_kaleido_fix.sh

# Run the installation script
./install_kaleido_fix.sh
```

### Option 2: Manual Installation
```bash
# Install kaleido package
pip install --upgrade kaleido==0.2.1

# Verify installation
python3 -c "import kaleido; print('Kaleido successfully installed')"
```

### Option 3: Using Requirements File
```bash
# Install from updated requirements
pip install -r requirements.txt
# or
pip install -r requirements_server.txt
```

## Verification
After installation, the application should:
1. Successfully export charts as PNG images when kaleido is available
2. Fall back to HTML format when kaleido is not available (with appropriate logging)
3. No longer throw the ValueError exception

## Files Modified
- `requirements.txt` - Added kaleido==0.2.1
- `requirements_server.txt` - Added kaleido>=0.2.1
- `uca_app/views.py` - Improved error handling in two functions
- `install_kaleido_fix.sh` - New installation script
- `KALEIDO_FIX.md` - This documentation

## Testing
To test the fix:
1. Navigate to a course analysis page
2. Try to save a chart (should work without errors)
3. Check the logs for successful kaleido import messages
4. Verify that chart files are created in the media/reports directory

## Fallback Behavior
If kaleido is still not available after installation:
- Charts will be saved as HTML files instead of PNG
- The application will continue to function normally
- Appropriate warning messages will be logged
- No exceptions will be thrown
