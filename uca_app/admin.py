from django.contrib import admin
from .models import Course, CourseConfiguration, Section, Assessment, GradeDistribution, CourseReport, ProjectFile


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'term_semester', 'coordinator', 'created_at']
    list_filter = ['term_semester', 'created_at']
    search_fields = ['name', 'code', 'coordinator']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']


@admin.register(CourseConfiguration)
class CourseConfigurationAdmin(admin.ModelAdmin):
    list_display = ['course', 'num_sections', 'num_quizzes', 'num_assignments', 'get_total_weight']
    list_filter = ['num_sections', 'num_quizzes', 'num_assignments']
    readonly_fields = ['get_total_weight']
    
    def get_total_weight(self, obj):
        return f"{obj.get_total_weight():.2f}%"
    get_total_weight.short_description = 'Total Weight'


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ['course', 'section_number', 'instructor', 'total_students']
    list_filter = ['course', 'section_number']
    search_fields = ['instructor', 'course__name']
    ordering = ['course', 'section_number']


@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = ['section', 'assessment_type', 'assessment_number', 'max_marks', 'average_marks', 'get_percentage']
    list_filter = ['assessment_type', 'section__course']
    search_fields = ['section__instructor', 'section__course__name']
    readonly_fields = ['get_percentage']
    
    def get_percentage(self, obj):
        return f"{obj.get_percentage():.1f}%"
    get_percentage.short_description = 'Percentage'


@admin.register(GradeDistribution)
class GradeDistributionAdmin(admin.ModelAdmin):
    list_display = ['course', 'section', 'grade', 'count']
    list_filter = ['grade', 'course', 'section']
    search_fields = ['section__instructor', 'course__name']


@admin.register(CourseReport)
class CourseReportAdmin(admin.ModelAdmin):
    list_display = ['course', 'title', 'generated_at']
    list_filter = ['generated_at']
    search_fields = ['course__name', 'title']
    readonly_fields = ['generated_at']
    ordering = ['-generated_at']


@admin.register(ProjectFile)
class ProjectFileAdmin(admin.ModelAdmin):
    list_display = ['course', 'file', 'uploaded_at']
    list_filter = ['uploaded_at']
    search_fields = ['course__name']
    readonly_fields = ['uploaded_at']
    ordering = ['-uploaded_at']
