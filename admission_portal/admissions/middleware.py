from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse

class RoleBasedAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        officer_urls = [
            '/officer/',
            '/officer/dashboard/',
            '/officer/applications/',
            '/officer/application/',
            '/officer/courses/',
        ]
        
        admin_urls = [
            '/admin/courses/',
            '/admin/seats/',
        ]
        for url in officer_urls:
            if request.path.startswith(url):
                if not request.user.is_authenticated:
                    messages.warning(request, '⚠️ Please login to access this page.')
                    return redirect('login')
                if not request.user.groups.filter(name='Admission Officers').exists() and not request.user.is_superuser:
                    messages.error(request, '⛔ Access denied. Officer privileges required.')
                    return redirect('home')
                    
        for url in admin_urls:
            if request.path.startswith(url):
                if not request.user.is_authenticated:
                    messages.warning(request, '⚠️ Please login to access this page.')
                    return redirect('login')
                if not request.user.is_superuser:
                    messages.error(request, '⛔ Access denied. Administrator privileges required.')
                    return redirect('home')
        
        response = self.get_response(request)
        return response