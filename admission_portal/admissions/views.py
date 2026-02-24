from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
# from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.core.paginator import Paginator
# from django.db.models import Q
from django.db.models import F
from .models import Application, Course, SeatAllocation
from .forms import UserRegistrationForm, ApplicationForm, ReviewApplicationForm, CourseSearchForm, ApplicationFilterForm,CourseForm
from .decorators import student_required,officer_required_with_login,admin_required_with_login
from django.utils import timezone
import logging
# from django.contrib.admin.views.decorators import staff_member_required
# from django.contrib.auth.decorators import user_passes_test


logger = logging.getLogger(__name__)


def home(request):
    """Home page view"""
    return render(request, 'admissions/index.html')

def user_login(request):
    """User login view"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            
            # Redirect based on user role
            if user.groups.filter(name='Admission Officers').exists():
                return redirect('dashboard_officer')
            elif user.groups.filter(name='Students').exists():
                return redirect('dashboard_student')
            else:
                return redirect('home')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'admissions/login.html')

def user_logout(request):
    """User logout view"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')

def register(request):
    """User registration view"""
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            from django.contrib.auth.models import Group
            student_group = Group.objects.get(name='Students')
            user.groups.add(student_group)
            
            messages.success(request, 'Registration successful! Please login.')
            return redirect('login')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'admissions/register.html', {'form': form})


@login_required
@student_required
def dashboard_student(request):
    """Student dashboard"""
    student = request.user
    applications = Application.objects.filter(student=student).order_by('-created_at')
    
    # Get statistics
    total_applications = applications.count()
    submitted_applications = applications.filter(status='SUBMITTED').count()
    approved_applications = applications.filter(status='APPROVED').count()
    
    context = {
        'applications': applications[:3],  
        'total_applications': total_applications,
        'submitted_applications': submitted_applications,
        'approved_applications': approved_applications,
    }
    return render(request, 'admissions/dashboard_student.html', context)

@login_required
@student_required
def apply_for_course(request):
    """Apply for a new course"""
    
    MAX_APPLICATIONS = 3
    courses = Course.objects.all()

    if not courses.exists():
        messages.warning(request, '⚠️ No courses are available for application at this time.')

    if request.method == 'POST':
        form = ApplicationForm(request.POST)

        if form.is_valid():
            course = form.cleaned_data['course']

            # ✅ Check 1: Already applied?
            can_apply, message = Application.can_apply(request.user, course)
            if not can_apply:
                messages.error(request, message)
            else:
                # ✅ Check 2: Max applications reached?
                can_create, message = Application.can_create_more(request.user, MAX_APPLICATIONS)
                if not can_create:
                    messages.error(request, message)
                else:
                    # ✅ All validations passed
                    application = form.save(commit=False)
                    application.student = request.user
                    application.status = 'DRAFT'

                    # Eligibility check
                    percentage = form.cleaned_data['percentage_obtained']

                    if percentage >= course.min_percentage:
                        application.is_eligible = True
                        application.eligibility_notes = (
                            f"✅ Eligible: {percentage}% >= {course.min_percentage}%"
                        )
                    else:
                        application.is_eligible = False
                        application.eligibility_notes = (
                            f"❌ Not Eligible: {percentage}% < {course.min_percentage}%"
                        )

                    application.save()

                    messages.success(request, '✅ Application saved successfully!')
                    return redirect('dashboard_student')
        else:
            # 🔥 IMPORTANT: See form errors in terminal
            print("FORM ERRORS:", form.errors)

    else:
        form = ApplicationForm()

    # Active application count
    active_count = 0
    remaining = MAX_APPLICATIONS

    if request.user.is_authenticated:
        active_count = Application.get_active_count(request.user)
        remaining = MAX_APPLICATIONS - active_count

    return render(request, 'admissions/apply.html', {
        'form': form,
        'courses': courses,
        'active_count': active_count,
        'remaining': remaining,
        'max_applications': MAX_APPLICATIONS,
        'total_courses': courses.count(),
    })
@login_required
@student_required
def submit_application(request, application_id):
    """Submit a draft application"""
    application = get_object_or_404(Application, id=application_id, student=request.user)
    
    if application.status == 'DRAFT':
        application.status = 'SUBMITTED'
        application.submission_date = timezone.now()
        application.save()
        messages.success(request, 'Application submitted successfully!')
    else:
        messages.warning(request, 'Application has already been submitted.')
    
    return redirect('dashboard_student')

# Officer Views
@login_required
@officer_required_with_login
def dashboard_officer(request):
    """Admission officer dashboard"""
    # Get statistics
    total_applications = Application.objects.count()
    pending_review = Application.objects.filter(status='SUBMITTED').count()
    approved_applications = Application.objects.filter(status='APPROVED').count()
    total_courses = Course.objects.count()
    
    # Get recent applications
    recent_applications = Application.objects.filter(status='SUBMITTED').order_by('-submission_date')[:5]
    
    # Get courses with low seat availability
    low_seat_courses = Course.objects.filter(filled_seats__gte=F('total_seats') * 4/5)[:5]
    
    context = {
        'total_applications': total_applications,
        'pending_review': pending_review,
        'approved_applications': approved_applications,
        'total_courses': total_courses,
        'recent_applications': recent_applications,
        'low_seat_courses': low_seat_courses,
    }
    return render(request, 'admissions/dashboard_officer.html', context)

@login_required
@officer_required_with_login
def manage_applications(request):
    """View and filter applications - PENDING FIRST!"""
    
    # Start with ONLY unreviewed applications
    applications = Application.objects.filter(
        status__in=['DRAFT', 'SUBMITTED', 'UNDER_REVIEW']
    )
    
    # Check if user wants to see all
    show_all = request.GET.get('show_all', 'false')
    if show_all == 'true':
        applications = Application.objects.all()
    
    # Apply status filter if specified
    status_filter = request.GET.get('status')
    if status_filter:
        applications = applications.filter(status=status_filter)
    
    # Apply course filter
    course_filter = request.GET.get('course')
    if course_filter:
        applications = applications.filter(course_id=course_filter)
    
    # Apply date filters
    date_from = request.GET.get('date_from')
    if date_from:
        applications = applications.filter(submission_date__date__gte=date_from)
    
    date_to = request.GET.get('date_to')
    if date_to:
        applications = applications.filter(submission_date__date__lte=date_to)
    
    # Order by submission date (newest first)
    applications = applications.order_by('-submission_date', '-created_at')
    
    # Pagination
    paginator = Paginator(applications, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get counts for badges
    pending_count = Application.objects.filter(
        status__in=['DRAFT', 'SUBMITTED', 'UNDER_REVIEW']
    ).count()
    
    approved_count = Application.objects.filter(status='APPROVED').count()
    rejected_count = Application.objects.filter(status='REJECTED').count()
    total_count = Application.objects.count()
    
    # Get all courses for filter dropdown
    all_courses = Course.objects.all()
    
    return render(request, 'admissions/applications.html', {
        'page_obj': page_obj,
        'form': ApplicationFilterForm(request.GET or None),
        'all_courses': all_courses,
        'pending_count': pending_count,
        'approved_count': approved_count,
        'rejected_count': rejected_count,
        'total_count': total_count,
        'show_all': show_all == 'true',
        'current_status': status_filter,
    })
@login_required
@officer_required_with_login
def review_application(request, application_id):
    """Review a specific application"""
    application = get_object_or_404(Application, id=application_id)
    
    if request.method == 'POST':
        form = ReviewApplicationForm(request.POST, instance=application)
        action = request.POST.get('action', 'save')  # ✅ GET THE BUTTON ACTION!
        
        if form.is_valid():
            reviewed_application = form.save(commit=False)
            reviewed_application.reviewed_by = request.user
            reviewed_application.review_date = timezone.now()
            
            # ✅ HANDLE DIFFERENT ACTIONS!
            if action == 'approve_and_allocate':
                reviewed_application.status = 'APPROVED'
                reviewed_application.save()
                
                # Check seat availability
                course = reviewed_application.course
                if course.available_seats > 0:
                    # Create seat allocation
                    SeatAllocation.objects.create(
                        application=reviewed_application,
                        course=course,
                        allocated_by=request.user,
                        confirmation_deadline=timezone.now().date() + timezone.timedelta(days=14)
                    )
                    # ✅ REDUCE SEAT COUNT!
                    course.filled_seats += 1
                    course.save()
                    messages.success(request, f'✅ Application approved and seat allocated! {course.available_seats} seats remaining.')
                else:
                    messages.warning(request, '⚠️ Application approved but NO SEATS AVAILABLE. Student added to waitlist.')
                    
            elif action == 'approve_only':
                reviewed_application.status = 'APPROVED'
                reviewed_application.save()
                messages.success(request, '✅ Application approved. No seat allocated.')
                
            elif action == 'reject':
                reviewed_application.status = 'REJECTED'
                reviewed_application.save()
                messages.success(request, '❌ Application rejected.')
                
            else:  # 'save' - just save review
                reviewed_application.save()
                messages.success(request, '✅ Review saved successfully.')
            
            return redirect('manage_applications')
    else:
        form = ReviewApplicationForm(instance=application)
    
    # Get status choices for the template
    status_choices = Application.APPLICATION_STATUS
    
    return render(request, 'admissions/application_detail.html', {
        'application': application,
        'form': form,
        'status_choices': status_choices,
    })
@login_required
@admin_required_with_login  # 👈 CHANGED FROM officer_required TO admin_required!
def manage_courses(request):
    """View and search courses - ADMIN ONLY"""
    courses = Course.objects.all().order_by('code')
    form = CourseSearchForm(request.GET or None)
    
    # Apply search filters
    if form.is_valid():
        name = form.cleaned_data.get('name')
        department = form.cleaned_data.get('department')
        course_type = form.cleaned_data.get('course_type')
        
        if name:
            courses = courses.filter(name__icontains=name)
        if department:
            courses = courses.filter(department__icontains=department)
        if course_type:
            courses = courses.filter(course_type=course_type)
    
    # Pagination
    paginator = Paginator(courses, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'admissions/manage_courses.html', {
        'page_obj': page_obj,
        'form': form,
        'total_count': courses.count(),
    })
@login_required
@admin_required_with_login  # 👈 CHANGED FROM officer_required TO admin_required!
def manage_seats(request):
    """Manage seat allocations - ADMIN ONLY"""
    seat_allocations = SeatAllocation.objects.select_related('application', 'course').order_by('-allocation_date')
    
    # Get seat statistics
    total_seats = sum(course.total_seats for course in Course.objects.all())
    filled_seats = sum(course.filled_seats for course in Course.objects.all())
    
    # Get courses with seat information
    courses = Course.objects.all().order_by('department')
    
    context = {
        'seat_allocations': seat_allocations[:10],
        'courses': courses,
        'total_seats': total_seats,
        'filled_seats': filled_seats,
        'available_seats': total_seats - filled_seats,
    }
    return render(request, 'admissions/manage_seats.html', context)
# Public Views
def view_courses(request):
    """Public view of available courses"""
    courses = Course.objects.all().order_by('department', 'code')
    form = CourseSearchForm(request.GET or None)
    
    # Apply search filters
    if form.is_valid():
        name = form.cleaned_data.get('name')
        department = form.cleaned_data.get('department')
        course_type = form.cleaned_data.get('course_type')
        
        if name:
            courses = courses.filter(name__icontains=name)
        if department:
            courses = courses.filter(department__icontains=department)
        if course_type:
            courses = courses.filter(course_type=course_type)
    
    # Pagination
    paginator = Paginator(courses, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'admissions/courses_public.html', {
        'page_obj': page_obj,
        'form': form,
    })

def allocate_seat(request, application):
    # Check if student already has a seat
    has_seat = SeatAllocation.objects.filter(
        application__student=application.student
    ).exists()
    
    if has_seat:
        messages.error(request, 'Student already has an allocated seat!')
        return False

@login_required
@officer_required_with_login
def view_courses_officer(request):

    if not request.user.is_authenticated:
        return redirect('login')
    """View-only courses for officers - NO EDIT/DELETE"""
    courses = Course.objects.all().order_by('department', 'code')
    form = CourseSearchForm(request.GET or None)
    
    # Apply search filters
    if form.is_valid():
        name = form.cleaned_data.get('name')
        department = form.cleaned_data.get('department')
        course_type = form.cleaned_data.get('course_type')
        
        if name:
            courses = courses.filter(name__icontains=name)
        if department:
            courses = courses.filter(department__icontains=department)
        if course_type:
            courses = courses.filter(course_type=course_type)
    
    # Pagination
    paginator = Paginator(courses, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'admissions/courses_viewonly.html', {
        'page_obj': page_obj,
        'form': form,
        'total_count': courses.count(),
    })

@login_required
@admin_required_with_login
def add_course(request):
    """Add a new course - ADMIN ONLY"""
    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            course = form.save()
            messages.success(request, f'✅ Course {course.code} created successfully!')
            return redirect('manage_courses')
    else:
        form = CourseForm()
    
    return render(request, 'admissions/course_form.html', {
        'form': form,
        'title': 'Add New Course'
    })

@login_required
@admin_required_with_login
def edit_course(request, course_id):
    """Edit an existing course - ADMIN ONLY"""
    course = get_object_or_404(Course, id=course_id)
    
    if request.method == 'POST':
        form = CourseForm(request.POST, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, f'✅ Course {course.code} updated successfully!')
            return redirect('manage_courses')
    else:
        form = CourseForm(instance=course)
    
    return render(request, 'admissions/course_form.html', {
        'form': form,
        'course': course,
        'title': f'Edit Course: {course.code}'
    })

@login_required
@ admin_required_with_login
def delete_course(request, course_id):
    """Delete a course - ADMIN ONLY"""
    course = get_object_or_404(Course, id=course_id)
    
    if request.method == 'POST':
        course_code = course.code
        course.delete()
        messages.success(request, f'✅ Course {course_code} deleted successfully!')
        return redirect('manage_courses')
    
    return render(request, 'admissions/course_confirm_delete.html', {
        'course': course
    })