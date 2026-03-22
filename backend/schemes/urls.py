"""schemes/urls.py"""
from django.urls import path
from .views import SchemeListView, SchemeDetailView, EligibleSchemesView

urlpatterns = [
    path('',            SchemeListView.as_view(),     name='scheme-list'),
    path('eligible/',   EligibleSchemesView.as_view(), name='eligible-schemes'),
    path('<int:pk>/',   SchemeDetailView.as_view(),   name='scheme-detail'),
]
