from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('register/', views.register, name='register'),
    path('courses/', views.view_courses, name='view_courses'),
    
    
    path('student/dashboard/', views.dashboard_student, name='dashboard_student'),
    path('student/apply/', views.apply_for_course, name='apply_for_course'),
    path('student/application/<int:application_id>/submit/', views.submit_application, name='submit_application'),
    
    path('officer/dashboard/', views.dashboard_officer, name='dashboard_officer'),
    path('officer/applications/', views.manage_applications, name='manage_applications'),
    path('officer/application/<int:application_id>/review/', views.review_application, name='review_application'),
    path('officer/courses/', views.view_courses_officer, name='officer_view_courses'),
    
    path('administration/courses/', views.manage_courses, name='manage_courses'),
    path('administration/courses/add/', views.add_course, name='add_course'),
    path('administration/courses/<int:course_id>/edit/', views.edit_course, name='edit_course'),
    path('administration/courses/<int:course_id>/delete/', views.delete_course, name='delete_course'),
    path('administration/seats/', views.manage_seats, name='manage_seats'),
]