from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User
import json


class Course(models.Model):
    """Main course model"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='courses', null=True, blank=True)
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50, blank=True)
    term_semester = models.CharField(max_length=100)
    coordinator = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.term_semester}"


class CourseConfiguration(models.Model):
    """Course configuration settings"""
    course = models.OneToOneField(Course, on_delete=models.CASCADE, related_name='configuration')
    num_sections = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(50)])
    num_quizzes = models.PositiveIntegerField(default=4, validators=[MinValueValidator(0), MaxValueValidator(20)])
    num_assignments = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(20)])
    
    # Weights for different assessment types
    quiz_weight = models.PositiveIntegerField(default=24)
    assignment_weight = models.PositiveIntegerField(default=0)
    hw_weight = models.PositiveIntegerField(default=6)
    midterm_weight = models.PositiveIntegerField(default=20)
    final_weight = models.PositiveIntegerField(default=30)
    lab_weight = models.PositiveIntegerField(default=20)
    
    def get_total_weight(self):
        """Calculate total weight percentage"""
        return (self.quiz_weight + self.assignment_weight + self.hw_weight + 
                self.midterm_weight + self.final_weight + self.lab_weight)
    
    def is_weight_valid(self):
        """Check if weights sum to 100%"""
        return abs(self.get_total_weight() - 100.00) < 0.01
    
    def __str__(self):
        return f"Config for {self.course.name}"


class Section(models.Model):
    """Course section model"""
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='sections')
    section_number = models.PositiveIntegerField()
    instructor = models.CharField(max_length=200)
    total_students = models.PositiveIntegerField()
    
    class Meta:
        unique_together = ['course', 'section_number']
        ordering = ['section_number']
    
    def __str__(self):
        return f"{self.course.name} - Section {self.section_number}"


class Assessment(models.Model):
    """Assessment data for each section"""
    ASSESSMENT_TYPES = [
        ('quiz', 'Quiz'),
        ('assignment', 'Assignment'),
        ('hw', 'Homework'),
        ('midterm', 'Midterm'),
        ('final', 'Final'),
        ('lab', 'Lab'),
    ]
    
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='assessments')
    assessment_type = models.CharField(max_length=20, choices=ASSESSMENT_TYPES)
    assessment_number = models.PositiveIntegerField(default=1)  # For quizzes/assignments
    max_marks = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    average_marks = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    
    class Meta:
        unique_together = ['section', 'assessment_type', 'assessment_number']
        ordering = ['assessment_type', 'assessment_number']
    
    def get_percentage(self):
        """Calculate percentage score"""
        if self.max_marks > 0:
            return (self.average_marks / self.max_marks) * 100
        return 0
    
    def __str__(self):
        if self.assessment_type in ['quiz', 'assignment']:
            return f"{self.section} - {self.get_assessment_type_display()} {self.assessment_number}"
        return f"{self.section} - {self.get_assessment_type_display()}"


class GradeDistribution(models.Model):
    """Grade distribution data"""
    GRADE_CHOICES = [
        ('A', 'A (92.5–100%)'),
        ('A-', 'A- (89.5–<92.5%)'),
        ('B+', 'B+ (86.5–<89.5%)'),
        ('B', 'B (82.5–<86.5%)'),
        ('B-', 'B- (79.5–<82.5%)'),
        ('C+', 'C+ (76.5–<79.5%)'),
        ('C', 'C (72.5–<76.5%)'),
        ('C-', 'C- (69.5–<72.5%)'),
        ('D', 'D (59.5–<69.5%)'),
        ('F', 'F (<59.5%)'),
    ]
    
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='grade_distributions')
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='grade_distributions')
    grade = models.CharField(max_length=3, choices=GRADE_CHOICES)
    count = models.PositiveIntegerField(default=0)
    
    class Meta:
        unique_together = ['course', 'section', 'grade']
        ordering = ['grade']
    
    def __str__(self):
        return f"{self.section} - {self.grade}: {self.count}"


class CourseReport(models.Model):
    """Generated course reports"""
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='reports')
    title = models.CharField(max_length=200)
    pdf_file = models.FileField(upload_to='reports/', blank=True, null=True)
    excel_file = models.FileField(upload_to='reports/', blank=True, null=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    data_snapshot = models.JSONField(default=dict)  # Store report data as JSON
    
    class Meta:
        ordering = ['-generated_at']
    
    def __str__(self):
        return f"{self.course.name} - {self.title}"


class ProjectFile(models.Model):
    """Project file for import/export functionality"""
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='project_files')
    file = models.FileField(upload_to='projects/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.course.name} - {self.file.name}"


class GradeCategory(models.Model):
    """Editable grade categories for courses"""
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='grade_categories')
    grade = models.CharField(max_length=5)  # A, A-, B+, etc.
    min_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    max_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    order = models.IntegerField(default=0)  # For ordering grades
    
    class Meta:
        ordering = ['order']
        unique_together = ['course', 'grade']
    
    def __str__(self):
        if self.max_percentage:
            return f"{self.grade} ({self.min_percentage}-{self.max_percentage}%)"
        else:
            return f"{self.grade} ({self.min_percentage}%+)"
    
    @property
    def range_display(self):
        """Return formatted range for display"""
        if self.max_percentage:
            return f"{self.min_percentage}-{self.max_percentage}%"
        else:
            return f"{self.min_percentage}%+"


class CourseAnalysisData(models.Model):
    """Store section statistics and analysis data for reports"""
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='analysis_data')
    section_statistics = models.JSONField(default=dict)  # Store section statistics table data
    overall_statistics_graph = models.ImageField(upload_to='analysis_graphs/', blank=True, null=True)  # Store graph as image
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"Analysis Data for {self.course.name} - {self.updated_at.strftime('%Y-%m-%d %H:%M')}"