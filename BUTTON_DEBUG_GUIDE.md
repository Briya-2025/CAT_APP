# Save Chart Button Debug Guide

## Issue
The "Save Chart for PDF Report" button is not working properly.

## Debugging Steps

### 1. Test Basic Function Call
1. Open the course analysis page in your browser
2. Open browser developer tools (F12)
3. Go to the Console tab
4. Click the "Save Chart for PDF Report" button
5. You should see:
   - An alert saying "saveCurrentChart function called!"
   - Console log: "saveCurrentChart function called"

**If you don't see the alert:**
- The function is not being called
- Check for JavaScript errors in the console
- Verify the button HTML is correct

### 2. Test Toggle States
If the alert appears, check the console for:
- "Toggle states: {quiz: true, assignment: false, ...}"
- This shows the current state of all toggle buttons

**If toggle states are undefined:**
- One or more toggle button IDs are missing
- Check that all toggle buttons exist in the HTML

### 3. Test CSRF Token
Check the console for:
- "CSRF Token: [some token value]"

**If CSRF token is missing:**
- The form doesn't have a CSRF token
- Check that `{% csrf_token %}` is in the template

### 4. Test Network Request
1. Go to the Network tab in developer tools
2. Click the "Save Chart for PDF Report" button
3. Look for a POST request to the same URL
4. Check the request details:
   - Headers should include `Content-Type: application/json`
   - Headers should include `X-CSRFToken`
   - Request body should contain the JSON data

### 5. Test Backend Response
Check the server logs for:
- "DEBUG: POST request received. Content-Type: application/json"
- "DEBUG: JSON data received: {...}"
- "DEBUG: Toggle states: {...}"
- "DEBUG: Save chart result: ..."

## Common Issues and Solutions

### Issue 1: Function Not Called
**Symptoms:** No alert, no console logs
**Solutions:**
- Check for JavaScript syntax errors
- Verify the button onclick attribute
- Check if there are conflicting JavaScript functions

### Issue 2: CSRF Token Missing
**Symptoms:** 403 Forbidden error, CSRF token error
**Solutions:**
- Ensure `{% csrf_token %}` is in the template
- Check that the token element exists in the DOM

### Issue 3: Toggle States Undefined
**Symptoms:** Error getting toggle states
**Solutions:**
- Verify all toggle button IDs exist
- Check that the buttons are rendered before the script runs

### Issue 4: Backend Not Receiving Request
**Symptoms:** No server logs, network request fails
**Solutions:**
- Check URL routing
- Verify the view handles POST requests
- Check for middleware issues

### Issue 5: Kaleido Error
**Symptoms:** Backend error about kaleido package
**Solutions:**
- Run the kaleido installation script
- Check that kaleido is properly installed

## Testing Commands

### Test JavaScript Function
```javascript
// Run this in browser console to test the function
saveCurrentChart();
```

### Test CSRF Token
```javascript
// Run this in browser console to check CSRF token
console.log(document.querySelector('[name=csrfmiddlewaretoken]').value);
```

### Test Toggle States
```javascript
// Run this in browser console to check toggle states
const toggleStates = {
    quiz: document.getElementById('toggleQuiz').checked,
    assignment: document.getElementById('toggleAssignment').checked,
    hw: document.getElementById('toggleHW').checked,
    midterm: document.getElementById('toggleMidterm').checked,
    final: document.getElementById('toggleFinal').checked,
    lab: document.getElementById('toggleLab').checked,
    weighted: document.getElementById('toggleWeighted').checked
};
console.log(toggleStates);
```

## Next Steps
1. Test the button with the debugging steps above
2. Check the browser console for any errors
3. Check the server logs for backend errors
4. Report back with the specific error messages or behavior you observe

## Files Modified for Debugging
- `templates/uca_app/course_analysis.html` - Added debugging logs and error handling
- `uca_app/views.py` - Added debugging prints to the backend

