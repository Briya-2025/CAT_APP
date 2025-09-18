from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.db.models import Sum, Avg
from django.contrib.auth.models import User
from django.forms import inlineformset_factory
import json
import tempfile
import plotly.graph_objects as go
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for web environment
import matplotlib.pyplot as plt
import numpy as np
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from .models import Course, CourseConfiguration, Section, Assessment, GradeDistribution, CourseReport, ProjectFile, CourseAnalysisData
from .forms import (CourseForm, CourseConfigurationForm, SectionForm, AssessmentForm, 
                   GradeDistributionForm, ProjectImportForm, ReportGenerationForm, SectionFormSet,
                   SimpleUserRegistrationForm, SimpleLoginForm)


def index(request):
    """Home page view"""
    # Regular users see only their own courses
    if request.user.is_authenticated:
        user_courses = Course.objects.filter(user=request.user)
        courses = user_courses[:5]
        total_courses = user_courses.count()
        # Calculate sections and students for user's courses only
        total_sections = Section.objects.filter(course__user=request.user).count()
        total_students = Section.objects.filter(course__user=request.user).aggregate(total=Sum('total_students'))['total'] or 0
    else:
        courses = []
        total_courses = 0
        total_sections = 0
        total_students = 0
    
    return render(request, 'uca_app/index.html', {
        'courses': courses,
        'total_courses': total_courses,
        'total_sections': total_sections,
        'total_students': total_students,
    })


def course_create(request):
    """Create new course - Step 1 (also handles editing mode)"""
    # Require user to be logged in
    if not request.user.is_authenticated:
        messages.error(request, 'You must be logged in to create courses.')
        return redirect('uca_app:simple_login')
    
    # Check if we're in editing mode
    editing_course_id = request.session.get('editing_course_id')
    editing_course = None
    is_editing = False
    
    if editing_course_id:
        try:
            editing_course = Course.objects.get(id=editing_course_id)
            # Check permissions
            if request.user.is_authenticated and not request.user.is_staff and editing_course.user and editing_course.user != request.user:
                messages.error(request, 'You do not have permission to edit this course.')
                del request.session['editing_course_id']
                return redirect('uca_app:course_list')
            is_editing = True
        except Course.DoesNotExist:
            del request.session['editing_course_id']
    
    if request.method == 'POST':
        if is_editing:
            course_form = CourseForm(request.POST, instance=editing_course)
            config_form = CourseConfigurationForm(request.POST, instance=editing_course.configuration)
        else:
            course_form = CourseForm(request.POST)
            config_form = CourseConfigurationForm(request.POST)
        
        action = request.POST.get('action', 'next')
        
        if course_form.is_valid() and config_form.is_valid():
            course = course_form.save(commit=False)
            
            if not is_editing:
                # Only assign user for new courses
                course.user = request.user
            
            course.save()
            
            config = config_form.save(commit=False)
            config.course = course
            config.save()
            
            # Clear editing session
            if is_editing:
                del request.session['editing_course_id']
            
            if action == 'back':
                if is_editing:
                    messages.success(request, f'Course "{course.name}" updated successfully!')
                    return redirect('uca_app:course_detail', course_id=course.id)
                else:
                    messages.success(request, f'Course "{course.name}" saved successfully!')
                    return redirect('uca_app:index')
            elif action == 'save':
                if is_editing:
                    messages.success(request, f'Course "{course.name}" saved successfully!')
                    return redirect('uca_app:course_edit', course_id=course.id)
                else:
                    messages.success(request, f'Course "{course.name}" saved successfully!')
                    return redirect('uca_app:course_edit', course_id=course.id)
            else:  # action == 'next'
                if is_editing:
                    messages.success(request, f'Course "{course.name}" updated successfully!')
                else:
                    messages.success(request, f'Course "{course.name}" created successfully!')
                return redirect('uca_app:course_sections', course_id=course.id)
    else:
        if is_editing:
            course_form = CourseForm(instance=editing_course)
            config_form = CourseConfigurationForm(instance=editing_course.configuration)
        else:
            course_form = CourseForm()
            config_form = CourseConfigurationForm()
    
    return render(request, 'uca_app/course_create.html', {
        'course_form': course_form,
        'config_form': config_form,
        'is_editing': is_editing,
        'editing_course': editing_course,
    })


def course_sections(request, course_id):
    """Manage course sections - Step 2"""
    course = get_object_or_404(Course, id=course_id)
    
    # Check access permissions
    # Allow access if user is admin OR if course belongs to user OR if course has no user (legacy courses)
    if request.user.is_authenticated and not request.user.is_staff and course.user and course.user != request.user:
        messages.error(request, 'You do not have permission to manage this course.')
        return redirect('uca_app:course_list')
    
    # Get course configuration to determine number of sections
    try:
        config = course.configuration
        num_sections = config.num_sections
    except:
        num_sections = 3  # Default fallback
    
    # Create dynamic formset based on number of sections
    # Show exactly the number of sections specified in configuration
    existing_sections = course.sections.count()
    
    # If we have more sections than needed, delete the extra ones
    if existing_sections > num_sections:
        sections_to_delete = course.sections.all()[num_sections:]
        for section in sections_to_delete:
            section.delete()
        existing_sections = num_sections
    
    # If we have fewer sections than needed, create the missing ones
    if existing_sections < num_sections:
        for i in range(existing_sections + 1, num_sections + 1):
            Section.objects.create(
                course=course,
                section_number=i,
                instructor='',
                total_students=0
            )
        existing_sections = num_sections
    
    # Show exactly the number of sections specified in configuration (no extra rows)
    # If we have existing sections, don't add extra forms
    extra_forms = 0
    
    # Create formset that only works with existing sections (no new sections)
    DynamicSectionFormSet = inlineformset_factory(
        Course, Section,
        form=SectionForm,
        extra=0,  # No extra forms - only edit existing sections
        can_delete=True,
        min_num=0,
        validate_min=False,
        max_num=1000  # Allow editing all existing sections
    )
    
    if request.method == 'POST':
        print(f"DEBUG: POST data: {request.POST}")
        formset = DynamicSectionFormSet(request.POST, instance=course)
        action = request.POST.get('action', 'next')
        print(f"DEBUG: Formset has {len(formset)} forms")
        
        if formset.is_valid():
            print("DEBUG: Formset is valid")
            formset.save()
            
            if action == 'back':
                messages.success(request, 'Sections saved successfully!')
                return redirect('uca_app:course_edit', course_id=course.id)
            elif action == 'save':
                messages.success(request, 'Sections saved successfully!')
                return redirect('uca_app:course_sections', course_id=course.id)
            else:  # action == 'next'
                messages.success(request, 'Sections updated successfully!')
                print(f"DEBUG: Redirecting to course_assessments for course_id={course.id}")
                return redirect('uca_app:course_assessments', course_id=course.id)
        else:
            # Formset is not valid, show errors
            print("DEBUG: Formset is not valid")
            messages.error(request, 'Please correct the errors below.')
            for i, form in enumerate(formset):
                print(f"DEBUG: Form {i} errors: {form.errors}")
                if form.errors:
                    for field, errors in form.errors.items():
                        for error in errors:
                            messages.error(request, f'Form {i+1} - {field}: {error}')
    else:
        # Only create formset with existing sections
        existing_sections = course.sections.all()
        print(f"DEBUG: Creating formset with {existing_sections.count()} existing sections")
        formset = DynamicSectionFormSet(instance=course, queryset=existing_sections)
    
    return render(request, 'uca_app/course_sections.html', {
        'course': course,
        'formset': formset,
        'num_sections': num_sections,
    })


def edit_sections(request, course_id):
    """Edit existing sections"""
    course = get_object_or_404(Course, id=course_id)
    
    # Check access permissions
    if request.user.is_authenticated and not request.user.is_staff and course.user and course.user != request.user:
        messages.error(request, 'You do not have permission to edit this course.')
        return redirect('uca_app:course_list')
    
    if request.method == 'POST':
        formset = SectionFormSet(request.POST, instance=course)
        if formset.is_valid():
            # Save the formset
            instances = formset.save(commit=False)
            
            # Delete marked instances
            for obj in formset.deleted_objects:
                obj.delete()
            
            # Save new and updated instances
            new_sections = []
            for instance in instances:
                instance.course = course
                instance.save()
                # Track new sections (those without assessments)
                if not instance.assessments.exists():
                    new_sections.append(instance)
            
            # Create default assessments for new sections
            if new_sections:
                config = course.configuration
                for section in new_sections:
                    # Create quiz assessments
                    for i in range(1, config.num_quizzes + 1):
                        Assessment.objects.create(
                            section=section,
                            assessment_type='quiz',
                            assessment_number=i,
                            max_marks=100,
                            average_marks=0
                        )
                    
                    # Create assignment assessments
                    for i in range(1, config.num_assignments + 1):
                        Assessment.objects.create(
                            section=section,
                            assessment_type='assignment',
                            assessment_number=i,
                            max_marks=100,
                            average_marks=0
                        )
                    
                    # Create other assessment types
                    Assessment.objects.create(
                        section=section,
                        assessment_type='hw',
                        assessment_number=1,
                        max_marks=100,
                        average_marks=0
                    )
                    
                    Assessment.objects.create(
                        section=section,
                        assessment_type='midterm',
                        assessment_number=1,
                        max_marks=100,
                        average_marks=0
                    )
                    
                    Assessment.objects.create(
                        section=section,
                        assessment_type='final',
                        assessment_number=1,
                        max_marks=100,
                        average_marks=0
                    )
                    
                    Assessment.objects.create(
                        section=section,
                        assessment_type='lab',
                        assessment_number=1,
                        max_marks=100,
                        average_marks=0
                    )
                
                messages.success(request, f'Sections updated successfully! Created default assessments for {len(new_sections)} new section(s).')
            else:
                messages.success(request, 'Sections updated successfully!')
            
            return redirect('uca_app:course_analysis', course_id=course.id)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        # Initialize formset with existing sections
        formset = SectionFormSet(instance=course)
    
    return render(request, 'uca_app/edit_sections.html', {
        'course': course,
        'formset': formset,
    })


def course_assessments(request, course_id):
    """Manage assessments for all sections - Step 3"""
    print(f"DEBUG: course_assessments called for course_id={course_id}")
    course = get_object_or_404(Course, id=course_id)
    print(f"DEBUG: Course found: {course.name}")
    
    # Check access permissions
    # Allow access if user is admin OR if course belongs to user OR if course has no user (legacy courses)
    if request.user.is_authenticated and not request.user.is_staff and course.user and course.user != request.user:
        messages.error(request, 'You do not have permission to manage this course.')
        return redirect('uca_app:course_list')
    sections = course.sections.all()
    print(f"DEBUG: Found {sections.count()} sections")
    
    # Check if sections exist
    if not sections.exists():
        print("DEBUG: No sections found, redirecting to course_sections")
        messages.warning(request, 'No sections found. Please go back to Step 2 and create sections first.')
        return redirect('uca_app:course_sections', course_id=course.id)
    
    if request.method == 'POST':
        # Handle assessment data submission
        assessment_data = json.loads(request.POST.get('assessment_data', '{}'))
        action = request.POST.get('action', 'next')
        
        # Clear existing assessments
        Assessment.objects.filter(section__course=course).delete()
        
        # Create new assessments
        for section_id, assessments in assessment_data.items():
            try:
                section = Section.objects.get(id=section_id)
                for assessment in assessments:
                    # Ensure all required fields are present
                    if 'type' not in assessment:
                        continue  # Skip assessments without type
                    
                    Assessment.objects.create(
                        section=section,
                        assessment_type=assessment['type'],
                        assessment_number=assessment.get('number', 1),
                        max_marks=assessment.get('max_marks') if assessment.get('max_marks') else None,
                        average_marks=assessment.get('average_marks') if assessment.get('average_marks') else None
                    )
            except Section.DoesNotExist:
                continue  # Skip if section doesn't exist
        
        if action == 'back':
            messages.success(request, 'Assessment data saved successfully!')
            return redirect('uca_app:course_sections', course_id=course.id)
        elif action == 'save':
            messages.success(request, 'Assessment data saved successfully!')
            return redirect('uca_app:course_assessments', course_id=course.id)
        else:  # action == 'next'
            messages.success(request, 'Assessment data saved successfully!')
            return redirect('uca_app:course_analysis', course_id=course.id)
    
    # Create default assessments for each section if they don't exist
    config = course.configuration
    
    # Ensure we have the correct number of sections based on configuration
    if not sections.exists():
        # Create sections based on course configuration
        for i in range(1, config.num_sections + 1):
            Section.objects.create(
                course=course,
                section_number=i,
                instructor='',
                total_students=0
            )
        sections = course.sections.all()
    
    for section in sections:
        if not section.assessments.exists():
            # Create quiz assessments (only if num_quizzes > 0)
            if config.num_quizzes > 0:
                for i in range(1, config.num_quizzes + 1):
                    Assessment.objects.create(
                        section=section,
                        assessment_type='quiz',
                        assessment_number=i,
                        max_marks=None,
                        average_marks=None
                    )
            
            # Create assignment assessments (only if num_assignments > 0)
            if config.num_assignments > 0:
                for i in range(1, config.num_assignments + 1):
                    Assessment.objects.create(
                        section=section,
                        assessment_type='assignment',
                        assessment_number=i,
                        max_marks=None,
                        average_marks=None
                    )
            
            # Create other assessment types (always create these)
            Assessment.objects.create(
                section=section,
                assessment_type='hw',
                assessment_number=1,
                max_marks=None,
                average_marks=None
            )
            
            Assessment.objects.create(
                section=section,
                assessment_type='midterm',
                assessment_number=1,
                max_marks=None,
                average_marks=None
            )
            
            Assessment.objects.create(
                section=section,
                assessment_type='final',
                assessment_number=1,
                max_marks=None,
                average_marks=None
            )
            
            Assessment.objects.create(
                section=section,
                assessment_type='lab',
                assessment_number=1,
                max_marks=None,
                average_marks=None
            )
    
    print("DEBUG: About to render course_assessments template")
    return render(request, 'uca_app/course_assessments.html', {
        'course': course,
        'sections': sections,
    })


def course_analysis(request, course_id):
    """Course analysis and statistics - Step 4"""
    course = get_object_or_404(Course, id=course_id)
    
    # Check access permissions
    # Allow access if user is admin OR if course belongs to user OR if course has no user (legacy courses)
    if request.user.is_authenticated and not request.user.is_staff and course.user and course.user != request.user:
        messages.error(request, 'You do not have permission to view this course.')
        return redirect('uca_app:course_list')
    
    # Handle POST request to save analysis data
    if request.method == 'POST':
        print(f"DEBUG: POST request received. Content-Type: {request.headers.get('Content-Type')}")
        # Check if this is an AJAX request for saving chart
        if request.headers.get('Content-Type') == 'application/json':
            try:
                data = json.loads(request.body)
                print(f"DEBUG: JSON data received: {data}")
                if data.get('action') == 'save_chart':
                    toggle_states = data.get('toggle_states', {})
                    print(f"DEBUG: Toggle states: {toggle_states}")
                    try:
                        # Save chart with current toggle states
                        result = save_chart_with_toggle_states(course, toggle_states)
                        print(f"DEBUG: Save chart result: {result}")
                        if result:
                            return JsonResponse({'success': True, 'message': 'Chart saved successfully!'})
                        else:
                            return JsonResponse({'success': False, 'error': 'Failed to save chart'})
                    except Exception as e:
                        import traceback
                        traceback.print_exc()
                        return JsonResponse({'success': False, 'error': f'Error saving chart: {str(e)}'})
            except json.JSONDecodeError as e:
                print(f"DEBUG: JSON decode error: {e}")
                return JsonResponse({'success': False, 'error': 'Invalid JSON data'})
        
        # Handle regular form submission
        action = request.POST.get('action', 'next')
        
        if action == 'save_analysis':
            # Save section statistics and analysis data
            save_course_analysis_data(course)
            messages.success(request, 'Analysis data saved successfully!')
            return redirect('uca_app:course_analysis', course_id=course.id)
        elif action == 'next':
            # Save analysis data before proceeding to grade distribution
            save_course_analysis_data(course)
            messages.success(request, 'Analysis data saved! Proceeding to grade distribution.')
            return redirect('uca_app:grade_distribution', course_id=course.id)
        elif action == 'back':
            return redirect('uca_app:course_assessments', course_id=course.id)
    
    sections = course.sections.all()
    config = course.configuration
    
    # Calculate statistics
    section_stats = []
    for section in sections:
        assessments = section.assessments.all()
        
        # Group by assessment type
        quiz_assessments = assessments.filter(assessment_type='quiz')
        assignment_assessments = assessments.filter(assessment_type='assignment')
        hw_assessments = assessments.filter(assessment_type='hw')
        midterm_assessments = assessments.filter(assessment_type='midterm')
        final_assessments = assessments.filter(assessment_type='final')
        lab_assessments = assessments.filter(assessment_type='lab')
        
        # Calculate percentages - convert to actual percentages out of 100
        def calculate_percentage(assessment_list):
            """Calculate percentage for a list of assessments"""
            if not assessment_list:
                return 0.0
            
            total_percentage = 0.0
            valid_assessments = 0
            
            for assessment in assessment_list:
                if (assessment.average_marks is not None and 
                    assessment.max_marks is not None and 
                    assessment.max_marks > 0):
                    percentage = (float(assessment.average_marks) / float(assessment.max_marks)) * 100
                    total_percentage += percentage
                    valid_assessments += 1
            
            return total_percentage / valid_assessments if valid_assessments > 0 else 0.0
        
        quiz_percentage = calculate_percentage(quiz_assessments)
        assignment_percentage = calculate_percentage(assignment_assessments)
        hw_percentage = calculate_percentage(hw_assessments)
        midterm_percentage = calculate_percentage(midterm_assessments)
        final_percentage = calculate_percentage(final_assessments)
        lab_percentage = calculate_percentage(lab_assessments)
        
        # Calculate weighted score - ensure all values are floats
        weighted_score = (
            (float(quiz_percentage) * float(config.quiz_weight or 0) / 100) +
            (float(assignment_percentage) * float(config.assignment_weight or 0) / 100) +
            (float(hw_percentage) * float(config.hw_weight or 0) / 100) +
            (float(midterm_percentage) * float(config.midterm_weight or 0) / 100) +
            (float(final_percentage) * float(config.final_weight or 0) / 100) +
            (float(lab_percentage) * float(config.lab_weight or 0) / 100)
        )
        
        section_stats.append({
            'section': section,
            'quiz_percentage': round(quiz_percentage, 1),
            'assignment_percentage': round(assignment_percentage, 1),
            'hw_percentage': round(hw_percentage, 1),
            'midterm_percentage': round(midterm_percentage, 1),
            'final_percentage': round(final_percentage, 1),
            'lab_percentage': round(lab_percentage, 1),
            'weighted_score': round(weighted_score, 2),
        })
    
    # Create charts
    charts = create_analysis_charts(section_stats, config)
    
    # Calculate total students
    total_students = sections.aggregate(total=Sum('total_students'))['total'] or 0
    
    # Convert section_stats to JSON-serializable format
    section_stats_json = []
    for stat in section_stats:
        section_stats_json.append({
            'section': {
                'section_number': stat['section'].section_number,
                'instructor': stat['section'].instructor,
                'total_students': stat['section'].total_students,
            },
            'quiz_percentage': stat['quiz_percentage'],
            'assignment_percentage': stat['assignment_percentage'],
            'hw_percentage': stat['hw_percentage'],
            'midterm_percentage': stat['midterm_percentage'],
            'final_percentage': stat['final_percentage'],
            'lab_percentage': stat['lab_percentage'],
            'weighted_score': stat['weighted_score'],
        })
    
    return render(request, 'uca_app/course_analysis.html', {
        'course': course,
        'section_stats': section_stats,
        'section_stats_json': json.dumps(section_stats_json),
        'charts': charts,
        'config': config,
        'total_students': total_students,
    })


def grade_distribution(request, course_id):
    """Grade distribution management - Step 5"""
    course = get_object_or_404(Course, id=course_id)
    
    # Check access permissions
    # Allow access if user is admin OR if course belongs to user OR if course has no user (legacy courses)
    if request.user.is_authenticated and not request.user.is_staff and course.user and course.user != request.user:
        messages.error(request, 'You do not have permission to manage this course.')
        return redirect('uca_app:course_list')
    sections = course.sections.all()
    
    if request.method == 'POST':
        # Handle grade distribution data
        grade_data = json.loads(request.POST.get('grade_data', '{}'))
        action = request.POST.get('action', 'next')
        
        # Clear existing grade distributions
        GradeDistribution.objects.filter(course=course).delete()
        
        # Create new grade distributions
        for section_id, grades in grade_data.items():
            try:
                # Ensure section_id is a valid integer
                section_id = int(section_id)
                section = Section.objects.get(id=section_id)
                for grade, count in grades.items():
                    if count > 0:
                        GradeDistribution.objects.create(
                            course=course,
                            section=section,
                            grade=grade,
                            count=count
                        )
            except (ValueError, Section.DoesNotExist) as e:
                # Skip invalid section IDs or non-existent sections
                continue
        
        # Save grade distribution images for PDF report
        save_grade_distribution_images(course)
        
        # Handle different actions
        if action == 'back':
            messages.success(request, 'Grade distribution saved!')
            return redirect('uca_app:course_analysis', course_id=course.id)
        elif action == 'save':
            messages.success(request, 'Grade distribution saved successfully!')
            return redirect('uca_app:grade_distribution', course_id=course.id)
        else:  # action == 'next' or default
            messages.success(request, 'Grade distribution saved successfully!')
            return redirect('uca_app:course_report', course_id=course.id)
    
    # Get existing grade distributions and create a data structure for the template
    grade_distributions = {}
    existing_grade_data = {}
    
    for section in sections:
        section_grades = section.grade_distributions.all()
        grade_distributions[section.id] = section_grades
        
        # Create a dictionary for easy access in template
        existing_grade_data[section.id] = {}
        for grade_dist in section_grades:
            existing_grade_data[section.id][grade_dist.grade] = grade_dist.count
    
    # Get or create default grade categories for this course
    grade_categories = course.grade_categories.all()
    
    # If no grade categories exist, create default ones
    if not grade_categories.exists():
        from .models import GradeCategory
        default_categories = [
            {'grade': 'A', 'min_percentage': 92.5, 'max_percentage': 100, 'order': 0},
            {'grade': 'A-', 'min_percentage': 89.5, 'max_percentage': 92.49, 'order': 1},
            {'grade': 'B+', 'min_percentage': 86.5, 'max_percentage': 89.49, 'order': 2},
            {'grade': 'B', 'min_percentage': 82.5, 'max_percentage': 86.49, 'order': 3},
            {'grade': 'B-', 'min_percentage': 79.5, 'max_percentage': 82.49, 'order': 4},
            {'grade': 'C+', 'min_percentage': 76.5, 'max_percentage': 79.49, 'order': 5},
            {'grade': 'C', 'min_percentage': 72.5, 'max_percentage': 76.49, 'order': 6},
            {'grade': 'C-', 'min_percentage': 69.5, 'max_percentage': 72.49, 'order': 7},
            {'grade': 'D', 'min_percentage': 59.5, 'max_percentage': 69.49, 'order': 8},
            {'grade': 'F', 'min_percentage': 0, 'max_percentage': 59.49, 'order': 9},
        ]
        
        for cat_data in default_categories:
            GradeCategory.objects.create(course=course, **cat_data)
        
        grade_categories = course.grade_categories.all()
    
    return render(request, 'uca_app/grade_distribution.html', {
        'course': course,
        'sections': sections,
        'grade_distributions': grade_distributions,
        'grade_categories': grade_categories,
        'existing_grade_data': existing_grade_data,
    })


def course_report(request, course_id):
    """Generate and view course report"""
    course = get_object_or_404(Course, id=course_id)
    
    # Check access permissions
    # Allow access if user is admin OR if course belongs to user OR if course has no user (legacy courses)
    if request.user.is_authenticated and not request.user.is_staff and course.user and course.user != request.user:
        messages.error(request, 'You do not have permission to access this course.')
        return redirect('uca_app:course_list')
    
    if request.method == 'POST':
        form = ReportGenerationForm(request.POST)
        if form.is_valid():
            export_type = request.POST.get('export_type', 'pdf')
            
            if export_type == 'excel':
                # Generate Excel report
                excel_file = generate_excel_report(course, form.cleaned_data)
                
                # Save report record
                report = CourseReport.objects.create(
                    course=course,
                    title=form.cleaned_data['report_title'],
                    excel_file=excel_file,  # Store Excel file in excel_file field
                    data_snapshot=get_course_snapshot(course)
                )
                
                messages.success(request, 'Excel report generated successfully!')
                return redirect('uca_app:download_report', report_id=report.id)
            else:
                # Generate PDF report
                report_file = generate_pdf_report(course, form.cleaned_data)
                
                # Save report record
                report = CourseReport.objects.create(
                    course=course,
                    title=form.cleaned_data['report_title'],
                    pdf_file=report_file,
                    data_snapshot=get_course_snapshot(course)
                )
                
                messages.success(request, 'PDF report generated successfully!')
                return redirect('uca_app:download_report', report_id=report.id)
    else:
        form = ReportGenerationForm()
    
    return render(request, 'uca_app/course_report.html', {
        'course': course,
        'form': form,
    })


def download_report(request, report_id):
    """Download generated report (PDF or Excel)"""
    report = get_object_or_404(CourseReport, id=report_id)
    
    # Check access permissions
    if request.user.is_authenticated and not request.user.is_staff and report.course.user and report.course.user != request.user:
        messages.error(request, 'You do not have permission to download this report.')
        return redirect('uca_app:course_list')
    
    # Check for PDF file
    if report.pdf_file and report.pdf_file.name:
        try:
            # Open and read the PDF file
            with report.pdf_file.open('rb') as pdf_file:
                response = HttpResponse(pdf_file.read(), content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="{report.title}.pdf"'
                return response
        except (FileNotFoundError, IOError) as e:
            messages.error(request, 'PDF report file not found or cannot be accessed.')
            return redirect('uca_app:course_report', course_id=report.course.id)
    
    # Check for Excel file
    if report.excel_file and report.excel_file.name:
        try:
            # Open and read the Excel file
            with report.excel_file.open('rb') as excel_file:
                response = HttpResponse(excel_file.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                response['Content-Disposition'] = f'attachment; filename="{report.title}.xlsx"'
                return response
        except (FileNotFoundError, IOError) as e:
            messages.error(request, 'Excel report file not found or cannot be accessed.')
            return redirect('uca_app:course_report', course_id=report.course.id)
    
    messages.error(request, 'Report file not found.')
    return redirect('uca_app:course_report', course_id=report.course.id)


def course_list(request):
    """List courses based on user permissions"""
    if not request.user.is_authenticated:
        messages.error(request, 'You must be logged in to view courses.')
        return redirect('uca_app:simple_login')
    
    if request.user.is_staff:
        # Admin sees all courses
        courses = Course.objects.all()
    else:
        # Regular users see only their own courses
        courses = Course.objects.filter(user=request.user)
    
    # Filter by term/semester if provided
    term_filter = request.GET.get('term', '')
    if term_filter:
        courses = courses.filter(term_semester__icontains=term_filter)
    
    # Get unique terms for filter dropdown
    if request.user.is_staff:
        unique_terms = Course.objects.values_list('term_semester', flat=True).distinct().order_by('term_semester')
    else:
        unique_terms = Course.objects.filter(user=request.user).values_list('term_semester', flat=True).distinct().order_by('term_semester')
    
    # Add student count to each course
    for course in courses:
        course.total_students = course.sections.aggregate(total=Sum('total_students'))['total'] or 0
    
    paginator = Paginator(courses, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'uca_app/course_list.html', {
        'page_obj': page_obj,
        'unique_terms': unique_terms,
        'selected_term': term_filter,
    })


def course_detail(request, course_id):
    """View course details"""
    course = get_object_or_404(Course, id=course_id)
    
    # Check access permissions
    # Allow access if user is admin OR if course belongs to user OR if course has no user (legacy courses)
    if request.user.is_authenticated and not request.user.is_staff and course.user and course.user != request.user:
        messages.error(request, 'You do not have permission to view this course.')
        return redirect('uca_app:course_list')
    
    sections = course.sections.all()
    
    return render(request, 'uca_app/course_detail.html', {
        'course': course,
        'sections': sections,
    })


def course_edit(request, course_id):
    """Edit course information - redirect to course creation workflow"""
    course = get_object_or_404(Course, id=course_id)
    
    # Check access permissions
    # Allow access if user is admin OR if course belongs to user OR if course has no user (legacy courses)
    if request.user.is_authenticated and not request.user.is_staff and course.user and course.user != request.user:
        messages.error(request, 'You do not have permission to edit this course.')
        return redirect('uca_app:course_list')
    
    # Store the course ID in session for editing mode
    request.session['editing_course_id'] = course_id
    messages.info(request, f'Editing course: {course.name}. You can update basic information and proceed through the workflow.')
    
    # Redirect to course creation page with existing data
    return redirect('uca_app:course_create')


def course_delete(request, course_id):
    """Delete course"""
    course = get_object_or_404(Course, id=course_id)
    
    # Check access permissions
    # Allow access if user is admin OR if course belongs to user OR if course has no user (legacy courses)
    if request.user.is_authenticated and not request.user.is_staff and course.user and course.user != request.user:
        messages.error(request, 'You do not have permission to delete this course.')
        return redirect('uca_app:course_list')
    
    if request.method == 'POST':
        course_name = course.name
        course.delete()
        messages.success(request, f'Course "{course_name}" deleted successfully!')
        return redirect('uca_app:course_list')
    
    return render(request, 'uca_app/course_delete.html', {
        'course': course,
    })


def project_import(request):
    """Import project from Excel file"""
    if request.method == 'POST':
        form = ProjectImportForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                # Parse Excel file
                excel_file = request.FILES['project_file']
                
                # Create course from Excel data
                course = import_course_from_excel(excel_file, request.user)
                
                messages.success(request, f'Project imported successfully! Course: {course.name}')
                return redirect('uca_app:course_detail', course_id=course.id)
            except Exception as e:
                messages.error(request, f'Error importing project: {str(e)}')
    else:
        form = ProjectImportForm()
    
    return render(request, 'uca_app/project_import.html', {
        'form': form,
    })


def project_export(request, course_id):
    """Export course as JSON project file"""
    course = get_object_or_404(Course, id=course_id)
    
    # Create JSON data
    project_data = export_course_to_json(course)
    
    # Create response
    response = HttpResponse(
        json.dumps(project_data, indent=2, default=str),
        content_type='application/json'
    )
    response['Content-Disposition'] = f'attachment; filename="{course.name}_project.json"'
    return response




# API Views for AJAX requests
@csrf_exempt
def api_calculate_stats(request):
    """API endpoint for calculating statistics"""
    if request.method == 'POST':
        data = json.loads(request.body)
        course_id = data.get('course_id')
        
        try:
            course = Course.objects.get(id=course_id)
            stats = calculate_course_statistics(course)
            return JsonResponse({'success': True, 'stats': stats})
        except Course.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Course not found'})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@csrf_exempt
def api_save_grade_distribution(request):
    """API endpoint for auto-saving grade distribution data"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            course_id = data.get('course_id')
            grade_data = data.get('grade_data', {})
            
            # Get course and check permissions
            course = Course.objects.get(id=course_id)
            if request.user.is_authenticated and not request.user.is_staff and course.user and course.user != request.user:
                return JsonResponse({'success': False, 'error': 'Permission denied'})
            
            # Clear existing grade distributions
            GradeDistribution.objects.filter(course=course).delete()
            
            # Create new grade distributions
            for section_id, grades in grade_data.items():
                try:
                    section_id = int(section_id)
                    section = Section.objects.get(id=section_id, course=course)
                    for grade, count in grades.items():
                        if count > 0:
                            GradeDistribution.objects.create(
                                course=course,
                                section=section,
                                grade=grade,
                                count=count
                            )
                except (ValueError, Section.DoesNotExist):
                    continue
            
            return JsonResponse({'success': True, 'message': 'Grade distribution saved'})
            
        except Course.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Course not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


# Helper functions
def create_analysis_charts(section_stats, config):
    """Create Plotly charts for analysis"""
    charts = {}
    
    # Section comparison chart
    if section_stats:
        # Bar chart for section comparison
        fig = go.Figure()
        
        assessment_types = ['quiz_percentage', 'assignment_percentage', 'hw_percentage', 
                          'midterm_percentage', 'final_percentage', 'lab_percentage']
        colors = ['#A2C4AD', '#C7E1F3', '#F0C4C0', '#BDE3E3', '#DBC6E4', '#FFE4B5']
        
        for i, assessment_type in enumerate(assessment_types):
            fig.add_trace(go.Bar(
                name=assessment_type.replace('_percentage', '').title(),
                x=[f"Section {stat['section'].section_number}" for stat in section_stats],
                y=[stat[assessment_type] for stat in section_stats],
                marker_color=colors[i]
            ))
        
        fig.update_layout(
            title='Section Performance Comparison',
            xaxis_title='Section',
            yaxis_title='Percentage',
            barmode='group',
            height=500
        )
        
        charts['section_comparison'] = {
            'data': fig.to_dict()['data'],
            'layout': fig.to_dict()['layout']
        }
        
        # Weighted score chart
        fig2 = go.Figure(go.Bar(
            x=[f"Section {stat['section'].section_number}" for stat in section_stats],
            y=[stat['weighted_score'] for stat in section_stats],
            marker_color='#5ec776'
        ))
        
        fig2.update_layout(
            title='Weighted Scores by Section',
            xaxis_title='Section',
            yaxis_title='Weighted Score (%)',
            height=400
        )
        
        charts['weighted_scores'] = {
            'data': fig2.to_dict()['data'],
            'layout': fig2.to_dict()['layout']
        }
    
    return charts

def generate_pdf_report(course, options):
    """Generate comprehensive PDF report with course info and images"""
    import os
    import uuid
    from datetime import datetime
    from django.conf import settings
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    from PIL import Image as PILImage
    
    # Create reports directory if it doesn't exist
    reports_dir = os.path.join(settings.MEDIA_ROOT, 'reports')
    os.makedirs(reports_dir, exist_ok=True)
    
    # Create unique filename
    filename = f"report_{course.id}_{uuid.uuid4().hex[:8]}.pdf"
    file_path = os.path.join(reports_dir, filename)
    
    # Get course data
    sections = course.sections.all()
    config = course.configuration
    total_sections = sections.count()
    total_students = sum(section.total_students for section in sections)
    
    # Course information variables (matching the format from report.py)
    course_name = course.name or ""
    semester = course.term_semester or ""
    coordinator = course.coordinator or ""
    now = datetime.now().strftime("%d %B %Y")
    page_w, page_h = letter
    
    # Create PDF canvas
    c = canvas.Canvas(file_path, pagesize=letter)
    
    # First page - Course Information
    # Add logo if exists
    logo_path = os.path.join(settings.MEDIA_ROOT, '..', 'logo.png')
    if os.path.exists(logo_path):
        lw, lh = 60, 60
        c.drawImage(logo_path, page_w - 40 - lw, page_h - 40 - lh, width=lw, height=lh, mask='auto')
    
    # Department header
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(page_w/2, page_h - 120, "Department of Physics")
    
    # Report title
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(page_w/2, page_h - 180, "Course Assessment Report")
    
    # Course information
    c.setFont("Helvetica", 12)
    c.drawCentredString(page_w/2, page_h - 240, f"Course Name: {course_name}")
    c.drawCentredString(page_w/2, page_h - 270, f"Term / Semester: {semester}")
    c.drawCentredString(page_w/2, page_h - 300, f"Coordinator: {coordinator}")
    c.drawCentredString(page_w/2, page_h - 330, f"Sections: {total_sections}    Students: {total_students}")
    
    # Generated date
    c.setFont("Helvetica-Oblique", 8)
    c.drawRightString(page_w - 40, 30, f"Generated: {now}")
    
    c.showPage()
    
    # Second page - Section Statistics (if available)
    try:
        analysis_data = CourseAnalysisData.objects.get(course=course)
        if analysis_data.section_statistics:
            c.setFont("Helvetica-Bold", 14)
            c.drawString(40, page_h - 50, "Section Statistics")
            
            # Check for section statistics table image
            table2_path = os.path.join(reports_dir, f"section_stats_table_{course.id}.png")
            if os.path.exists(table2_path):
                img = PILImage.open(table2_path)
                iw, ih = img.size
                tw = page_w - 80
                th = tw * ih / iw
                y_table = page_h - 80 - th
                c.drawImage(table2_path, 40, y_table, width=tw, height=th, mask='auto')
            
            # Check for section statistics chart image
            chart2_path = os.path.join(reports_dir, f"section_stats_chart_{course.id}.png")
            if os.path.exists(chart2_path):
                img2 = PILImage.open(chart2_path)
                iw2, ih2 = img2.size
                cw = page_w - 80
                ch = cw * ih2 / iw2
                y_chart = y_table - 20 - ch if 'y_table' in locals() else page_h - 80 - ch
                c.drawImage(chart2_path, 40, y_chart, width=cw, height=ch, mask='auto')
            
            c.showPage()
    except CourseAnalysisData.DoesNotExist:
        pass
    
    # Third page - Grade Distribution
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, page_h - 50, "Grade Distribution")
    
    # Check for grade distribution table image
    grade_table_path = os.path.join(reports_dir, f"grade_dist_table_{course.id}.png")
    if os.path.exists(grade_table_path):
        img3 = PILImage.open(grade_table_path)
        iw3, ih3 = img3.size
        tw3 = page_w - 80
        th3 = tw3 * ih3 / iw3
        y_t3 = page_h - 80 - th3
        c.drawImage(grade_table_path, 40, y_t3, width=tw3, height=th3, mask='auto')
        
        # Check for grade distribution chart image
        grade_chart_path = os.path.join(reports_dir, f"grade_dist_chart_{course.id}.png")
        print(f"DEBUG: Looking for grade chart at: {grade_chart_path}")
        print(f"DEBUG: Grade chart exists: {os.path.exists(grade_chart_path)}")
        if os.path.exists(grade_chart_path):
            img4 = PILImage.open(grade_chart_path)
            iw4, ih4 = img4.size
            cw4 = page_w - 80
            ch4 = cw4 * ih4 / iw4
            y_c3 = y_t3 - 20 - ch4
            c.drawImage(grade_chart_path, 40, y_c3, width=cw4, height=ch4, mask='auto')
            print(f"DEBUG: Grade chart added to PDF successfully")
        else:
            print(f"DEBUG: Grade chart not found, skipping chart in PDF")
    
    # Save the PDF
    c.save()
    
    # Return relative path from media root
    return os.path.join('reports', filename)

def generate_excel_report(course, options):
    """Generate comprehensive Excel report with all course data"""
    import os
    import pandas as pd
    from django.conf import settings
    from datetime import datetime
    
    # Create reports directory if it doesn't exist
    reports_dir = os.path.join(settings.MEDIA_ROOT, 'reports')
    os.makedirs(reports_dir, exist_ok=True)
    
    # Create unique filename
    import uuid
    filename = f"report_{course.id}_{uuid.uuid4().hex[:8]}.xlsx"
    file_path = os.path.join(reports_dir, filename)
    
    # Get course data
    sections = course.sections.all()
    config = course.configuration
    total_sections = sections.count()
    total_students = sum(section.total_students for section in sections)
    
    # Create Excel writer
    with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
        # Course Information Sheet
        course_info = pd.DataFrame({
            'Field': ['Course Name', 'Course Code', 'Term/Semester', 'Coordinator', 'Total Sections', 'Number of Quizzes', 'Number of Assignments', 'Quiz Weight', 'Assignment Weight', 'HW Weight', 'Midterm Weight', 'Final Weight', 'Lab Weight', 'Generated On'],
            'Value': [course.name, course.code, course.term_semester, course.coordinator, total_sections, config.num_quizzes, config.num_assignments, config.quiz_weight, config.assignment_weight, config.hw_weight, config.midterm_weight, config.final_weight, config.lab_weight, datetime.now().strftime("%d %B %Y")]
        })
        course_info.to_excel(writer, sheet_name='Course Info', index=False)
        
        # Assessment Data Sheet - Original min and max values from step 3
        assessment_data = []
        for section in sections:
            assessments = section.assessments.all()
            
            # Group by assessment type
            quiz_assessments = assessments.filter(assessment_type='quiz')
            assignment_assessments = assessments.filter(assessment_type='assignment')
            hw_assessments = assessments.filter(assessment_type='hw')
            midterm_assessments = assessments.filter(assessment_type='midterm')
            final_assessments = assessments.filter(assessment_type='final')
            lab_assessments = assessments.filter(assessment_type='lab')
            
            # Create assessment data row
            assessment_row = {
                'Section': f"Section {section.section_number}",
                'Instructor': section.instructor,
                'Students': section.total_students,
            }
            
            # Add quiz data
            for i, quiz in enumerate(quiz_assessments, 1):
                assessment_row[f'Quiz {i} Max'] = float(quiz.max_marks) if quiz.max_marks is not None else 0.0
                assessment_row[f'Quiz {i} Avg'] = float(quiz.average_marks) if quiz.average_marks is not None else 0.0
            
            # Add assignment data
            for i, assignment in enumerate(assignment_assessments, 1):
                assessment_row[f'Assignment {i} Max'] = float(assignment.max_marks) if assignment.max_marks is not None else 0.0
                assessment_row[f'Assignment {i} Avg'] = float(assignment.average_marks) if assignment.average_marks is not None else 0.0
            
            # Add other assessment types
            if hw_assessments.exists():
                hw = hw_assessments.first()
                assessment_row['HW Max'] = float(hw.max_marks) if hw.max_marks is not None else 0.0
                assessment_row['HW Avg'] = float(hw.average_marks) if hw.average_marks is not None else 0.0
            
            if midterm_assessments.exists():
                midterm = midterm_assessments.first()
                assessment_row['Midterm Max'] = float(midterm.max_marks) if midterm.max_marks is not None else 0.0
                assessment_row['Midterm Avg'] = float(midterm.average_marks) if midterm.average_marks is not None else 0.0
            
            if final_assessments.exists():
                final = final_assessments.first()
                assessment_row['Final Max'] = float(final.max_marks) if final.max_marks is not None else 0.0
                assessment_row['Final Avg'] = float(final.average_marks) if final.average_marks is not None else 0.0
            
            if lab_assessments.exists():
                lab = lab_assessments.first()
                assessment_row['Lab Max'] = float(lab.max_marks) if lab.max_marks is not None else 0.0
                assessment_row['Lab Avg'] = float(lab.average_marks) if lab.average_marks is not None else 0.0
            
            assessment_data.append(assessment_row)
        
        if assessment_data:
            assessment_df = pd.DataFrame(assessment_data)
            assessment_df.to_excel(writer, sheet_name='Assessment Data', index=False)
        
        # Section Statistics Sheet - Use saved analysis data if available (calculated percentages)
        try:
            analysis_data = CourseAnalysisData.objects.get(course=course)
            if analysis_data.section_statistics:
                sections_data = []
                for stat in analysis_data.section_statistics:
                    sections_data.append({
                        'Section': f"Section {stat['section_number']}",
                        'Instructor': stat['instructor'],
                        'Students': stat['total_students'],
                        'Quiz %': f"{stat['quiz_percentage']:.1f}",
                        'Assignment %': f"{stat['assignment_percentage']:.1f}",
                        'HW %': f"{stat['hw_percentage']:.1f}",
                        'Midterm %': f"{stat['midterm_percentage']:.1f}",
                        'Final %': f"{stat['final_percentage']:.1f}",
                        'Lab %': f"{stat['lab_percentage']:.1f}",
                        'Weighted Score': f"{stat['weighted_score']:.2f}"
                    })
                
                sections_df = pd.DataFrame(sections_data)
                sections_df.to_excel(writer, sheet_name='Section Statistics', index=False)
            else:
                # Fallback to calculating on the fly
                sections_data = []
                for section in sections:
                    stats = calculate_section_statistics(section, config)
                    sections_data.append({
                        'Section': f"Section {section.section_number}",
                        'Instructor': section.instructor,
                        'Students': section.total_students,
                        'Quiz %': f"{stats['quiz_percentage']:.1f}",
                        'Assignment %': f"{stats['assignment_percentage']:.1f}",
                        'HW %': f"{stats['hw_percentage']:.1f}",
                        'Midterm %': f"{stats['midterm_percentage']:.1f}",
                        'Final %': f"{stats['final_percentage']:.1f}",
                        'Lab %': f"{stats['lab_percentage']:.1f}",
                        'Weighted Score': f"{stats['weighted_score']:.2f}"
                    })
                
                sections_df = pd.DataFrame(sections_data)
                sections_df.to_excel(writer, sheet_name='Section Statistics', index=False)
        except CourseAnalysisData.DoesNotExist:
            # Fallback to calculating on the fly
            sections_data = []
            for section in sections:
                stats = calculate_section_statistics(section, config)
                sections_data.append({
                    'Section': f"Section {section.section_number}",
                    'Instructor': section.instructor,
                    'Students': section.total_students,
                    'Quiz %': f"{stats['quiz_percentage']:.1f}",
                    'Assignment %': f"{stats['assignment_percentage']:.1f}",
                    'HW %': f"{stats['hw_percentage']:.1f}",
                    'Midterm %': f"{stats['midterm_percentage']:.1f}",
                    'Final %': f"{stats['final_percentage']:.1f}",
                    'Lab %': f"{stats['lab_percentage']:.1f}",
                    'Weighted Score': f"{stats['weighted_score']:.2f}"
                })
            
            sections_df = pd.DataFrame(sections_data)
            sections_df.to_excel(writer, sheet_name='Section Statistics', index=False)
        
        # Grade Distribution Sheet
        grade_distributions = GradeDistribution.objects.filter(course=course)
        if grade_distributions:
            # Get actual grade categories from the model instead of hardcoding
            grade_choices = [choice[0] for choice in GradeDistribution.GRADE_CHOICES]
            grades = grade_choices  # Use the actual model choices
            
            grade_data = {}
            
            for grade_dist in grade_distributions:
                section_num = grade_dist.section.section_number
                if section_num not in grade_data:
                    grade_data[section_num] = {}
                grade_data[section_num][grade_dist.grade] = grade_dist.count
            
            # Create comprehensive grade distribution table
            grade_table_data = []
            for grade in grades:
                row = {'Grade': grade}
                total_count = 0
                for section_num in sorted(grade_data.keys()):
                    count = grade_data[section_num].get(grade, 0)
                    row[f'Section {section_num}'] = count
                    total_count += count
                row['Total'] = total_count
                freq = (total_count / total_students * 100) if total_students > 0 else 0
                row['Frequency %'] = f"{freq:.1f}"
                grade_table_data.append(row)
            
            grade_df = pd.DataFrame(grade_table_data)
            grade_df.to_excel(writer, sheet_name='Grade Distribution', index=False)
        
    
    return os.path.join('reports', filename)


def calculate_course_statistics(course):
    """Calculate comprehensive course statistics"""
    sections = course.sections.all()
    config = course.configuration
    
    total_students = sections.aggregate(total=Sum('total_students'))['total'] or 0
    total_sections = sections.count()
    
    # Calculate overall averages
    overall_stats = {
        'total_students': total_students,
        'total_sections': total_sections,
        'quiz_avg': 0,
        'assignment_avg': 0,
        'hw_avg': 0,
        'midterm_avg': 0,
        'final_avg': 0,
        'lab_avg': 0,
        'weighted_avg': 0,
    }
    
    if sections:
        # Calculate averages across all sections
        quiz_scores = []
        assignment_scores = []
        hw_scores = []
        midterm_scores = []
        final_scores = []
        lab_scores = []
        weighted_scores = []
        
        for section in sections:
            stats = calculate_section_statistics(section, config)
            quiz_scores.append(stats['quiz_percentage'])
            assignment_scores.append(stats['assignment_percentage'])
            hw_scores.append(stats['hw_percentage'])
            midterm_scores.append(stats['midterm_percentage'])
            final_scores.append(stats['final_percentage'])
            lab_scores.append(stats['lab_percentage'])
            weighted_scores.append(stats['weighted_score'])
        
        overall_stats.update({
            'quiz_avg': round(sum(quiz_scores) / len(quiz_scores), 1),
            'assignment_avg': round(sum(assignment_scores) / len(assignment_scores), 1),
            'hw_avg': round(sum(hw_scores) / len(hw_scores), 1),
            'midterm_avg': round(sum(midterm_scores) / len(midterm_scores), 1),
            'final_avg': round(sum(final_scores) / len(final_scores), 1),
            'lab_avg': round(sum(lab_scores) / len(lab_scores), 1),
            'weighted_avg': round(sum(weighted_scores) / len(weighted_scores), 2),
        })
    
    return overall_stats


def calculate_section_statistics(section, config):
    """Calculate statistics for a single section"""
    assessments = section.assessments.all()
    
    # Group by assessment type
    quiz_assessments = assessments.filter(assessment_type='quiz')
    assignment_assessments = assessments.filter(assessment_type='assignment')
    hw_assessments = assessments.filter(assessment_type='hw')
    midterm_assessments = assessments.filter(assessment_type='midterm')
    final_assessments = assessments.filter(assessment_type='final')
    lab_assessments = assessments.filter(assessment_type='lab')
    
    def calculate_percentage(assessment_list):
        """Calculate percentage for a list of assessments"""
        if not assessment_list:
            return 0.0
        
        total_percentage = 0.0
        valid_assessments = 0
        
        for assessment in assessment_list:
            if (assessment.average_marks is not None and 
                assessment.max_marks is not None and 
                assessment.max_marks > 0):
                percentage = (float(assessment.average_marks) / float(assessment.max_marks)) * 100
                total_percentage += percentage
                valid_assessments += 1
        
        return total_percentage / valid_assessments if valid_assessments > 0 else 0.0
    
    # Calculate percentages - convert to actual percentages out of 100
    quiz_percentage = calculate_percentage(quiz_assessments)
    assignment_percentage = calculate_percentage(assignment_assessments)
    hw_percentage = calculate_percentage(hw_assessments)
    midterm_percentage = calculate_percentage(midterm_assessments)
    final_percentage = calculate_percentage(final_assessments)
    lab_percentage = calculate_percentage(lab_assessments)
    
    # Calculate weighted score - ensure all values are floats and handle None weights
    weighted_score = (
        (float(quiz_percentage) * float(config.quiz_weight or 0) / 100) +
        (float(assignment_percentage) * float(config.assignment_weight or 0) / 100) +
        (float(hw_percentage) * float(config.hw_weight or 0) / 100) +
        (float(midterm_percentage) * float(config.midterm_weight or 0) / 100) +
        (float(final_percentage) * float(config.final_weight or 0) / 100) +
        (float(lab_percentage) * float(config.lab_weight or 0) / 100)
    )
    
    return {
        'quiz_percentage': quiz_percentage,
        'assignment_percentage': assignment_percentage,
        'hw_percentage': hw_percentage,
        'midterm_percentage': midterm_percentage,
        'final_percentage': final_percentage,
        'lab_percentage': lab_percentage,
        'weighted_score': weighted_score,
    }


def get_course_snapshot(course):
    """Get a snapshot of course data for storage"""
    sections_data = []
    for section in course.sections.all():
        section_data = {
            'section_number': section.section_number,
            'instructor': section.instructor,
            'total_students': section.total_students,
            'assessments': []
        }
        
        for assessment in section.assessments.all():
            section_data['assessments'].append({
                'type': assessment.assessment_type,
                'number': assessment.assessment_number,
                'max_marks': float(assessment.max_marks) if assessment.max_marks is not None else 0.0,
                'average_marks': float(assessment.average_marks) if assessment.average_marks is not None else 0.0,
            })
        
        sections_data.append(section_data)
    
    # Include saved analysis data if available
    analysis_data = None
    try:
        analysis_data_obj = CourseAnalysisData.objects.get(course=course)
        analysis_data = {
            'section_statistics': analysis_data_obj.section_statistics,
            'has_graph': bool(analysis_data_obj.overall_statistics_graph),
            'created_at': analysis_data_obj.created_at.isoformat(),
            'updated_at': analysis_data_obj.updated_at.isoformat(),
        }
    except CourseAnalysisData.DoesNotExist:
        analysis_data = None
    
    return {
        'course_name': course.name,
        'course_code': course.code,
        'term_semester': course.term_semester,
        'coordinator': course.coordinator,
        'sections': sections_data,
        'analysis_data': analysis_data,
        'configuration': {
            'num_sections': course.configuration.num_sections,
            'num_quizzes': course.configuration.num_quizzes,
            'num_assignments': course.configuration.num_assignments,
            'weights': {
                'quiz': float(course.configuration.quiz_weight) if course.configuration.quiz_weight is not None else 0.0,
                'assignment': float(course.configuration.assignment_weight) if course.configuration.assignment_weight is not None else 0.0,
                'hw': float(course.configuration.hw_weight) if course.configuration.hw_weight is not None else 0.0,
                'midterm': float(course.configuration.midterm_weight) if course.configuration.midterm_weight is not None else 0.0,
                'final': float(course.configuration.final_weight) if course.configuration.final_weight is not None else 0.0,
                'lab': float(course.configuration.lab_weight) if course.configuration.lab_weight is not None else 0.0,
            }
        }
    }


def import_course_from_json(json_data):
    """Import course from JSON data"""
    # Create course
    course = Course.objects.create(
        name=json_data.get('course_name', 'Imported Course'),
        code=json_data.get('course_code', ''),
        term_semester=json_data.get('term_semester', ''),
        coordinator=json_data.get('coordinator', '')
    )
    
    # Create configuration
    config_data = json_data.get('configuration', {})
    CourseConfiguration.objects.create(
        course=course,
        num_sections=config_data.get('num_sections', 1),
        num_quizzes=config_data.get('num_quizzes', 4),
        num_assignments=config_data.get('num_assignments', 0),
        quiz_weight=config_data.get('weights', {}).get('quiz', 15.00),
        assignment_weight=config_data.get('weights', {}).get('assignment', 15.00),
        hw_weight=config_data.get('weights', {}).get('hw', 10.00),
        midterm_weight=config_data.get('weights', {}).get('midterm', 30.00),
        final_weight=config_data.get('weights', {}).get('final', 25.00),
        lab_weight=config_data.get('weights', {}).get('lab', 5.00),
    )
    
    # Create sections and assessments
    for section_data in json_data.get('sections', []):
        section = Section.objects.create(
            course=course,
            section_number=section_data.get('section_number', 1),
            instructor=section_data.get('instructor', ''),
            total_students=section_data.get('total_students', 0)
        )
        
        for assessment_data in section_data.get('assessments', []):
            Assessment.objects.create(
                section=section,
                assessment_type=assessment_data.get('type', 'quiz'),
                assessment_number=assessment_data.get('number', 1),
                max_marks=assessment_data.get('max_marks', 0),
                average_marks=assessment_data.get('average_marks', 0)
            )
    
    return course


def export_course_to_json(course):
    """Export course to JSON format"""
    return get_course_snapshot(course)


def import_course_from_excel(excel_file, user):
    """Import course from Excel file"""
    import pandas as pd
    import io
    
    # Read the Excel file
    excel_data = pd.read_excel(excel_file, sheet_name=None)
    
    # Extract course info from Course Info sheet
    course_info_sheet = excel_data.get('Course Info')
    if course_info_sheet is None:
        raise ValueError("Course Info sheet not found in Excel file")
    
    # Convert course info to dictionary
    course_info = {}
    for _, row in course_info_sheet.iterrows():
        field = row['Field']
        value = row['Value']
        if field == 'Course Name':
            course_info['name'] = str(value)
        elif field == 'Course Code':
            course_info['code'] = str(value)
        elif field == 'Term/Semester':
            course_info['term_semester'] = str(value)
        elif field == 'Coordinator':
            course_info['coordinator'] = str(value)
        elif field == 'Total Sections':
            course_info['num_sections'] = int(value)
        elif field == 'Number of Quizzes':
            course_info['num_quizzes'] = int(value)
        elif field == 'Number of Assignments':
            course_info['num_assignments'] = int(value)
        elif field == 'Quiz Weight':
            course_info['quiz_weight'] = float(value)
        elif field == 'Assignment Weight':
            course_info['assignment_weight'] = float(value)
        elif field == 'HW Weight':
            course_info['hw_weight'] = float(value)
        elif field == 'Midterm Weight':
            course_info['midterm_weight'] = float(value)
        elif field == 'Final Weight':
            course_info['final_weight'] = float(value)
        elif field == 'Lab Weight':
            course_info['lab_weight'] = float(value)
    
    # Create course
    course = Course.objects.create(
        name=course_info.get('name', 'Imported Course'),
        code=course_info.get('code', ''),
        term_semester=course_info.get('term_semester', ''),
        coordinator=course_info.get('coordinator', ''),
        user=user
    )
    
    # Create configuration with imported weight values
    config = CourseConfiguration.objects.create(
        course=course,
        num_sections=course_info.get('num_sections', 1),
        num_quizzes=course_info.get('num_quizzes', 0),
        num_assignments=course_info.get('num_assignments', 0),
        quiz_weight=course_info.get('quiz_weight', 15.0),
        assignment_weight=course_info.get('assignment_weight', 15.0),
        hw_weight=course_info.get('hw_weight', 10.0),
        midterm_weight=course_info.get('midterm_weight', 30.0),
        final_weight=course_info.get('final_weight', 25.0),
        lab_weight=course_info.get('lab_weight', 5.0),
    )
    
    # Extract section data from Section Statistics sheet
    section_stats_sheet = excel_data.get('Section Statistics')
    if section_stats_sheet is not None:
        for _, row in section_stats_sheet.iterrows():
            section_name = str(row['Section'])
            section_number = int(section_name.replace('Section ', ''))
            instructor = str(row['Instructor'])
            students = int(row['Students'])
            
            # Create section
            section = Section.objects.create(
                course=course,
                section_number=section_number,
                instructor=instructor,
                total_students=students
            )
            
            # Create default assessments for this section
            # Quiz assessments
            for i in range(1, config.num_quizzes + 1):
                Assessment.objects.create(
                    section=section,
                    assessment_type='quiz',
                    assessment_number=i,
                    max_marks=100,
                    average_marks=0
                )
            
            # Assignment assessments
            for i in range(1, config.num_assignments + 1):
                Assessment.objects.create(
                    section=section,
                    assessment_type='assignment',
                    assessment_number=i,
                    max_marks=100,
                    average_marks=0
                )
            
            # Other assessment types
            Assessment.objects.create(
                section=section,
                assessment_type='hw',
                assessment_number=1,
                max_marks=100,
                average_marks=0
            )
            
            Assessment.objects.create(
                section=section,
                assessment_type='midterm',
                assessment_number=1,
                max_marks=100,
                average_marks=0
            )
            
            Assessment.objects.create(
                section=section,
                assessment_type='final',
                assessment_number=1,
                max_marks=100,
                average_marks=0
            )
            
            Assessment.objects.create(
                section=section,
                assessment_type='lab',
                assessment_number=1,
                max_marks=100,
                average_marks=0
            )
    
    # Extract assessment data from Assessment Data sheet if available
    assessment_data_sheet = excel_data.get('Assessment Data')
    if assessment_data_sheet is not None:
        for _, row in assessment_data_sheet.iterrows():
            section_name = str(row['Section'])
            section_number = int(section_name.replace('Section ', ''))
            
            try:
                section = Section.objects.get(course=course, section_number=section_number)
                
                # Update quiz assessments
                for i in range(1, config.num_quizzes + 1):
                    max_col = f'Quiz {i} Max'
                    avg_col = f'Quiz {i} Avg'
                    if max_col in row and avg_col in row:
                        try:
                            assessment = Assessment.objects.get(
                                section=section,
                                assessment_type='quiz',
                                assessment_number=i
                            )
                            assessment.max_marks = float(row[max_col]) if pd.notna(row[max_col]) else None
                            assessment.average_marks = float(row[avg_col]) if pd.notna(row[avg_col]) else None
                            assessment.save()
                        except Assessment.DoesNotExist:
                            pass
                
                # Update assignment assessments
                for i in range(1, config.num_assignments + 1):
                    max_col = f'Assignment {i} Max'
                    avg_col = f'Assignment {i} Avg'
                    if max_col in row and avg_col in row:
                        try:
                            assessment = Assessment.objects.get(
                                section=section,
                                assessment_type='assignment',
                                assessment_number=i
                            )
                            assessment.max_marks = float(row[max_col]) if pd.notna(row[max_col]) else None
                            assessment.average_marks = float(row[avg_col]) if pd.notna(row[avg_col]) else None
                            assessment.save()
                        except Assessment.DoesNotExist:
                            pass
                
                # Update other assessment types
                assessment_types = ['HW', 'Midterm', 'Final', 'Lab']
                for assessment_type in assessment_types:
                    max_col = f'{assessment_type} Max'
                    avg_col = f'{assessment_type} Avg'
                    if max_col in row and avg_col in row:
                        try:
                            assessment = Assessment.objects.get(
                                section=section,
                                assessment_type=assessment_type.lower(),
                                assessment_number=1
                            )
                            assessment.max_marks = float(row[max_col]) if pd.notna(row[max_col]) else None
                            assessment.average_marks = float(row[avg_col]) if pd.notna(row[avg_col]) else None
                            assessment.save()
                        except Assessment.DoesNotExist:
                            pass
                            
            except Section.DoesNotExist:
                continue
    
    # Extract grade distribution data if available
    grade_dist_sheet = excel_data.get('Grade Distribution')
    if grade_dist_sheet is not None:
        # Get actual grade categories from the model instead of hardcoding
        grade_choices = [choice[0] for choice in GradeDistribution.GRADE_CHOICES]
        grades = grade_choices  # Use the actual model choices
        
        for _, row in grade_dist_sheet.iterrows():
            grade = str(row['Grade'])
            if grade in grades:
                # Find sections for this course
                sections = course.sections.all()
                for section in sections:
                    section_col = f'Section {section.section_number}'
                    if section_col in row:
                        count = int(row[section_col]) if pd.notna(row[section_col]) else 0
                        if count > 0:
                            GradeDistribution.objects.create(
                                course=course,
                                section=section,
                                grade=grade,
                                count=count
                            )
    
    return course


def simple_register(request):
    """Simple user registration"""
    if request.user.is_authenticated:
        return redirect('uca_app:index')
    
    if request.method == 'POST':
        form = SimpleUserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created successfully for {username}! You can now log in.')
            return redirect('uca_app:simple_login')
    else:
        form = SimpleUserRegistrationForm()
    
    return render(request, 'uca_app/simple_register.html', {'form': form})


def simple_login(request):
    """Simple user login using email or username"""
    if request.user.is_authenticated:
        return redirect('uca_app:index')
    
    if request.method == 'POST':
        form = SimpleLoginForm(request.POST)
        if form.is_valid():
            email_or_username = form.cleaned_data['email_or_username']
            password = form.cleaned_data['password']
            
            # Try to authenticate with username first, then email
            user = authenticate(request, username=email_or_username, password=password)
            
            # If username authentication failed, try email
            if user is None:
                try:
                    user_obj = User.objects.get(email=email_or_username)
                    user = authenticate(request, username=user_obj.username, password=password)
                except User.DoesNotExist:
                    pass
            
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {user.first_name or user.username}!')
                return redirect('uca_app:index')
            else:
                messages.error(request, 'Invalid email/username or password. Please try again.')
    else:
        form = SimpleLoginForm()
    
    return render(request, 'uca_app/simple_login.html', {'form': form})


def simple_logout(request):
    """Simple logout"""
    from django.contrib.auth import logout
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('uca_app:index')


def edit_grade_categories(request, course_id):
    """Edit grade categories for a course"""
    course = get_object_or_404(Course, id=course_id)
    
    # Check access permissions
    if request.user.is_authenticated and not request.user.is_staff and course.user and course.user != request.user:
        messages.error(request, 'You do not have permission to edit this course.')
        return redirect('uca_app:course_list')
    
    grade_categories = course.grade_categories.all()
    
    if request.method == 'POST':
        # Handle form submission
        from .forms import GradeCategoryForm
        from .models import GradeCategory
        
        # Delete existing categories
        grade_categories.delete()
        
        # Create new categories from form data
        for key, value in request.POST.items():
            if key.startswith('grade_') and key.endswith('_grade'):
                index = key.replace('grade_', '').replace('_grade', '')
                grade = value
                min_percentage = request.POST.get(f'grade_{index}_min', 0)
                max_percentage = request.POST.get(f'grade_{index}_max', None)
                order = request.POST.get(f'grade_{index}_order', 0)
                
                if grade and min_percentage:
                    GradeCategory.objects.create(
                        course=course,
                        grade=grade,
                        min_percentage=min_percentage,
                        max_percentage=max_percentage if max_percentage else None,
                        order=order
                    )
        
        messages.success(request, 'Grade categories updated successfully!')
        return redirect('uca_app:grade_distribution', course_id=course.id)
    
    return render(request, 'uca_app/edit_grade_categories.html', {
        'course': course,
        'grade_categories': grade_categories,
    })


def save_course_analysis_data(course):
    """Save section statistics and analysis data for reports"""
    import os
    import base64
    from django.conf import settings
    from django.core.files.base import ContentFile
    
    # Calculate section statistics
    sections = course.sections.all()
    config = course.configuration
    
    section_stats = []
    for section in sections:
        stats = calculate_section_statistics(section, config)
        section_stats.append({
            'section_number': section.section_number,
            'instructor': section.instructor,
            'total_students': section.total_students,
            'quiz_percentage': stats['quiz_percentage'],
            'assignment_percentage': stats['assignment_percentage'],
            'hw_percentage': stats['hw_percentage'],
            'midterm_percentage': stats['midterm_percentage'],
            'final_percentage': stats['final_percentage'],
            'lab_percentage': stats['lab_percentage'],
            'weighted_score': stats['weighted_score'],
        })
    
    # Save section statistics images for PDF report
    save_section_statistics_images(course, section_stats, config)
    
    # Create or update CourseAnalysisData
    analysis_data, created = CourseAnalysisData.objects.get_or_create(
        course=course,
        defaults={'section_statistics': section_stats}
    )
    
    if not created:
        # Update existing record
        analysis_data.section_statistics = section_stats
        analysis_data.save()
    
    return analysis_data


def test_kaleido_functionality():
    """Test function to verify Kaleido is working properly"""
    try:
        import kaleido
        print("✅ Kaleido imported successfully")
        
        import plotly.graph_objects as go
        import plotly.io as pio
        import tempfile
        import os
        
        # Create a simple test figure
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=[1, 2, 3], y=[1, 2, 3], name='Test'))
        fig.update_layout(title="Kaleido Test Chart")
        
        # Try to save as PNG
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
            pio.write_image(fig, tmp_file.name, width=400, height=300, format='png')
            
            if os.path.exists(tmp_file.name) and os.path.getsize(tmp_file.name) > 0:
                print("✅ Kaleido PNG creation successful")
                os.unlink(tmp_file.name)  # Clean up
                return True
            else:
                print("❌ Kaleido PNG creation failed - file not created or empty")
                return False
                
    except Exception as e:
        print(f"❌ Kaleido test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def save_chart_with_toggle_states(course, toggle_states):
    """Save chart with specific toggle states using Plotly"""
    import os
    import plotly.graph_objects as go
    import plotly.io as pio
    from django.conf import settings
    
    # Test Kaleido functionality first
    print("DEBUG: Testing Kaleido functionality...")
    kaleido_working = test_kaleido_functionality()
    
    # Use the test result to determine if kaleido is available
    kaleido_available = kaleido_working
    if kaleido_available:
        print("DEBUG: Kaleido is working properly, will save as PNG")
    else:
        print("DEBUG: Kaleido is not working properly, will save as HTML")
    
    # Create media/reports directory if it doesn't exist
    reports_dir = os.path.join(settings.MEDIA_ROOT, 'reports')
    os.makedirs(reports_dir, exist_ok=True)
    
    # Get section statistics data
    sections = course.sections.all()
    config = course.configuration
    
    # Calculate statistics (same logic as course_analysis view)
    section_stats = []
    for section in sections:
        assessments = section.assessments.all()
        
        # Group by assessment type
        quiz_assessments = assessments.filter(assessment_type='quiz')
        assignment_assessments = assessments.filter(assessment_type='assignment')
        hw_assessments = assessments.filter(assessment_type='hw')
        midterm_assessments = assessments.filter(assessment_type='midterm')
        final_assessments = assessments.filter(assessment_type='final')
        lab_assessments = assessments.filter(assessment_type='lab')
        
        # Calculate percentages
        def calculate_percentage(assessment_list):
            if not assessment_list:
                return 0.0
            total_percentage = 0.0
            valid_assessments = 0
            for assessment in assessment_list:
                if (assessment.average_marks is not None and 
                    assessment.max_marks is not None and 
                    assessment.max_marks > 0):
                    percentage = (float(assessment.average_marks) / float(assessment.max_marks)) * 100
                    total_percentage += percentage
                    valid_assessments += 1
            return total_percentage / valid_assessments if valid_assessments > 0 else 0.0
        
        quiz_percentage = calculate_percentage(quiz_assessments)
        assignment_percentage = calculate_percentage(assignment_assessments)
        hw_percentage = calculate_percentage(hw_assessments)
        midterm_percentage = calculate_percentage(midterm_assessments)
        final_percentage = calculate_percentage(final_assessments)
        lab_percentage = calculate_percentage(lab_assessments)
        
        # Calculate weighted score
        weighted_score = (
            (float(quiz_percentage) * float(config.quiz_weight or 0) / 100) +
            (float(assignment_percentage) * float(config.assignment_weight or 0) / 100) +
            (float(hw_percentage) * float(config.hw_weight or 0) / 100) +
            (float(midterm_percentage) * float(config.midterm_weight or 0) / 100) +
            (float(final_percentage) * float(config.final_weight or 0) / 100) +
            (float(lab_percentage) * float(config.lab_weight or 0) / 100)
        )
        
        section_stats.append({
            'section_number': section.section_number,
            'quiz_percentage': round(quiz_percentage, 1),
            'assignment_percentage': round(assignment_percentage, 1),
            'hw_percentage': round(hw_percentage, 1),
            'midterm_percentage': round(midterm_percentage, 1),
            'final_percentage': round(final_percentage, 1),
            'lab_percentage': round(lab_percentage, 1),
            'weighted_score': round(weighted_score, 2),
        })
    
    if not section_stats:
        return False
    
    # Generate chart using Plotly with toggle states
    sections = [f"Section {stat['section_number']}" for stat in section_stats]
    
    # Define assessment types and their colors (matching web app exactly)
    assessment_types = [
        {'key': 'quiz_percentage', 'name': 'Quiz Avg', 'color': '#55C2C3'},
        {'key': 'assignment_percentage', 'name': 'Assign Avg', 'color': '#A2C4AD'},
        {'key': 'hw_percentage', 'name': 'HW Avg', 'color': '#C7E1F3'},
        {'key': 'midterm_percentage', 'name': 'Midterm Avg', 'color': '#F0C4C0'},
        {'key': 'final_percentage', 'name': 'Final Avg', 'color': '#BDE3E3'},
        {'key': 'lab_percentage', 'name': 'Lab Avg', 'color': '#DBC6E4'},
        {'key': 'weighted_score', 'name': 'Weighted', 'color': '#696969'}
    ]
    
    # Create traces for each assessment type with toggle states
    chart_data = []
    for assessment in assessment_types:
        values = [stat[assessment['key']] for stat in section_stats]
        
        # Determine visibility based on toggle states
        is_visible = True
        if assessment['name'] == 'Quiz Avg':
            is_visible = toggle_states.get('quiz', True)
        elif assessment['name'] == 'Assign Avg':
            is_visible = toggle_states.get('assignment', False)
        elif assessment['name'] == 'HW Avg':
            is_visible = toggle_states.get('hw', True)
        elif assessment['name'] == 'Midterm Avg':
            is_visible = toggle_states.get('midterm', True)
        elif assessment['name'] == 'Final Avg':
            is_visible = toggle_states.get('final', True)
        elif assessment['name'] == 'Lab Avg':
            is_visible = toggle_states.get('lab', True)
        elif assessment['name'] == 'Weighted':
            is_visible = toggle_states.get('weighted', True)
        
        chart_data.append(go.Bar(
            x=sections,
            y=values,
            name=assessment['name'],
            marker=dict(
                color=assessment['color'],
                opacity=0.8,
                line=dict(color='darkgray', width=1)
            ),
            visible=is_visible,
            text=[f"{v:.1f}" for v in values],
            textposition='inside',
            textfont=dict(color='black', size=12)
        ))
    
    # Create layout (matching web app exactly)
    layout = go.Layout(
        title=dict(
            text='Course Performance Analysis by Section',
            font=dict(size=20, color='#000000'),
            x=0.5,
            xanchor='center'
        ),
        xaxis=dict(
            title=dict(text='Sections', font=dict(size=18, color='#000000')),
            tickfont=dict(size=16, color='#000000'),
            showgrid=True,
            gridcolor='rgba(0,0,0,0.1)',
            showline=True,
            linecolor='#000000',
            linewidth=1,
            mirror=True
        ),
        yaxis=dict(
            title=dict(text='Percentage (%)', font=dict(size=18, color='#000000')),
            tickfont=dict(size=16, color='#000000'),
            showgrid=True,
            gridcolor='rgba(0,0,0,0.1)',
            showline=True,
            linecolor='#000000',
            linewidth=1,
            mirror=True,
            range=[0, 100]
        ),
        barmode='group',
        showlegend=True,
        height=650,
        plot_bgcolor='rgba(255,255,255,0.2)',
        paper_bgcolor='rgba(255,255,255,0.1)',
        font=dict(color='#333'),
        legend=dict(
            bgcolor='rgba(255,255,255,0.9)',
            bordercolor='rgba(0,0,0,0.4)',
            borderwidth=2,
            x=0.5,
            y=1.02,
            xanchor='center',
            yanchor='bottom',
            orientation='h',
            font=dict(size=12)
        )
    )
    
    # Create figure
    fig = go.Figure(data=chart_data, layout=layout)
    
    # Save chart based on kaleido availability
    if kaleido_available:
        # Save as PNG (high quality) using kaleido
        chart_path = os.path.join(reports_dir, f"section_stats_chart_{course.id}.png")
        print(f"DEBUG: Attempting to save chart to: {chart_path}")
        try:
            print(f"DEBUG: About to call pio.write_image with kaleido")
            pio.write_image(fig, chart_path, width=1400, height=650, scale=2, format='png')
            print(f"Chart saved successfully to: {chart_path}")
            print(f"DEBUG: Chart file exists after save: {os.path.exists(chart_path)}")
            if os.path.exists(chart_path):
                file_size = os.path.getsize(chart_path)
                print(f"DEBUG: Chart file size: {file_size} bytes")
                if file_size > 0:
                    print("DEBUG: Chart file created successfully with content")
                    return True
                else:
                    print("DEBUG: Chart file is empty, falling back to HTML")
                    kaleido_available = False
            else:
                print("DEBUG: Chart file was not created, falling back to HTML")
                kaleido_available = False

        except Exception as e:
            print(f"Error saving chart with Plotly/Kaleido: {e}")
            print(f"Error type: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            # Fallback to HTML
            kaleido_available = False
    
    if not kaleido_available:
        # Use matplotlib to create PNG (same approach as grade distribution)
        print("DEBUG: Using matplotlib to create PNG chart (same as grade distribution)...")
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            import numpy as np
            
            # Create matplotlib version of the chart
            sections = [f"Section {stat['section_number']}" for stat in section_stats]
            
            # Create matplotlib figure
            fig_mpl, ax = plt.subplots(figsize=(14, 6.5), dpi=100)
            
            # Plot each assessment type
            assessment_types = [
                {'key': 'quiz_percentage', 'name': 'Quiz Avg', 'color': '#55C2C3'},
                {'key': 'assignment_percentage', 'name': 'Assign Avg', 'color': '#A2C4AD'},
                {'key': 'hw_percentage', 'name': 'HW Avg', 'color': '#C7E1F3'},
                {'key': 'midterm_percentage', 'name': 'Midterm Avg', 'color': '#F0C4C0'},
                {'key': 'final_percentage', 'name': 'Final Avg', 'color': '#BDE3E3'},
                {'key': 'lab_percentage', 'name': 'Lab Avg', 'color': '#DBC6E4'},
                {'key': 'weighted_score', 'name': 'Weighted', 'color': '#696969'}
            ]
            
            x = np.arange(len(sections))
            width = 0.12
            
            for i, assessment in enumerate(assessment_types):
                values = [stat[assessment['key']] for stat in section_stats]
                ax.bar(x + i * width, values, width, label=assessment['name'], 
                      color=assessment['color'], alpha=0.8)
            
            ax.set_xlabel('Sections', fontsize=12, fontweight='bold')
            ax.set_ylabel('Percentage (%)', fontsize=12, fontweight='bold')
            ax.set_title('Course Performance Analysis by Section', fontsize=14, fontweight='bold')
            ax.set_xticks(x + width * 3)
            ax.set_xticklabels(sections)
            ax.legend(bbox_to_anchor=(0.5, 1.02), loc='lower center', ncol=7)
            ax.grid(True, alpha=0.3)
            
            # Save as PNG (same method as grade distribution)
            png_path = os.path.join(reports_dir, f"section_stats_chart_{course.id}.png")
            plt.tight_layout()
            plt.savefig(png_path, dpi=300, bbox_inches='tight')
            plt.close(fig_mpl)
            
            print(f"DEBUG: Section statistics PNG created using matplotlib: {png_path}")
            print(f"DEBUG: PNG file exists: {os.path.exists(png_path)}")
            if os.path.exists(png_path):
                file_size = os.path.getsize(png_path)
                print(f"DEBUG: PNG file size: {file_size} bytes")
            
            return True
                
        except Exception as e:
            print(f"DEBUG: Matplotlib chart creation failed: {e}")
            import traceback
            traceback.print_exc()
            return False


def save_section_statistics_images(course, section_stats, config):
    """Save section statistics table and chart as PNG images for PDF report using Plotly"""
    import os
    import json
    import plotly.graph_objects as go
    import plotly.io as pio
    from django.conf import settings
    
    # Test Kaleido availability first
    kaleido_available = False
    try:
        import kaleido
        print("Kaleido imported successfully for section statistics")
        kaleido_available = True
    except ImportError as e:
        print(f"Kaleido import error: {e}")
        print("Kaleido package not available. Chart will be saved as HTML instead.")
    except Exception as e:
        print(f"Error checking Kaleido: {e}")
        print("Kaleido package not available. Chart will be saved as HTML instead.")
    
    # Create media/reports directory if it doesn't exist
    reports_dir = os.path.join(settings.MEDIA_ROOT, 'reports')
    os.makedirs(reports_dir, exist_ok=True)
    
    if section_stats:
        # Create section statistics table using matplotlib (keep existing table)
        import matplotlib
        matplotlib.use('Agg')  # Use non-interactive backend
        import matplotlib.pyplot as plt
        
        cols = ["Section", "Instructor", "Students", "Quiz %", "Assign %", "HW %", "Midterm %", "Final %", "Lab %", "Weighted Score"]
        table_data = []
        
        for stat in section_stats:
            row = [
                f"Section {stat['section_number']}",
                stat['instructor'],
                stat['total_students'],
                f"{stat['quiz_percentage']:.1f}",
                f"{stat['assignment_percentage']:.1f}",
                f"{stat['hw_percentage']:.1f}",
                f"{stat['midterm_percentage']:.1f}",
                f"{stat['final_percentage']:.1f}",
                f"{stat['lab_percentage']:.1f}",
                f"{stat['weighted_score']:.2f}"
            ]
            table_data.append(row)
        
        # Generate table image
        fig, ax = plt.subplots(figsize=(12, len(section_stats) * 0.4 + 1), dpi=200)
        ax.axis('off')
        
        table = ax.table(cellText=table_data, colLabels=cols, loc='center')
        table.auto_set_font_size(False)
        table.set_fontsize(8)
        
        # Set column widths
        lengths = np.array([len(c) for c in cols], dtype=float)
        lengths = lengths / lengths.sum()
        for (row, col), cell in table.get_celld().items():
            cell.set_width(lengths[col])
            cell.set_text_props(ha='center', va='center')
        
        table.scale(1, 1)
        fig.tight_layout()
        
        # Save table image
        table_path = os.path.join(reports_dir, f"section_stats_table_{course.id}.png")
        fig.savefig(table_path, dpi=300, bbox_inches='tight')
        plt.close(fig)
        
        # Generate chart using Plotly (exact same as web application)
        sections = [f"Section {stat['section_number']}" for stat in section_stats]
        
        # Define assessment types and their colors (matching web app exactly)
        assessment_types = [
            {'key': 'quiz_percentage', 'name': 'Quiz Avg', 'color': '#4ECDC4'},
        ]
        
        # Only include assignment if weight > 0
        if config.assignment_weight > 0:
            assessment_types.append({'key': 'assignment_percentage', 'name': 'Assign Avg', 'color': '#00B894'})
        
        # Add remaining assessment types
        assessment_types.extend([
            {'key': 'hw_percentage', 'name': 'HW Avg', 'color': '#96CEB4'},
            {'key': 'midterm_percentage', 'name': 'Midterm Avg', 'color': '#F0C4C0'},
            {'key': 'final_percentage', 'name': 'Final Avg', 'color': '#BDE3E3'},
            {'key': 'lab_percentage', 'name': 'Lab Avg', 'color': '#DBC6E4'},
            {'key': 'weighted_score', 'name': 'Weighted', 'color': '#696969'}
        ])
        
        # Create traces for each assessment type (matching web app)
        chart_data = []
        for assessment in assessment_types:
            values = [stat[assessment['key']] for stat in section_stats]
            
            # Set assignment trace as not visible by default (matching web app)
            # Only applies if assignment is included (weight > 0)
            is_visible = assessment['name'] != 'Assign Avg'
            
            chart_data.append(go.Bar(
                x=sections,
                y=values,
                name=assessment['name'],
                marker=dict(
                    color=assessment['color'],
                    opacity=0.8,
                    line=dict(color='darkgray', width=1)
                ),
                visible=is_visible,
                text=[f"{v:.1f}" for v in values],
                textposition='outside',
                textfont=dict(color='black', size=14)
            ))
        
        # Create layout (matching web app exactly)
        layout = go.Layout(
            title=dict(
                text='Course Performance Analysis by Section',
                font=dict(size=20, color='#000000', weight='bold'),
                x=0.5,
                xanchor='center',
                y=0.95
            ),
            xaxis=dict(
                title=dict(text='Sections', font=dict(size=20, color='#000000', weight='bold')),
                tickfont=dict(size=16, color='#000000', weight='bold'),
                showgrid=True,
                gridcolor='rgba(0,0,0,0.1)',
                showline=True,
                linecolor='#000000',
                linewidth=1,
                mirror=True
            ),
            yaxis=dict(
                title=dict(text='Percentage (%)', font=dict(size=20, color='#000000', weight='bold')),
                tickfont=dict(size=16, color='#000000', weight='bold'),
                showgrid=True,
                gridcolor='rgba(0,0,0,0.1)',
                showline=True,
                linecolor='#000000',
                linewidth=1,
                mirror=True,
                range=[0, 104]
            ),
            barmode='group',
            showlegend=True,
            height=650,
            plot_bgcolor='rgba(255,255,255,0.2)',
            paper_bgcolor='rgba(255,255,255,0.1)',
            font=dict(color='#333'),
            legend=dict(
                bgcolor='rgba(255,255,255,0.9)',
                bordercolor='rgba(0,0,0,0.4)',
                borderwidth=2,
                x=0.5,
                y=1.02,
                xanchor='center',
                yanchor='bottom',
                orientation='h',
                font=dict(size=16, weight='bold')
            )
        )
        
        # Create figure
        fig = go.Figure(data=chart_data, layout=layout)
        
        # Save chart based on kaleido availability
        if kaleido_available:
            # Save as PNG (high quality) using kaleido
            chart_path = os.path.join(reports_dir, f"section_stats_chart_{course.id}.png")
            try:
                pio.write_image(fig, chart_path, width=1400, height=650, scale=2, format='png')
                print(f"Section statistics chart saved successfully to: {chart_path}")
            except Exception as e:
                print(f"Error saving section statistics chart with Plotly/Kaleido: {e}")
                import traceback
                traceback.print_exc()
                # Fallback to HTML
                kaleido_available = False
        
        if not kaleido_available:
            # Save as HTML when kaleido is not available
            chart_path = os.path.join(reports_dir, f"section_stats_chart_{course.id}.html")
            try:
                fig.write_html(chart_path)
                print(f"Section statistics chart saved as HTML (kaleido not available): {chart_path}")
            except Exception as e:
                print(f"Error saving section statistics chart as HTML: {e}")
                import traceback
                traceback.print_exc()
                chart_path = None
        
        return {
            'table_path': table_path,
            'chart_path': chart_path
        }
    
    return None


def save_grade_distribution_images(course):
    """Save grade distribution table and chart as PNG images for PDF report using Plotly"""
    import os
    import matplotlib
    matplotlib.use('Agg')  # Use non-interactive backend
    import matplotlib.pyplot as plt
    import plotly.graph_objects as go
    import plotly.io as pio
    from django.conf import settings
    
    print(f"DEBUG: save_grade_distribution_images called for course {course.id}")
    
    # Create media/reports directory if it doesn't exist
    reports_dir = os.path.join(settings.MEDIA_ROOT, 'reports')
    os.makedirs(reports_dir, exist_ok=True)
    
    # Get grade distribution data
    sections = course.sections.all()
    grade_distributions = GradeDistribution.objects.filter(course=course)
    
    print(f"DEBUG: Found {grade_distributions.count()} grade distributions for course {course.id}")
    
    if grade_distributions.exists():
        # Get actual grade categories from the model
        grade_choices = [choice[0] for choice in GradeDistribution.GRADE_CHOICES]
        grades = grade_choices
        
        # Create grade distribution table
        grade_data = {}
        for grade_dist in grade_distributions:
            section_num = grade_dist.section.section_number
            if section_num not in grade_data:
                grade_data[section_num] = {}
            grade_data[section_num][grade_dist.grade] = grade_dist.count
        
        # Calculate totals
        total_students = sum(section.total_students for section in sections)
        
        # Create table data
        table_data = []
        for grade in grades:
            row_vals = []
            total_count = 0
            for section_num in sorted(grade_data.keys()):
                count = grade_data[section_num].get(grade, 0)
                row_vals.append(count)
                total_count += count
            
            freq = (total_count / total_students * 100) if total_students > 0 else 0
            table_data.append([grade] + row_vals + [total_count, f"{freq:.1f}"])
        
        # Create column headers
        cols = ["Grade Distribution"] + [f"Sec{num}" for num in sorted(grade_data.keys())] + ["Tot.stud", "Freq(%)"]
        
        # Generate table image
        fig, ax = plt.subplots(figsize=(10, len(grades) * 0.3 + 1), dpi=200)
        ax.axis('off')
        
        table = ax.table(cellText=table_data, colLabels=cols, loc='center')
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        
        # Set column widths
        lengths = np.array([len(c) for c in cols], dtype=float)
        lengths = lengths / lengths.sum()
        for (row, col), cell in table.get_celld().items():
            cell.set_width(lengths[col])
            cell.set_text_props(ha='center', va='center')
        
        table.scale(1.2, 1.2)
        fig.tight_layout()
        
        # Save table image
        table_path = os.path.join(reports_dir, f"grade_dist_table_{course.id}.png")
        fig.savefig(table_path, dpi=300, bbox_inches='tight')
        plt.close(fig)
        
        # Generate stacked bar chart with section colors and frequency line (matching web app)
        fig, ax1 = plt.subplots(figsize=(14, 8), dpi=200)
        
        # Section colors from web application
        section_colors = [
            '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', 
            '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9',
            '#FF9F43', '#10AC84', '#EE5A24', '#0984E3', '#6C5CE7',
            '#A29BFE', '#FD79A8', '#FDCB6E', '#E17055', '#00B894'
        ]
        
        # Prepare data for stacked bars
        section_numbers = sorted(grade_data.keys())
        bottom = [0] * len(grades)
        
        # Create stacked bars for each section
        for i, section_num in enumerate(section_numbers):
            section_data = [grade_data[section_num].get(grade, 0) for grade in grades]
            color = section_colors[i % len(section_colors)]
            
            bars = ax1.bar(grades, section_data, bottom=bottom, 
                          label=f'Section {section_num}', 
                          color=color, edgecolor='white', linewidth=0.5)
            
            # Add value labels within each bar segment
            for j, (bar, value) in enumerate(zip(bars, section_data)):
                if value > 0:  # Only show label if there's a value
                    # Calculate the center position of this bar segment
                    bar_center = bar.get_x() + bar.get_width() / 2
                    bar_middle = bar.get_y() + bar.get_height() / 2
                    
                    # Add text label with white color for visibility
                    ax1.text(bar_center, bar_middle, str(value), 
                            ha='center', va='center', fontsize=10, 
                            color='black', fontweight='bold')
            
            # Update bottom for stacking
            bottom = [b + s for b, s in zip(bottom, section_data)]
        
        # Calculate total counts and frequencies
        total_counts = [sum(grade_data[section_num].get(grade, 0) for section_num in grade_data.keys()) for grade in grades]
        # Use the actual total students from sections, not from grade distribution counts
        # This ensures consistency with the web interface
        total_students_from_sections = sum(section.total_students for section in sections)
        frequencies = [(count / total_students_from_sections * 100) if total_students_from_sections > 0 else 0 for count in total_counts]
        
        # Calculate max_students early for use in label positioning
        max_students = max(total_counts) if total_counts else 0
        
        # Create second y-axis for frequency
        ax2 = ax1.twinx()
        
        # Add frequency line with red color (matching web app)
        line = ax2.plot(grades, frequencies, 'o-', color='#FF0000', linewidth=3, 
                       markersize=8, label='Frequency (%)')
        
        # Add frequency value labels above the bar graph (matching web app positioning)
        for i, (grade, freq, total_count) in enumerate(zip(grades, frequencies, total_counts)):
            if total_count > 0:  # Only show label if there are students
                # Position label above the bar graph using same logic as web app
                # Web app uses: totalCounts[index] + (maxBarHeight * 0.08)
                label_y = total_count + (max_students * 0.08)  # 8% spacing above bar
                
                # Add text label with same styling as web app
                ax1.text(i, label_y, f'{freq:.1f}%', ha='center', va='bottom', 
                        fontsize=12, color='#000000', fontweight='bold',
                        bbox=dict(boxstyle='round,pad=0.3', facecolor='white', 
                                 edgecolor='lightgray', alpha=0.8))
        
        # Set labels and titles
        ax1.set_xlabel('Grade', fontsize=16, fontweight='bold')
        ax1.set_ylabel('Number of Students', fontsize=16, fontweight='bold')
        ax2.set_ylabel('Frequency (%)', fontsize=16, fontweight='bold')
        
        # Set y-axis ranges to accommodate labels (matching web app logic)
        # Left y-axis (Number of Students): Add extra space for frequency labels
        max_students_y = max_students if max_students > 0 else 10
        # Calculate the highest label position: max_students + (max_students * 0.08) + some padding
        max_label_height = max_students + (max_students * 0.08) + (max_students * 0.15)  # 15% extra padding
        ax1.set_ylim(0, max_label_height)
        
        # Right y-axis (Frequency): Show max frequency value + extra space
        max_frequency_y = max(frequencies) if frequencies else 100
        ax2.set_ylim(0, max_frequency_y + 15)  # Increased range to accommodate text (matching web app)
        
        # Set y-axis ticks to show the maximum values clearly
        ax1.set_yticks([0, max_students_y//2, max_students_y])
        ax2.set_yticks([0, max_frequency_y//2, max_frequency_y])
        
        
        # Add grid
        ax1.grid(axis='y', alpha=0.3)
        ax1.grid(axis='x', alpha=0.3)
        
        # Add legend at the top outside the graph horizontally (max 5 per row)
        max_cols = min(6, len(section_numbers))  # Limit to maximum 5 columns per row
        ax1.legend(loc='upper center', bbox_to_anchor=(0.5, 1.2), ncol=max_cols, 
                  frameon=True, fancybox=True, shadow=True, fontsize=12)
        ax2.legend(loc='upper center', bbox_to_anchor=(0.5, 1.08), 
                  frameon=True, fancybox=True, shadow=True, fontsize=12)
        
        # Add title above the legends
        fig.suptitle('Grade Distribution', fontsize=18, fontweight='bold', y=1)
        
        # Rotate x-axis labels
        plt.xticks(rotation=45)
        fig.tight_layout()
        
        # Save chart image
        chart_path = os.path.join(reports_dir, f"grade_dist_chart_{course.id}.png")
        print(f"DEBUG: Saving grade distribution chart to: {chart_path}")
        fig.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close(fig)
        print(f"DEBUG: Grade distribution chart saved successfully")
        
        return {
            'table_path': table_path,
            'chart_path': chart_path
        }
    
    return None
