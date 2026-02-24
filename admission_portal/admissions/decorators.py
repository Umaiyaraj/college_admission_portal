from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps

def student_required(view_func):
    @wraps(view_func)
    @login_required  
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.groups.filter(name='Students').exists():
            if request.user.groups.filter(name='Admission Officers').exists():
                messages.error(request, '⛔ This page is for students only.')
                return redirect('dashboard_officer')
            else:
                messages.error(request, '⛔ Please register as a student first.')
                return redirect('register')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def officer_required_with_login(view_func):
    @wraps(view_func)
    @login_required  
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.groups.filter(name='Admission Officers').exists():
            if request.user.groups.filter(name='Students').exists():
                messages.error(request, '⛔ Access denied. This page is for officers only.')
                return redirect('dashboard_student')
            else:
                messages.error(request, '⛔ Access denied. Officer privileges required.')
                return redirect('home')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def admin_required_with_login(view_func):
    @wraps(view_func)
    @login_required 
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_superuser:
            messages.error(request, '⛔ Access denied. Administrator privileges required.')
            if request.user.groups.filter(name='Admission Officers').exists():
                return redirect('dashboard_officer')
            elif request.user.groups.filter(name='Students').exists():
                return redirect('dashboard_student')
            else:
                return redirect('home')
        return view_func(request, *args, **kwargs)
    return _wrapped_view