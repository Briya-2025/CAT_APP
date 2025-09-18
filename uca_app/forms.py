from django import forms
from django.forms import formset_factory, inlineformset_factory
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from decimal import Decimal
from .models import Course, CourseConfiguration, Section, Assessment, GradeDistribution


class CourseForm(forms.ModelForm):
    """Form for course basic information"""
    class Meta:
        model = Course
        fields = ['name', 'code', 'term_semester', 'coordinator']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter course name'
            }),
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., PHYS101'
            }),
            'term_semester': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Fall 2024'
            }),
            'coordinator': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Course coordinator name'
            }),
        }

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if not name or not name.strip():
            raise forms.ValidationError("Course name is required.")
        return name.strip()

    def clean_term_semester(self):
        term = self.cleaned_data.get('term_semester')
        if not term or not term.strip():
            raise forms.ValidationError("Term/Semester is required.")
        return term.strip()


class CourseConfigurationForm(forms.ModelForm):
    """Form for course configuration"""
    class Meta:
        model = CourseConfiguration
        fields = ['num_sections', 'num_quizzes', 'num_assignments',
                 'quiz_weight', 'assignment_weight', 'hw_weight',
                 'midterm_weight', 'final_weight', 'lab_weight']
        widgets = {
            'num_sections': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '50'
            }),
            'num_quizzes': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '20'
            }),
            'num_assignments': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '20'
            }),
            'quiz_weight': forms.NumberInput(attrs={
                'class': 'form-control weight-input',
                'min': '0',
                'max': '100'
            }),
            'assignment_weight': forms.NumberInput(attrs={
                'class': 'form-control weight-input',
                'min': '0',
                'max': '100'
            }),
            'hw_weight': forms.NumberInput(attrs={
                'class': 'form-control weight-input',
                'min': '0',
                'max': '100'
            }),
            'midterm_weight': forms.NumberInput(attrs={
                'class': 'form-control weight-input',
                'min': '0',
                'max': '100'
            }),
            'final_weight': forms.NumberInput(attrs={
                'class': 'form-control weight-input',
                'min': '0',
                'max': '100'
            }),
            'lab_weight': forms.NumberInput(attrs={
                'class': 'form-control weight-input',
                'min': '0',
                'max': '100'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        total_weight = (
            cleaned_data.get('quiz_weight', 0) +
            cleaned_data.get('assignment_weight', 0) +
            cleaned_data.get('hw_weight', 0) +
            cleaned_data.get('midterm_weight', 0) +
            cleaned_data.get('final_weight', 0) +
            cleaned_data.get('lab_weight', 0)
        )
        
        if abs(total_weight - 100) > 0:
            raise forms.ValidationError(
                f"Weights must sum to 100%. Current total: {total_weight}%"
            )
        
        return cleaned_data


class SectionForm(forms.ModelForm):
    """Form for section information"""
    class Meta:
        model = Section
        fields = ['section_number', 'instructor', 'total_students']
        widgets = {
            'section_number': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1'
            }),
            'instructor': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Instructor name'
            }),
            'total_students': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1'
            }),
        }


class AssessmentForm(forms.ModelForm):
    """Form for assessment data"""
    class Meta:
        model = Assessment
        fields = ['assessment_type', 'assessment_number', 'max_marks', 'average_marks']
        widgets = {
            'assessment_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'assessment_number': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1'
            }),
            'max_marks': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'average_marks': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        max_marks = cleaned_data.get('max_marks', 0)
        average_marks = cleaned_data.get('average_marks', 0)
        
        if max_marks < 0 or average_marks < 0:
            raise forms.ValidationError("Marks cannot be negative.")
        
        if average_marks > max_marks:
            raise forms.ValidationError("Average marks cannot exceed maximum marks.")
        
        if max_marks == 0 and average_marks > 0:
            raise forms.ValidationError("Cannot have average marks when maximum is 0.")
        
        return cleaned_data


class GradeDistributionForm(forms.ModelForm):
    """Form for grade distribution"""
    class Meta:
        model = GradeDistribution
        fields = ['grade', 'count']
        widgets = {
            'grade': forms.Select(attrs={
                'class': 'form-control'
            }),
            'count': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),
        }


# Formset factories
SectionFormSet = inlineformset_factory(
    Course, Section,
    form=SectionForm,
    extra=3,  # Allow up to 3 additional sections
    can_delete=True,
    min_num=1,
    validate_min=True
)

AssessmentFormSet = inlineformset_factory(
    Section, Assessment,
    form=AssessmentForm,
    extra=1,
    can_delete=True,
    min_num=1
)

GradeDistributionFormSet = inlineformset_factory(
    Section, GradeDistribution,
    form=GradeDistributionForm,
    extra=1,
    can_delete=True,
    min_num=1
)


class ProjectImportForm(forms.Form):
    """Form for importing project files"""
    project_file = forms.FileField(
        label='Select Project File',
        help_text='Upload an Excel project file (.xlsx)',
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.xlsx,.xls'
        })
    )


class ReportGenerationForm(forms.Form):
    """Form for report generation options"""
    include_charts = forms.BooleanField(
        initial=True,
        required=False,
        label='Include Charts',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    include_tables = forms.BooleanField(
        initial=True,
        required=False,
        label='Include Tables',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    include_grade_distribution = forms.BooleanField(
        initial=True,
        required=False,
        label='Include Grade Distribution',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    report_title = forms.CharField(
        max_length=200,
        initial='Course Assessment Report',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter report title'
        })
    )


class SimpleUserRegistrationForm(UserCreationForm):
    """Simple user registration form"""
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address'
        })
    )
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your first name'
        })
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your last name'
        })
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Choose a username'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirm password'
        })

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
        return user


class SimpleLoginForm(forms.Form):
    """Simple login form using email or username"""
    email_or_username = forms.CharField(
        max_length=254,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email or username'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password'
        })
    )


class GradeCategoryForm(forms.ModelForm):
    """Form for editing grade categories"""
    class Meta:
        from .models import GradeCategory
        model = GradeCategory
        fields = ['grade', 'min_percentage', 'max_percentage', 'order']
        widgets = {
            'grade': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., A, A-, B+'
            }),
            'min_percentage': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'max': '100'
            }),
            'max_percentage': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'max': '100'
            }),
            'order': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            })
        }
