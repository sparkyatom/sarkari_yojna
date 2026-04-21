"""
schemes/views.py
Public scheme listing + eligible schemes for logged-in users
"""
from datetime import timedelta

from rest_framework import generics, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.db.models import Q, Count
from django.utils import timezone

from .models import Scheme
from .serializers import SchemeListSerializer, SchemeDetailSerializer
from core.matcher import get_eligible_schemes
from users.models import UserSchemeStatus

ACTIVE_SCHEME_CATEGORIES = [
    'agriculture', 'education', 'housing', 'health',
    'women', 'employment', 'social', 'finance'
]


def get_active_non_expired_queryset():
    today = timezone.now().date()
    return Scheme.objects.filter(status='active').exclude(last_date__lt=today)


class SchemeListView(generics.ListAPIView):
    """
    GET /api/schemes/
    Public — returns all active schemes with optional filters.
    Query params: category, caste, state, search, ordering, eligible
    """
    serializer_class    = SchemeListSerializer
    permission_classes  = [AllowAny]
    filter_backends     = [filters.SearchFilter, filters.OrderingFilter]
    search_fields       = ['name', 'description', 'ministry']
    ordering_fields     = ['last_date', 'benefit_amount', 'created_at']
    ordering            = ['last_date']

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def get_queryset(self):
        # Start with active schemes that are not yet expired
        qs = get_active_non_expired_queryset()

        # Eligible filter (requires auth) — only when explicitly requested
        eligible = self.request.query_params.get('eligible')
        if eligible and str(eligible).lower() in ('1', 'true', 'yes'):
            if not self.request.user.is_authenticated:
                return Scheme.objects.none()
            eligible_qs = get_eligible_schemes(self.request.user)
            eligible_ids = [s.id for s in eligible_qs]
            qs = qs.filter(id__in=eligible_ids)

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
            norm = str(state).replace('_', ' ').strip().lower()
            qs = qs.filter(Q(eligible_state='all') | Q(eligible_state__icontains=norm))

        # Income filter
        income = self.request.query_params.get('income')
        if income:
            try:
                max_val = int(income.split('-')[-1]) if '-' in income else int(income)
                qs = qs.filter(Q(max_income__isnull=True) | Q(max_income__gte=max_val))
            except ValueError:
                pass

        # Default ordering: closest deadline first
        return qs.order_by('last_date')


class SchemeDetailView(generics.RetrieveAPIView):
    """GET /api/schemes/{id}/"""
    queryset           = Scheme.objects.filter(status='active')
    serializer_class   = SchemeDetailSerializer
    permission_classes = [AllowAny]


class EligibleSchemesView(APIView):
    """
    GET /api/schemes/eligible/
    Requires authentication — returns schemes matching the user's profile in priority order
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        today = timezone.now().date()
        schemes = get_eligible_schemes(user)
        
        # Categorize for priority sorting
        schemes_list = list(schemes)
        at_risk = [s for s in schemes_list if today <= s.last_date <= today + timedelta(days=10)]
        future = [s for s in schemes_list if s.last_date > today + timedelta(days=10)]
        
        # Return at-risk first, then future
        prioritized = at_risk + future
        
        serializer = SchemeListSerializer(prioritized, many=True, context={'request': request})
        return Response({
            'count': len(prioritized),
            'results': serializer.data,
        })


class ApplySchemeView(APIView):
    """POST /api/schemes/apply/ — mark a scheme applied or un-applied for the current user."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        scheme_id = request.data.get('scheme_id')
        applied = request.data.get('applied')

        if scheme_id is None:
            return Response({'detail': 'scheme_id is required.'}, status=400)

        try:
            scheme = Scheme.objects.get(pk=scheme_id)
        except Scheme.DoesNotExist:
            return Response({'detail': 'Scheme not found.'}, status=404)

        if applied in [True, 'true', 'True', '1', 1]:
            status_obj, _ = UserSchemeStatus.objects.get_or_create(user=request.user, scheme=scheme)
            status_obj.applied = True
            status_obj.applied_date = timezone.now()
            status_obj.save()
            return Response({'scheme_id': scheme.id, 'applied': True})

        UserSchemeStatus.objects.filter(user=request.user, scheme=scheme).delete()
        return Response({'scheme_id': scheme.id, 'applied': False})


class AppliedSchemesView(APIView):
    """GET /api/schemes/applied/ — user applied schemes."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        statuses = UserSchemeStatus.objects.filter(user=request.user, applied=True).select_related('scheme')
        schemes = [status.scheme for status in statuses]
        serializer = SchemeListSerializer(schemes, many=True, context={'request': request})
        return Response({
            'count':   len(schemes),
            'results': serializer.data,
        })


class SchemeCategoriesView(APIView):
    """GET /api/schemes/categorized/ — categorized schemes for the logged-in user with prioritization."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        today = timezone.now().date()
        applied_ids = set(
            UserSchemeStatus.objects.filter(user=user, applied=True).values_list('scheme__id', flat=True)
        )

        # IMPORTANT: Buckets must be user-specific AND consistent with what the UI labels mean.
        # - eligible_now: matched & open (deadline >= today) excluding applied
        # - at_risk: eligible_now where deadline within 10 days
        # - future: schemes within 2 years where user will satisfy age by the scheme deadline
        # - missed: eligible since user signup, deadline passed, not applied

        eligible_all_now = get_eligible_schemes(user, as_of_date=today, include_age=True, include_expired=False)

        # Applied schemes (keep history even if expired/draft)
        applied = Scheme.objects.filter(id__in=applied_ids).order_by('last_date')

        eligible_open = eligible_all_now.exclude(id__in=applied_ids)
        at_risk = eligible_open.filter(last_date__lte=today + timedelta(days=10)).order_by('last_date')

        # Future within 2 years:
        # schemes the user is NOT eligible for today (usually due to age),
        # but will satisfy age by the scheme deadline, while satisfying other constraints.
        future_base = get_eligible_schemes(
            user,
            as_of_date=today,
            include_age=False,   # don't block future due to age today
            include_expired=True,
        ).filter(
            last_date__gt=today + timedelta(days=10),
            last_date__lte=today + timedelta(days=730),
        ).exclude(id__in=applied_ids).exclude(
            id__in=eligible_all_now.values_list('id', flat=True)  # already eligible today
        )

        user_dob = getattr(user, 'date_of_birth', None)
        future_list = []
        if user_dob:
            for s in future_base.iterator():
                if s.min_age is None and s.max_age is None:
                    future_list.append(s)
                    continue
                # compute age on scheme deadline
                d = s.last_date
                age_on_deadline = d.year - user_dob.year - ((d.month, d.day) < (user_dob.month, user_dob.day))
                if (s.min_age is None or age_on_deadline >= s.min_age) and (s.max_age is None or age_on_deadline <= s.max_age):
                    future_list.append(s)
        else:
            future_list = list(future_base)
        future = Scheme.objects.filter(id__in=[s.id for s in future_list]).order_by('last_date')

        # Eligible "now" excluding at-risk bucket (future is disjoint by construction)
        eligible = eligible_open.exclude(id__in=at_risk.values_list('id', flat=True)).order_by('last_date')

        # Missed since signup date (eligible at the time, deadline passed, not applied)
        signup_date = getattr(user, 'date_joined', None)
        signup_day = signup_date.date() if signup_date else None
        missed_qs = get_eligible_schemes(
            user,
            as_of_date=today,
            include_age=False,  # evaluate age at deadline below
            include_expired=True,
        ).filter(last_date__lt=today).exclude(id__in=applied_ids)
        if signup_day:
            missed_qs = missed_qs.filter(last_date__gte=signup_day)
        # Apply age-at-deadline to missed bucket
        missed_list = []
        if user_dob:
            for s in missed_qs.iterator():
                if s.min_age is None and s.max_age is None:
                    missed_list.append(s)
                    continue
                d = s.last_date
                age_on_deadline = d.year - user_dob.year - ((d.month, d.day) < (user_dob.month, user_dob.day))
                if (s.min_age is None or age_on_deadline >= s.min_age) and (s.max_age is None or age_on_deadline <= s.max_age):
                    missed_list.append(s)
        else:
            missed_list = list(missed_qs)
        missed = Scheme.objects.filter(id__in=[s.id for s in missed_list]).order_by('-last_date')

        return Response({
            'applied': {
                'count': applied.count(),
                'results': SchemeListSerializer(applied, many=True, context={'request': request}).data,
            },
            'eligible': {
                'count': eligible.count(),
                'results': SchemeListSerializer(eligible, many=True, context={'request': request}).data,
            },
            'missed': {
                'count': missed.count(),
                'results': SchemeListSerializer(missed, many=True, context={'request': request}).data,
            },
            'at_risk': {
                'count': at_risk.count(),
                'results': SchemeListSerializer(at_risk, many=True, context={'request': request}).data,
            },
            'future': {
                'count': future.count(),
                'results': SchemeListSerializer(future, many=True, context={'request': request}).data,
            },
            'matched_open_total': int(eligible.count() + at_risk.count() + future.count()),
        })


class CategoryCountsView(APIView):
    """GET /api/schemes/category-counts/ — counts per category matching current filters."""
    permission_classes = [AllowAny]

    def get(self, request):
        # Get the filtered queryset using the same logic as SchemeListView
        list_view = SchemeListView()
        list_view.request = request
        qs = list_view.get_queryset()
        
        # Count by category
        counts = qs.values('category').annotate(count=Count('category')).order_by('category')
        raw = {item['category']: item['count'] for item in counts}

        # Always return all supported categories to avoid missing keys in UI.
        category_counts = {cat: int(raw.get(cat, 0)) for cat in ACTIVE_SCHEME_CATEGORIES}
        total = sum(category_counts.values())
        return Response({
            **category_counts,
            'total': total,
            'sum_of_categories': total,
            'is_consistent': True,
        })
