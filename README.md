# Unified Course Assessment - Django Web Application

A comprehensive web-based course assessment and analysis system for the Department of Physics, converted from the original desktop application.

## Features

### 🎯 Core Features
- **Course Management**: Create, edit, and manage multiple courses
- **Section Management**: Handle multiple sections per course with different instructors
- **Assessment Tracking**: Track quizzes, assignments, homework, midterms, finals, and labs
- **Weighted Calculations**: Customizable weight distribution for different assessment types
- **Statistical Analysis**: Comprehensive performance analysis with interactive charts
- **Grade Distribution**: Manage and visualize grade distributions across sections
- **PDF Report Generation**: Generate professional PDF reports with charts and tables

### 🌐 Web Advantages
- **Cross-Platform**: Works on Windows, Mac, Linux, and mobile devices
- **No Installation**: Access via any web browser
- **Real-time Updates**: Instant calculations and visualizations
- **Data Persistence**: Secure database storage with backup capabilities
- **Modern UI**: Responsive, modern interface with Bootstrap 5
- **Collaboration Ready**: Multiple users can access simultaneously

### 📊 Visualization & Analysis
- **Interactive Charts**: Plotly.js powered interactive visualizations
- **Section Comparison**: Compare performance across different sections
- **Weighted Score Analysis**: Visual representation of weighted performance
- **Grade Distribution Charts**: Bar charts and pie charts for grade analysis
- **Real-time Statistics**: Live calculation of course statistics

### 📄 Reporting & Export
- **PDF Reports**: Professional PDF generation with ReportLab
- **JSON Export/Import**: Full project backup and sharing capabilities
- **Data Snapshots**: Historical data preservation
- **Customizable Reports**: Include/exclude charts, tables, and sections

## Technology Stack

- **Backend**: Django 4.2.7
- **Frontend**: Bootstrap 5, jQuery, Plotly.js
- **Database**: SQLite (can be upgraded to PostgreSQL/MySQL)
- **Charts**: Plotly.js for interactive visualizations
- **PDF Generation**: ReportLab
- **Forms**: Django Crispy Forms with Bootstrap 5
- **Styling**: Custom CSS with modern design

## Installation & Setup

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)

### Step 1: Clone/Download the Project
```bash
# Navigate to your desired directory
cd /path/to/your/project

# The project files should be in the django_uca directory
```

### Step 2: Create Virtual Environment
```bash
# Create a virtual environment
python -m venv uca_env

# Activate the virtual environment
# On Windows:
uca_env\Scripts\activate

# On macOS/Linux:
source uca_env/bin/activate
```

### Step 3: Install Dependencies
```bash
# Install all required packages
pip install -r requirements.txt
```

### Step 4: Database Setup
```bash
# Create database tables
python manage.py makemigrations
python manage.py migrate

# Create a superuser (admin account)
python manage.py createsuperuser
```

### Step 5: Run the Development Server
```bash
# Start the development server
python manage.py runserver

# The application will be available at:
# http://127.0.0.1:8000/
```

### Step 6: Access the Application
- **Main Application**: http://127.0.0.1:8000/
- **Admin Interface**: http://127.0.0.1:8000/admin/

## Usage Guide

### 1. Creating a New Course
1. Click "Create New Course" from the home page
2. Fill in course information (name, code, term, coordinator)
3. Configure assessment weights (must sum to 100%)
4. Click "Next: Add Sections"

### 2. Managing Sections
1. Add section information (instructor, student count)
2. Configure the number of sections needed
3. Click "Next: Add Assessments"

### 3. Adding Assessments
1. For each section, add assessment data:
   - Quiz scores (max marks and average marks)
   - Assignment scores
   - Homework scores
   - Midterm scores
   - Final exam scores
   - Lab scores
2. Click "Calculate Course Statistics"

### 4. Viewing Analysis
1. Review section performance comparison charts
2. Analyze weighted scores
3. View detailed statistics table
4. Click "Continue to Grade Distribution"

### 5. Grade Distribution
1. Enter grade counts for each section
2. View grade distribution charts
3. Click "Generate Report"

### 6. Generating Reports
1. Choose report options (include charts, tables, etc.)
2. Enter report title
3. Generate and download PDF report

## Project Structure

```
django_uca/
├── manage.py                 # Django management script
├── requirements.txt          # Python dependencies
├── README.md                # This file
├── uca_project/             # Django project settings
│   ├── __init__.py
│   ├── settings.py          # Django settings
│   ├── urls.py              # Main URL configuration
│   ├── wsgi.py              # WSGI configuration
│   └── asgi.py              # ASGI configuration
├── uca_app/                 # Main application
│   ├── __init__.py
│   ├── admin.py             # Django admin configuration
│   ├── apps.py              # App configuration
│   ├── models.py            # Database models
│   ├── forms.py             # Django forms
│   ├── views.py             # View functions
│   └── urls.py              # App URL patterns
├── templates/               # HTML templates
│   ├── base.html            # Base template
│   └── uca_app/             # App-specific templates
│       ├── index.html       # Home page
│       ├── course_create.html
│       ├── course_analysis.html
│       └── ...
├── static/                  # Static files (CSS, JS, images)
├── media/                   # User-uploaded files
└── logs/                    # Application logs
```

## Database Models

### Course
- Basic course information (name, code, term, coordinator)
- One-to-one relationship with CourseConfiguration

### CourseConfiguration
- Number of sections, quizzes, assignments
- Weight distribution for assessment types

### Section
- Section information (number, instructor, student count)
- Foreign key to Course

### Assessment
- Assessment data (type, number, max marks, average marks)
- Foreign key to Section

### GradeDistribution
- Grade counts for each section
- Foreign keys to Course and Section

### CourseReport
- Generated PDF reports
- Data snapshots for historical reference

## API Endpoints

- `GET /` - Home page
- `GET /courses/` - Course list
- `GET /course/create/` - Create new course
- `GET /course/<id>/` - Course details
- `GET /course/<id>/analysis/` - Course analysis
- `GET /course/<id>/grades/` - Grade distribution
- `GET /course/<id>/report/` - Generate report
- `POST /api/calculate-stats/` - Calculate statistics (AJAX)

## Customization

### Adding New Assessment Types
1. Update `Assessment.ASSESSMENT_TYPES` in `models.py`
2. Add corresponding weight fields in `CourseConfiguration`
3. Update forms and views accordingly

### Modifying Charts
1. Edit chart creation functions in `views.py`
2. Update Plotly.js configurations
3. Modify chart containers in templates

### Styling Changes
1. Edit CSS in `templates/base.html`
2. Modify Bootstrap classes in templates
3. Update color variables in CSS

## Deployment

### Development
```bash
python manage.py runserver
```

### Production (Recommended)
1. Set `DEBUG = False` in settings.py
2. Configure a production database (PostgreSQL/MySQL)
3. Set up static file serving
4. Use a production WSGI server (Gunicorn)
5. Configure a reverse proxy (Nginx)

### Docker Deployment
```bash
# Build and run with Docker
docker build -t uca-app .
docker run -p 8000:8000 uca-app
```

## Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Use a different port
   python manage.py runserver 8001
   ```

2. **Database Migration Errors**
   ```bash
   # Reset migrations
   python manage.py makemigrations --empty uca_app
   python manage.py migrate
   ```

3. **Static Files Not Loading**
   ```bash
   # Collect static files
   python manage.py collectstatic
   ```

4. **Permission Errors (Windows)**
   ```bash
   # Run PowerShell as Administrator
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

## Support

For technical support or questions:
- Check the Django documentation: https://docs.djangoproject.com/
- Review the application logs in the `logs/` directory
- Contact the development team

## License

This project is developed for the Department of Physics.
Developed by Briya Tariq (PhD student 100062544)
Under supervision of Dr. Aamir Raja

## Version History

- **v1.0** - Initial web conversion from desktop application
- Features: Course management, assessment tracking, analysis, reporting
- Technology: Django 4.2.7, Bootstrap 5, Plotly.js, ReportLab
