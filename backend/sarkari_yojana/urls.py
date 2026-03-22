"""
SarkariYojana — Main URL Configuration
All API routes under /api/
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('django-admin/', admin.site.urls),     # Django built-in admin
    path('api/auth/',    include('users.urls')),
    path('api/schemes/', include('schemes.urls')),
    path('api/admin/',   include('core.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
