"""schemes/urls.py"""
from django.urls import path
from .views import (
    SchemeListView,
    SchemeDetailView,
    EligibleSchemesView,
    ApplySchemeView,
    AppliedSchemesView,
    SchemeCategoriesView,
    CategoryCountsView,
)

urlpatterns = [
    path('',            SchemeListView.as_view(),        name='scheme-list'),
    path('eligible/',   EligibleSchemesView.as_view(),   name='eligible-schemes'),
    path('apply/',      ApplySchemeView.as_view(),      name='apply-scheme'),
    path('applied/',    AppliedSchemesView.as_view(),    name='applied-schemes'),
    path('categorized/', SchemeCategoriesView.as_view(), name='scheme-categories'),
    path('category-counts/', CategoryCountsView.as_view(), name='category-counts'),
    path('<int:pk>/',   SchemeDetailView.as_view(),      name='scheme-detail'),
]
