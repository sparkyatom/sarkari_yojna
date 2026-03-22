"""
users/views.py
Auth views: register, login, logout, profile
"""
from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.contrib.auth import authenticate, get_user_model

from .serializers import RegisterSerializer, UserSummarySerializer, ProfileSerializer

User = get_user_model()


class RegisterView(APIView):
    permission_classes = [AllowAny]
    # FIX: Accept both JSON (no profile pic) and multipart (with profile pic)
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(
                {'message': 'Account created successfully', 'username': user.username},
                status=status.HTTP_201_CREATED
            )
        # FIX: Return a flat, human-readable error message so the frontend
        # catch block (Object.values(err)[0]?.[0]) always gets a clear string.
        errors = serializer.errors
        # Flatten nested error dict into the first meaningful message
        first_field = next(iter(errors))
        first_msg = errors[first_field]
        if isinstance(first_msg, list):
            first_msg = first_msg[0]
        if isinstance(first_msg, dict):
            first_msg = next(iter(first_msg.values()))[0]
        return Response(
            {first_field: [str(first_msg)]},
            status=status.HTTP_400_BAD_REQUEST
        )


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username', '').strip()
        password = request.data.get('password', '')

        if not username or not password:
            return Response({'detail': 'Username and password are required.'}, status=400)

        user = authenticate(request, username=username, password=password)
        if not user:
            return Response({'detail': 'Invalid username or password.'}, status=401)

        if not user.is_active:
            return Response({'detail': 'Account is inactive.'}, status=403)

        refresh = RefreshToken.for_user(user)
        return Response({
            'access':  str(refresh.access_token),
            'refresh': str(refresh),
            'user':    UserSummarySerializer(user).data,
        })


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError:
            pass
        return Response({'message': 'Logged out successfully.'})


class ProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class   = ProfileSerializer
    # FIX: support multipart for profile picture updates
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_object(self):
        return self.request.user
