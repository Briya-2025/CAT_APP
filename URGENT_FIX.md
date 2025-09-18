# 🚨 URGENT FIX: USE_HTTPS NameError

## The Problem
Your Django application is failing to start with this error:
```
NameError: name 'USE_HTTPS' is not defined
```

This is happening because the `USE_HTTPS` variable is being used before it's defined in the settings file.

## The Solution

I've fixed the issue in the code, but you need to update your server. Here are two ways to fix it:

### Option 1: Quick Fix (Recommended)
Run this command on your server:
```bash
cd /var/www/uca_app
python3 quick_fix.py
```

### Option 2: Manual Fix
1. **Update the settings file** on your server:
   ```bash
   # The USE_HTTPS variable needs to be defined before it's used
   # It should be defined right after the DEBUG line
   ```

2. **Restart the service**:
   ```bash
   sudo systemctl restart uca_app
   ```

## What I Fixed

1. **Moved `USE_HTTPS` definition** to the top of the settings file (line 19)
2. **Removed duplicate definition** that was later in the file
3. **Removed unused import** (`dj_database_url`)
4. **Created a quick fix script** that can be run on the server

## Files Modified

- ✅ `uca_project/settings_production.py` - Fixed variable order
- ✅ `quick_fix.py` - Created automated fix script

## After the Fix

Once you run the fix, your application should:
- ✅ Start without the NameError
- ✅ Work on HTTP (as intended)
- ✅ Be ready for HTTPS upgrade when needed

## Next Steps

1. **Run the quick fix**: `python3 quick_fix.py`
2. **Verify the service is running**: `sudo systemctl status uca_app`
3. **Test your application**: Visit your domain
4. **Optionally enable HTTPS**: `./setup_https.sh your-domain.com your-email@example.com`

The fix is simple but critical - the variable definition order was wrong in the Django settings file.
