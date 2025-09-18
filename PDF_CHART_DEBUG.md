# PDF Chart Debug Guide

## Issue
The "Save Chart for PDF Report" button is working (chart is being saved), but the chart is not appearing in the PDF report.

## Debugging Steps

### 1. Check Chart File Creation
After clicking "Save Chart for PDF Report", check the server logs for:

**For PNG files (kaleido available):**
```
DEBUG: Attempting to save chart to: /path/to/media/reports/section_stats_chart_4.png
Chart saved successfully to: /path/to/media/reports/section_stats_chart_4.png
DEBUG: Chart file exists after save: True
DEBUG: Chart file size: [number] bytes
```

**For HTML files (kaleido not available):**
```
DEBUG: Attempting to save chart as HTML to: /path/to/media/reports/section_stats_chart_4.html
Chart saved as HTML (kaleido not available): /path/to/media/reports/section_stats_chart_4.html
DEBUG: HTML file exists after save: True
DEBUG: HTML file size: [number] bytes
```

### 2. Check PDF Generation
When generating a PDF report, check the server logs for:

```
DEBUG: Looking for section stats chart at: /path/to/media/reports/section_stats_chart_4.png
DEBUG: Section stats chart exists: True/False
DEBUG: Looking for section stats chart HTML at: /path/to/media/reports/section_stats_chart_4.html
DEBUG: Section stats chart HTML exists: True/False
DEBUG: Section stats chart added to PDF successfully
```

### 3. Manual File Check
Check if the chart file actually exists on the server:

```bash
# Check if PNG file exists
ls -la /path/to/media/reports/section_stats_chart_4.png

# Check if HTML file exists
ls -la /path/to/media/reports/section_stats_chart_4.html

# Check file permissions
ls -la /path/to/media/reports/
```

### 4. Common Issues and Solutions

#### Issue 1: Chart saved as HTML instead of PNG
**Symptoms:** 
- Server logs show "Chart saved as HTML (kaleido not available)"
- PDF logs show "Section stats chart PNG not found, but HTML exists"

**Solution:**
- Install kaleido package: `pip install kaleido==0.2.1`
- Restart the Django application

#### Issue 2: File not found during PDF generation
**Symptoms:**
- Server logs show "Section stats chart exists: False"
- Chart was saved successfully but PDF can't find it

**Possible Causes:**
- File path mismatch
- File permissions issue
- File was deleted between save and PDF generation
- Different media root settings

**Solution:**
- Check file paths in logs
- Verify file permissions
- Ensure consistent media root settings

#### Issue 3: File exists but PDF generation fails
**Symptoms:**
- Server logs show "Section stats chart exists: True"
- But no "Section stats chart added to PDF successfully" message

**Possible Causes:**
- Image file is corrupted
- PIL/Pillow can't open the image
- PDF generation error

**Solution:**
- Check if the image file can be opened manually
- Verify PIL/Pillow installation
- Check for PDF generation errors

### 5. Testing Commands

#### Test Chart File Creation
```python
# Run this in Django shell
from django.conf import settings
import os

course_id = 4  # Replace with your course ID
reports_dir = os.path.join(settings.MEDIA_ROOT, 'reports')
chart_path = os.path.join(reports_dir, f"section_stats_chart_{course_id}.png")
html_path = os.path.join(reports_dir, f"section_stats_chart_{course_id}.html")

print(f"PNG file exists: {os.path.exists(chart_path)}")
print(f"HTML file exists: {os.path.exists(html_path)}")

if os.path.exists(chart_path):
    print(f"PNG file size: {os.path.getsize(chart_path)} bytes")
if os.path.exists(html_path):
    print(f"HTML file size: {os.path.getsize(html_path)} bytes")
```

#### Test PDF Generation
```python
# Run this in Django shell
from uca_app.models import Course
from uca_app.views import generate_pdf_report

course = Course.objects.get(id=4)  # Replace with your course ID
options = {}  # Add any options you need

try:
    pdf_path = generate_pdf_report(course, options)
    print(f"PDF generated successfully: {pdf_path}")
except Exception as e:
    print(f"PDF generation failed: {e}")
    import traceback
    traceback.print_exc()
```

### 6. Next Steps
1. Click "Save Chart for PDF Report" and check server logs
2. Generate a PDF report and check server logs
3. Compare the file paths and existence checks
4. Report back with the specific log messages you see

## Files Modified for Debugging
- `uca_app/views.py` - Added debugging to chart saving and PDF generation
- `templates/uca_app/course_analysis.html` - Removed temporary alert

## Expected Behavior
1. Click "Save Chart for PDF Report" → Chart file created
2. Generate PDF report → Chart included in PDF
3. Open PDF → Chart visible on Section Statistics page
