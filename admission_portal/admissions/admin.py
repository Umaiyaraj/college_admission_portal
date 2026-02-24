from django.contrib import admin
from .models import Course, Application, SeatAllocation

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'department', 'course_type', 'total_seats', 'filled_seats', 'available_seats', 'min_percentage')
    list_filter = ('department', 'course_type')
    search_fields = ('code', 'name', 'department')
    readonly_fields = ('filled_seats',)

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('application_number', 'student', 'course', 'status', 'is_eligible', 'submission_date')
    list_filter = ('status', 'is_eligible', 'course', 'submission_date')
    search_fields = ('application_number', 'student__username', 'student__email')
    readonly_fields = ('application_number', 'created_at', 'last_updated')
    date_hierarchy = 'submission_date'
