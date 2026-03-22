"""core/urls.py — Admin API routes (all under /api/admin/)"""
from django.urls import path
from .views import (
    AdminStatsView,
    AdminSchemeListCreateView,
    AdminSchemeDetailView,
    ExcelUploadView,
    AdminUsersView,
    UploadHistoryView,
)

urlpatterns = [
    path('stats/',              AdminStatsView.as_view(),            name='admin-stats'),
    path('schemes/',            AdminSchemeListCreateView.as_view(),  name='admin-schemes'),
    path('schemes/<int:pk>/',   AdminSchemeDetailView.as_view(),      name='admin-scheme-detail'),
    path('upload/excel/',       ExcelUploadView.as_view(),            name='admin-upload-excel'),
    path('users/',              AdminUsersView.as_view(),             name='admin-users'),
    path('uploads/',            UploadHistoryView.as_view(),          name='admin-uploads'),
]
