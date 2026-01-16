from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from .models import User
from .serializers import UserSerializer, RegisterSerializer, UserProfileUpdateSerializer, CustomTokenObtainPairSerializer
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
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

class CustomTokenObtainPairView(TokenObtainPairView):
    """Custom login view that accepts email instead of username"""
    serializer_class = CustomTokenObtainPairSerializer

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def validate_token(request):
    """
    Simple endpoint to validate if the access token is still valid.
    Returns 200 if valid, 401 if invalid (handled by permission_classes).
    """
    return Response({
        "valid": True,
        "user": {
            "id": request.user.id,
            "email": request.user.email,
            "user_type": request.user.user_type
        }
    }, status=status.HTTP_200_OK)

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
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Automatically log in the user and return JWT tokens
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': {
                'id': user.id,
                'email': user.email,
                'full_name': user.full_name,
                'phone': user.phone,
                'country_code': user.country_code,
                'user_type': user.user_type
            },
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'message': 'User registered successfully'
        }, status=status.HTTP_201_CREATED)

class UserProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def get_serializer_class(self):
        if self.request.method == 'PUT':
            return UserProfileUpdateSerializer
        return UserSerializer

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

        # Get user_type from request (required for new users)
        user_type = request.data.get('user_type', 'advertiser')
        if user_type not in ['advertiser', 'media_owner']:
            user_type = 'advertiser'  # Default to advertiser if invalid
        
        # Get or create user (email is now USERNAME_FIELD, no username needed)
        from .models import User
        # Combine given_name and family_name into full_name
        full_name = data.get('name', '')
        if not full_name:
            given_name = data.get('given_name', '')
            family_name = data.get('family_name', '')
            full_name = f"{given_name} {family_name}".strip()
        
        user, created = User.objects.get_or_create(email=email, defaults={
            'full_name': full_name or 'Google User',
            'phone': '+0000000000',  # Placeholder, user should update
            'country_code': 'US',  # Placeholder, user should update
            'user_type': user_type,
        })
        if created:
            user.set_unusable_password()
            user.save()

        # Issue JWT
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': {
                'id': user.id,
                'email': user.email,
                'user_type': user.user_type
            },
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