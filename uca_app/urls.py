from django.urls import path
from . import views

app_name = 'uca_app'

urlpatterns = [
    # Main pages
    path('', views.index, name='index'),
    path('courses/', views.course_list, name='course_list'),
    
    # Simple Authentication
    path('register/', views.simple_register, name='simple_register'),
    path('login/', views.simple_login, name='simple_login'),
    path('logout/', views.simple_logout, name='simple_logout'),
    
    # Course management
    path('course/create/', views.course_create, name='course_create'),
    path('course/<int:course_id>/', views.course_detail, name='course_detail'),
    path('course/<int:course_id>/edit/', views.course_edit, name='course_edit'),
    path('course/<int:course_id>/delete/', views.course_delete, name='course_delete'),
    
    # Course workflow
    path('course/<int:course_id>/sections/', views.course_sections, name='course_sections'),
    path('course/<int:course_id>/sections/edit/', views.edit_sections, name='edit_sections'),
    path('course/<int:course_id>/assessments/', views.course_assessments, name='course_assessments'),
    path('course/<int:course_id>/analysis/', views.course_analysis, name='course_analysis'),
    path('course/<int:course_id>/grades/', views.grade_distribution, name='grade_distribution'),
    path('course/<int:course_id>/grades/edit-categories/', views.edit_grade_categories, name='edit_grade_categories'),
    path('course/<int:course_id>/report/', views.course_report, name='course_report'),
    
    # Reports and downloads
    path('report/<int:report_id>/download/', views.download_report, name='download_report'),
    
    # API endpoints
    path('api/save-grade-distribution/', views.api_save_grade_distribution, name='api_save_grade_distribution'),
    
    # Project import/export
    path('project/import/', views.project_import, name='project_import'),
    path('course/<int:course_id>/export/', views.project_export, name='project_export'),
    
    # API endpoints
    path('api/calculate-stats/', views.api_calculate_stats, name='api_calculate_stats'),
    
]
