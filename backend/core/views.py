"""
core/views.py
Admin-only API views:
  - Dashboard stats
  - CRUD for schemes
  - Excel/CSV upload
  - User listing
  - Upload history
"""
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework import status, filters
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser
from django.http import HttpResponse
from django.utils import timezone
from django.db.models import Count
from datetime import timedelta          # FIX: timezone.timedelta doesn't exist
from django.contrib.auth import get_user_model
import csv
import json

from schemes.models import Scheme
from schemes.serializers import SchemeListSerializer, SchemeCreateSerializer
from schemes.views import get_active_non_expired_queryset, ACTIVE_SCHEME_CATEGORIES
from users.serializers import ProfileSerializer
from .excel_importer import import_from_excel, import_from_csv
from .models import UploadHistory

User = get_user_model()


class IsAdminUser(IsAuthenticated):
    """Custom permission: must be logged in AND is_admin=True"""
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.is_admin


# ─────────────────────────────────────────
# STATS
# ─────────────────────────────────────────
class AdminStatsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        today    = timezone.now().date()
        in_30d   = today + timedelta(days=30)   # FIX: was timezone.timedelta (doesn't exist)
        active_qs = get_active_non_expired_queryset()
        total    = active_qs.count()
        expiring = active_qs.filter(last_date__range=[today, in_30d]).count()
        users    = User.objects.filter(is_active=True).count()
        category_rows = active_qs.values('category').annotate(count=Count('category'))
        category_counts = {cat: 0 for cat in ACTIVE_SCHEME_CATEGORIES}
        for row in category_rows:
            category = row['category']
            if category in category_counts:
                category_counts[category] = row['count']
        sum_of_categories = sum(category_counts.values())

        return Response({
            'total_schemes': total,
            'active':        total,
            'expiring':      expiring,
            'users':         users,
            'states':        36,
            'matches':       total * users,
            'category_counts': category_counts,
            'sum_of_categories': sum_of_categories,
            'counts_consistent': sum_of_categories == total,
            'active_definition': "status == 'active' and last_date >= today",
        })


# ─────────────────────────────────────────
# SCHEME CRUD (Admin)
# ─────────────────────────────────────────
class AdminSchemeListCreateView(APIView):
    permission_classes = [IsAdminUser]

    # def get(self, request):
    #     qs = Scheme.objects.all()
    #     category = request.query_params.get('category')
    #     if category:
    #         qs = qs.filter(category=category)
    #     search = request.query_params.get('search')
    #     if search:
    #         qs = qs.filter(name__icontains=search)
    #     qs = qs.order_by('last_date')
    #     serializer = SchemeListSerializer(qs, many=True)
    #     return Response({'count': qs.count(), 'results': serializer.data})
    

    def get(self, request):

      qs = Scheme.objects.all()

      category = request.query_params.get('category')
      if category is not None:
        qs = qs.filter(category=category)

      search = request.query_params.get('search')
      if search is not None:
        qs = qs.filter(name__icontains=search)

      qs = qs.order_by('last_date')

      serializer = SchemeListSerializer(qs, many=True)

      return Response({
        'count': qs.count(),
        'results': serializer.data
      })

    def post(self, request):
        serializer = SchemeCreateSerializer(data=request.data)
        if serializer.is_valid():
            scheme = serializer.save()
            return Response(SchemeListSerializer(scheme).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AdminSchemeDetailView(APIView):
    permission_classes = [IsAdminUser]

    def _get_scheme(self, pk):
        try:
            return Scheme.objects.get(pk=pk)
        except Scheme.DoesNotExist:
            return None

    def get(self, request, pk):
        scheme = self._get_scheme(pk)
        if not scheme:
            return Response({'detail': 'Not found'}, status=404)
        return Response(SchemeListSerializer(scheme).data)

    def put(self, request, pk):
        scheme = self._get_scheme(pk)
        if not scheme:
            return Response({'detail': 'Not found'}, status=404)
        serializer = SchemeCreateSerializer(scheme, data=request.data, partial=True)
        if serializer.is_valid():
            updated = serializer.save()
            return Response(SchemeListSerializer(updated).data)
        return Response(serializer.errors, status=400)

    def delete(self, request, pk):
        scheme = self._get_scheme(pk)
        if not scheme:
            return Response({'detail': 'Not found'}, status=404)
        scheme.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ─────────────────────────────────────────
# EXCEL / CSV UPLOAD
# ─────────────────────────────────────────
class ExcelUploadView(APIView):
    permission_classes = [IsAdminUser]
    parser_classes     = [MultiPartParser, FormParser]

    def post(self, request):
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response({'detail': 'No file provided.'}, status=400)

        filename = file_obj.name.lower()
        try:
            if filename.endswith('.csv'):
                result = import_from_csv(file_obj)
            elif filename.endswith(('.xlsx', '.xls')):
                result = import_from_excel(file_obj)
            else:
                return Response({'detail': 'Only .xlsx, .xls, .csv files are supported.'}, status=400)
        except Exception as e:
            return Response({'detail': f'Parse error: {str(e)}'}, status=400)

        UploadHistory.objects.create(
            filename        = file_obj.name,
            file_type       = 'csv' if filename.endswith('.csv') else 'excel',
            schemes_created = result['created'],
            schemes_skipped = result['skipped'],
            uploaded_by     = request.user,
            success         = len(result['errors']) == 0,
        )

        status_code = status.HTTP_200_OK
        if result['created'] == 0 and result['errors']:
            status_code = status.HTTP_400_BAD_REQUEST

        response_data = {
            'message': f"Import complete: {result['created']} created, {result['skipped']} skipped.",
            'created': result['created'],
            'skipped': result['skipped'],
            'errors':  result['errors'],
        }
        if status_code != status.HTTP_200_OK:
            response_data['detail'] = 'Upload failed. See errors for details.'

        return Response(response_data, status=status_code)


class JsonUploadView(APIView):
    permission_classes = [IsAdminUser]
    parser_classes     = [MultiPartParser, FormParser]

    def post(self, request):
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response({'detail': 'No file provided.'}, status=400)

        if not file_obj.name.lower().endswith('.json'):
            return Response({'detail': 'Only .json files are supported on this endpoint.'}, status=400)

        try:
            payload = json.loads(file_obj.read().decode('utf-8'))
        except Exception:
            return Response({'detail': 'Invalid JSON file.'}, status=400)

        if not isinstance(payload, list):
            return Response({'detail': 'JSON must be an array of scheme objects.'}, status=400)

        created = 0
        skipped = 0
        errors = []
        for idx, raw in enumerate(payload, start=1):
            if not isinstance(raw, dict):
                skipped += 1
                errors.append(f'Row {idx}: entry must be an object')
                continue

            normalized = {
                'name': raw.get('name') or raw.get('scheme_name'),
                'ministry': raw.get('ministry') or 'Ministry',
                'category': raw.get('category'),
                'description': raw.get('description') or '',
                'eligible_category': raw.get('eligible_category', 'all'),
                'eligible_occupation': raw.get('eligible_occupation', 'all'),
                'eligible_gender': raw.get('eligible_gender', 'all'),
                'eligible_state': raw.get('eligible_state', 'all'),
                'min_income': raw.get('min_income', 0),
                'max_income': raw.get('max_income'),
                'benefit_amount': raw.get('benefit_amount', 0),
                'benefit_period': raw.get('benefit_period', 'per_year'),
                'last_date': raw.get('last_date'),
                'official_url': raw.get('official_url'),
                'status': raw.get('status', 'active'),
                'required_documents': raw.get('required_documents', []),
            }
            if isinstance(normalized['required_documents'], str):
                normalized['required_documents'] = [d.strip() for d in normalized['required_documents'].split(';') if d.strip()]

            serializer = SchemeCreateSerializer(data=normalized)
            if serializer.is_valid():
                serializer.save()
                created += 1
            else:
                skipped += 1
                errors.append(f'Row {idx}: {serializer.errors}')

        UploadHistory.objects.create(
            filename=file_obj.name,
            file_type='json',
            schemes_created=created,
            schemes_skipped=skipped,
            uploaded_by=request.user,
            success=len(errors) == 0,
        )

        status_code = status.HTTP_200_OK if created > 0 else status.HTTP_400_BAD_REQUEST
        return Response({
            'message': f'Import complete: {created} created, {skipped} skipped.',
            'created': created,
            'skipped': skipped,
            'errors': errors,
        }, status=status_code)


# ─────────────────────────────────────────
# USERS (Admin)
# ─────────────────────────────────────────
class AdminUsersView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        qs     = User.objects.filter(is_active=True).order_by('-date_joined')
        search = request.query_params.get('search')
        if search:
            qs = qs.filter(full_name__icontains=search)
        serializer = ProfileSerializer(qs, many=True)
        return Response({'count': qs.count(), 'results': serializer.data})


# ─────────────────────────────────────────
# UPLOAD HISTORY
# ─────────────────────────────────────────
class UploadHistoryView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        qs   = UploadHistory.objects.order_by('-uploaded_at')[:20]
        data = [{
            'id':              h.id,
            'filename':        h.filename,
            'file_type':       h.file_type,
            'schemes_created': h.schemes_created,
            'schemes_skipped': h.schemes_skipped,
            'uploaded_at':     h.uploaded_at.strftime('%d %b %Y'),
            'uploaded_by':     h.uploaded_by.username if h.uploaded_by else 'Unknown',
            'success':         h.success,
        } for h in qs]
        return Response(data)


class ExcelTemplateDownloadView(APIView):
    """GET /api/admin/template/excel/ — download a CSV template for bulk uploads."""
    permission_classes = [IsAdminUser]

    def get(self, request):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="scheme_import_template.csv"'
        writer = csv.writer(response)
        writer.writerow([
            'scheme_name', 'category', 'ministry', 'description',
            'eligible_category', 'eligible_occupation', 'eligible_gender', 'eligible_state',
            'min_income', 'max_income',
            'benefit_amount', 'benefit_period',
            'last_date', 'required_documents', 'official_url', 'status'
        ])
        writer.writerow([
            'Sample Agriculture Support',
            'agriculture',
            'Ministry of Agriculture',
            'Support for farmers',
            'all',
            'farmer',
            'all',
            'all',
            '0',
            '300000',
            '6000',
            'per_year',
            timezone.now().date().isoformat(),
            'Aadhaar Card;Income Certificate',
            'https://example.gov.in/scheme',
            'active',
        ])
        return response
