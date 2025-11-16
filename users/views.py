from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from .models import User
from .serializers import UserSerializer, RegisterSerializer, UserProfileUpdateSerializer
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.decorators import api_view, permission_classes
from rest_framework.parsers import MultiPartParser, FormParser
from django.conf import settings
from django.core.files.storage import default_storage
from .country_codes import get_all_country_codes, COUNTRY_CODES
import requests
import os
import uuid
import logging

logger = logging.getLogger(__name__)

GOOGLE_CLIENT_ID = "971707519453-srarmkadprdmpgv385312cgfckok9eku.apps.googleusercontent.com"

@swagger_auto_schema(
    method='get',
    operation_summary="Validate JWT token",
    tags=['Users & Authentication'],
    security=[{'Bearer': []}],
    responses={200: 'Token is valid', 401: 'Token is invalid'}
)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def validate_token(request):
    """
    Simple endpoint to validate if the access token is still valid.
    Returns 200 if valid, 401 if invalid (handled by permission_classes).
    """
    return Response({
        "valid": True,
        "user_id": request.user.id,
        "email": request.user.email
    }, status=status.HTTP_200_OK)

@swagger_auto_schema(
    method='get',
    operation_summary="Get country codes",
    tags=['Users & Authentication'],
    responses={200: 'List of country codes'}
)
@api_view(['GET'])
@permission_classes([AllowAny])
def get_country_codes(request):
    """
    Get list of available country codes for phone number validation
    """
    try:
        # Return simplified country codes list
        country_list = []
        for code, info in COUNTRY_CODES.items():
            country_list.append({
                'code': code,
                'name': info['name'],
                'dial_code': info['dial_code']
            })
        
        # Sort by country name
        country_list.sort(key=lambda x: x['name'])
        
        return Response({
            'countries': country_list,
            'total': len(country_list)
        }, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Error getting country codes: {str(e)}")
        return Response({
            'error': 'Failed to get country codes'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class RegisterView(generics.CreateAPIView):
    """
    Register a new user account.
    Returns JWT tokens upon successful registration.
    """
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer
    
    @swagger_auto_schema(
        operation_summary="Register new user",
        tags=['Users & Authentication'],
        request_body=RegisterSerializer,
        responses={
            201: openapi.Response('User registered successfully', schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'user': openapi.Schema(type=openapi.TYPE_OBJECT),
                    'refresh': openapi.Schema(type=openapi.TYPE_STRING),
                    'access': openapi.Schema(type=openapi.TYPE_STRING),
                    'message': openapi.Schema(type=openapi.TYPE_STRING),
                }
            ))
        }
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Automatically log in the user and return JWT tokens
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'message': 'User registered successfully'
        }, status=status.HTTP_201_CREATED)

class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    Get or update user profile.
    - **GET**: Get current user profile
    - **PUT/PATCH**: Update user profile
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def get_serializer_class(self):
        if self.request.method == 'PUT':
            return UserProfileUpdateSerializer
        return UserSerializer
    
    @swagger_auto_schema(
        operation_summary="Get my profile",
        tags=['Users & Authentication'],
        security=[{'Bearer': []}],
        responses={200: UserSerializer}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="Update my profile",
        tags=['Users & Authentication'],
        security=[{'Bearer': []}],
        request_body=UserProfileUpdateSerializer,
        responses={200: UserSerializer}
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

class GoogleLoginView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        id_token = request.data.get('id_token')
        if not id_token:
            return Response({'detail': 'No ID token provided.'}, status=status.HTTP_400_BAD_REQUEST)

        # Verify the token with Google
        google_url = f"https://oauth2.googleapis.com/tokeninfo?id_token={id_token}"
        resp = requests.get(google_url)
        if resp.status_code != 200:
            return Response({'detail': 'Invalid Google token.'}, status=status.HTTP_400_BAD_REQUEST)
        data = resp.json()
        if data.get('aud') != GOOGLE_CLIENT_ID:
            return Response({'detail': 'Invalid audience.'}, status=status.HTTP_400_BAD_REQUEST)
        email = data.get('email')
        if not email:
            return Response({'detail': 'No email in Google token.'}, status=status.HTTP_400_BAD_REQUEST)

        # Get or create user
        from .models import User
        user, created = User.objects.get_or_create(email=email, defaults={
            'username': email,
            'name': data.get('name', ''),
            'first_name': data.get('given_name', ''),
            'last_name': data.get('family_name', ''),
        })
        if created:
            user.set_unusable_password()
            user.save()

        # Issue JWT
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        })

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def upload_profile_image(request):
    """
    Upload a profile image for the authenticated user
    """
    try:
        file_obj = request.FILES.get('image')
        if not file_obj:
            return Response({'detail': 'No image provided.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate file type
        allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/jpg']
        if file_obj.content_type not in allowed_types:
            return Response({'detail': f'Invalid file type: {file_obj.content_type}'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate file size (5MB limit for profile images)
        max_size = 5 * 1024 * 1024
        if file_obj.size > max_size:
            return Response({'detail': 'File too large. Maximum size is 5MB.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Generate unique filename
        file_extension = os.path.splitext(file_obj.name)[1] if file_obj.name else '.jpg'
        if not file_extension:
            if file_obj.content_type == 'image/png':
                file_extension = '.png'
            elif file_obj.content_type in ['image/jpeg', 'image/jpg']:
                file_extension = '.jpg'
            elif file_obj.content_type == 'image/gif':
                file_extension = '.gif'
            elif file_obj.content_type == 'image/webp':
                file_extension = '.webp'
            else:
                file_extension = '.jpg'
        
        unique_filename = f"{uuid.uuid4().hex}{file_extension}"
        file_path = f'profile_images/{unique_filename}'
        
        # Save file
        path = default_storage.save(file_path, file_obj)
        
        # Update user's profile image
        request.user.profile_image = path
        request.user.save()
        
        # Generate URL
        image_url = request.build_absolute_uri(f'{settings.MEDIA_URL}{path}')
        
        return Response({'url': image_url}, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Error uploading profile image: {str(e)}")
        return Response({'detail': f'Upload failed: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class HealthCheckView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, format=None):
        from datetime import datetime
        return Response({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'message': 'Users backend is running'
        }, status=status.HTTP_200_OK)

# Authentication endpoints for Next.js admin panel
@api_view(['POST'])
@permission_classes([AllowAny])
def admin_login(request):
    """
    Admin login endpoint for Next.js admin panel
    """
    try:
        email = request.data.get('email')
        password = request.data.get('password')
        
        if not email or not password:
            return Response({
                'error': 'Email and password are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Authenticate user
        from django.contrib.auth import authenticate
        user = authenticate(username=email, password=password)
        
        if not user:
            return Response({
                'error': 'Invalid credentials'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Check if user is staff (admin)
        if not user.is_staff:
            return Response({
                'error': 'Access denied. Admin privileges required.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': {
                'id': user.id,
                'email': user.email,
                'name': user.name or user.email,
                'is_staff': user.is_staff,
                'is_superuser': user.is_superuser,
            },
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'message': 'Login successful'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Admin login error: {str(e)}")
        return Response({
            'error': 'Login failed'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_current_user(request):
    """
    Get current authenticated user info
    """
    try:
        user = request.user
        return Response({
            'user': {
                'id': user.id,
                'email': user.email,
                'name': user.name or user.email,
                'is_staff': user.is_staff,
                'is_superuser': user.is_superuser,
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Get current user error: {str(e)}")
        return Response({
            'error': 'Failed to get user info'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def admin_logout(request):
    """
    Admin logout endpoint
    """
    try:
        # In JWT, logout is typically handled client-side by removing tokens
        # But we can add any server-side cleanup here if needed
        return Response({
            'message': 'Logout successful'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Admin logout error: {str(e)}")
        return Response({
            'error': 'Logout failed'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)