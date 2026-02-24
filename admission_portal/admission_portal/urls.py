from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('backstage/', admin.site.urls), 
    path('', include('admissions.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

admin.site.site_header = "College Admission Portal Admin"
admin.site.site_title = "Admission Portal Admin"
admin.site.index_title = "Welcome to Administration"