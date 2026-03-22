"""
schemes/views.py
Public scheme listing + eligible schemes for logged-in users
"""
from rest_framework import generics, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.db.models import Q
from django.utils import timezone

from .models import Scheme
from .serializers import SchemeListSerializer, SchemeDetailSerializer
from core.matcher import get_eligible_schemes


class SchemeListView(generics.ListAPIView):
    """
    GET /api/schemes/
    Public — returns all active schemes with optional filters.
    Query params: category, caste, state, search, ordering
    """
    serializer_class    = SchemeListSerializer
    permission_classes  = [AllowAny]
    filter_backends     = [filters.SearchFilter, filters.OrderingFilter]
    search_fields       = ['name', 'description', 'ministry']
    ordering_fields     = ['last_date', 'benefit_amount', 'created_at']
    ordering            = ['last_date']

    def get_queryset(self):
        qs = Scheme.objects.filter(status='active')

        # Category filter
        category = self.request.query_params.get('category')
        if category:
            qs = qs.filter(category=category)

        # Caste filter
        caste = self.request.query_params.get('caste')
        if caste:
            qs = qs.filter(
                Q(eligible_category='all') | Q(eligible_category__icontains=caste)
            )

        # State filter
        state = self.request.query_params.get('state')
        if state:
            qs = qs.filter(Q(eligible_state='all') | Q(eligible_state=state))

        # Income filter
        income = self.request.query_params.get('income')
        if income:
            try:
                max_val = int(income.split('-')[-1]) if '-' in income else int(income)
                qs = qs.filter(Q(max_income__isnull=True) | Q(max_income__gte=max_val))
            except ValueError:
                pass

        return qs


class SchemeDetailView(generics.RetrieveAPIView):
    """GET /api/schemes/{id}/"""
    queryset           = Scheme.objects.filter(status='active')
    serializer_class   = SchemeDetailSerializer
    permission_classes = [AllowAny]


class EligibleSchemesView(APIView):
    """
    GET /api/schemes/eligible/
    Requires authentication — returns schemes matching the user's profile
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user    = request.user
        schemes = get_eligible_schemes(user)
        serializer = SchemeListSerializer(schemes, many=True)
        return Response({
            'count':   len(schemes),
            'results': serializer.data,
        })
