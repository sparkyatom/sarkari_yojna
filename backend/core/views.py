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
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django.utils import timezone
from datetime import timedelta          # FIX: timezone.timedelta doesn't exist
from django.contrib.auth import get_user_model

from schemes.models import Scheme
from schemes.serializers import SchemeListSerializer, SchemeCreateSerializer
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
    permission_classes = [IsAdminUser]

    def get(self, request):
        today = timezone.now().date()
        in_30d = today + timedelta(days=30)

        total_schemes = Scheme.objects.count()
        active_schemes = Scheme.objects.filter(status='active').count()
        expiring = Scheme.objects.filter(last_date__gte=today, last_date__lte=in_30d).count()
        users = User.objects.filter(is_active=True).count()

        return Response({
            'total_schemes': total_schemes,
            'active_schemes': active_schemes,
            'users': users,
            'expiring': expiring,
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
