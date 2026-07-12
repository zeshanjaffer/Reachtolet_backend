from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from core.responses import action_response, auth_response
from .models import User, PasswordResetOTP
from .serializers import (
    UserSerializer,
    RegisterSerializer,
    UserProfileUpdateSerializer,
    CustomTokenObtainPairSerializer,
    ProfileSetupSerializer,
    ForgotPasswordSerializer,
    VerifyResetOTPSerializer,
    ResetPasswordSerializer,
    ChangePasswordSerializer,
    AppleLoginSerializer,
)
from .email_service import send_otp_email
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework.decorators import api_view, permission_classes
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.utils import timezone
from .country_codes import COUNTRY_CODES
import hashlib
import jwt
import requests
import os
import secrets
import uuid
import logging
from datetime import timedelta

logger = logging.getLogger(__name__)

OTP_EXPIRY_MINUTES = 10
RESET_TOKEN_EXPIRY_MINUTES = 15
MAX_OTP_ATTEMPTS = 5
APPLE_JWKS_URL = 'https://appleid.apple.com/auth/keys'
APPLE_ISSUER = 'https://appleid.apple.com'


def _google_allowed_audiences():
    """
    Return allowed Google OAuth client IDs from env.
    Supports one or many values (comma-separated).
    """
    raw = os.environ.get("GOOGLE_CLIENT_IDS") or os.environ.get("GOOGLE_CLIENT_ID", "")
    values = [item.strip() for item in raw.split(",") if item.strip()]
    return set(values)


def _apple_allowed_audiences():
    raw = os.environ.get('APPLE_CLIENT_IDS', '')
    return [item.strip() for item in raw.split(',') if item.strip()]


def _hash_otp(otp: str) -> str:
    return hashlib.sha256(otp.encode('utf-8')).hexdigest()


def _generate_otp() -> str:
    return f'{secrets.randbelow(10 ** 6):06d}'


def _auth_user_payload(user):
    return {
        'id': user.id,
        'email': user.email,
        'full_name': user.full_name,
        'phone': user.phone or None,
        'country_code': user.country_code or None,
        'user_type': user.user_type,
        'preferred_currency': user.preferred_currency or None,
        'profile_setup_completed': user.profile_setup_completed,
    }


class CustomTokenObtainPairView(TokenObtainPairView):
    """Custom login view that accepts email instead of username"""
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        return auth_response(
            'Logged in successfully',
            status.HTTP_200_OK,
            data['access'],
            data['refresh'],
            data.get('user'),
        )


class CustomTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        return auth_response(
            'Token refreshed successfully',
            status.HTTP_200_OK,
            data['access'],
            data.get('refresh', request.data.get('refresh')),
        )


def _user_from_bearer_access(request):
    """Return user if Authorization Bearer access token is valid, else None."""
    auth = JWTAuthentication()
    header = auth.get_header(request)
    if header is None:
        return None
    try:
        raw = auth.get_raw_token(header)
        validated = auth.get_validated_token(raw)
        return auth.get_user(validated)
    except Exception:
        return None


class LogoutView(APIView):
    """
    Logout: client should clear stored tokens.
    Accepts either a valid Bearer access token, or JSON body {"refresh": "..."}.
    If refresh is sent, it is blacklisted (requires token_blacklist app).
    """
    permission_classes = (AllowAny,)

    def post(self, request):
        user = _user_from_bearer_access(request)
        refresh_str = request.data.get("refresh")

        if refresh_str:
            try:
                token = RefreshToken(refresh_str)
                token.blacklist()
            except TokenError as e:
                return action_response(str(e), status.HTTP_401_UNAUTHORIZED)

        if user is not None or refresh_str:
            return action_response('Logged out successfully', status.HTTP_200_OK)

        return action_response(
            'Provide Authorization: Bearer <access> and/or a valid refresh token in the JSON body.',
            status.HTTP_401_UNAUTHORIZED,
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
        "user": _auth_user_payload(request.user),
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
        refresh = RefreshToken.for_user(user)
        return auth_response(
            'User registered successfully',
            status.HTTP_201_CREATED,
            str(refresh.access_token),
            str(refresh),
            _auth_user_payload(user),
        )


class UserProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get_object(self):
        return self.request.user

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return UserProfileUpdateSerializer
        return UserSerializer

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        # Multipart often sends remove_profile_image as string "true"
        if str(data.get('remove_profile_image', '')).lower() in ('true', '1', 'yes'):
            data['remove_profile_image'] = True
        serializer = self.get_serializer(instance, data=data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(UserSerializer(instance, context={'request': request}).data)


class ProfileSetupView(APIView):
    """PUT /api/users/profile/setup/ — one-time profile completion."""

    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def put(self, request):
        user = request.user
        if user.profile_setup_completed:
            return Response(
                {
                    'detail': 'Profile setup already completed. Use PUT/PATCH /api/users/profile/ to update your profile.',
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = ProfileSetupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.update(user, serializer.validated_data)
        return Response(
            UserSerializer(user, context={'request': request}).data,
            status=status.HTTP_200_OK,
        )


class GoogleLoginView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        id_token = request.data.get('id_token')
        if not id_token:
            return action_response('No ID token provided.', status.HTTP_400_BAD_REQUEST)

        # Verify the token with Google
        google_url = f"https://oauth2.googleapis.com/tokeninfo?id_token={id_token}"
        resp = requests.get(google_url)
        if resp.status_code != 200:
            return action_response('Invalid Google token.', status.HTTP_400_BAD_REQUEST)
        data = resp.json()
        token_aud = data.get('aud')
        allowed_audiences = _google_allowed_audiences()
        if not allowed_audiences:
            logger.error("Google login misconfigured: GOOGLE_CLIENT_ID(S) not set")
            return action_response('Google login is not configured.', status.HTTP_500_INTERNAL_SERVER_ERROR)
        if token_aud not in allowed_audiences:
            logger.warning(
                "Google login invalid audience: token_aud=%s expected_one_of=%s",
                token_aud,
                sorted(allowed_audiences),
            )
            return action_response('Invalid audience.', status.HTTP_400_BAD_REQUEST)
        email = data.get('email')
        if not email:
            return action_response('No email in Google token.', status.HTTP_400_BAD_REQUEST)

        # Get user_type from request (required for new users)
        user_type = request.data.get('user_type', 'advertiser')
        if user_type not in ['advertiser', 'media_owner']:
            user_type = 'advertiser'  # Default to advertiser if invalid

        # Combine given_name and family_name into full_name
        full_name = data.get('name', '')
        if not full_name:
            given_name = data.get('given_name', '')
            family_name = data.get('family_name', '')
            full_name = f"{given_name} {family_name}".strip()

        user, created = User.objects.get_or_create(email=email, defaults={
            'full_name': full_name or 'Google User',
            'user_type': user_type,
            'profile_setup_completed': False,
        })
        if created:
            user.set_unusable_password()
            user.save()

        refresh = RefreshToken.for_user(user)
        return auth_response(
            'Google login successful',
            status.HTTP_200_OK,
            str(refresh.access_token),
            str(refresh),
            _auth_user_payload(user),
        )


class AppleLoginView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        audiences = _apple_allowed_audiences()
        if not audiences:
            return action_response(
                'Apple login is not configured.',
                status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        serializer = AppleLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        identity_token = serializer.validated_data['identity_token']
        user_type = serializer.validated_data.get('user_type') or 'advertiser'
        provided_full_name = serializer.validated_data.get('full_name') or ''
        provided_email = serializer.validated_data.get('email') or ''

        try:
            jwks_client = jwt.PyJWKClient(APPLE_JWKS_URL)
            signing_key = jwks_client.get_signing_key_from_jwt(identity_token)
            claims = jwt.decode(
                identity_token,
                signing_key.key,
                algorithms=['RS256'],
                audience=audiences,
                issuer=APPLE_ISSUER,
            )
        except Exception as exc:
            logger.warning('Apple token verification failed: %s', exc)
            return action_response('Invalid Apple identity token.', status.HTTP_400_BAD_REQUEST)

        apple_sub = claims.get('sub')
        if not apple_sub:
            return action_response('Invalid Apple identity token.', status.HTTP_400_BAD_REQUEST)

        email = claims.get('email') or provided_email
        user = User.objects.filter(apple_sub=apple_sub).first()
        if user is None and email:
            user = User.objects.filter(email=email).first()
            if user and not user.apple_sub:
                user.apple_sub = apple_sub
                user.save(update_fields=['apple_sub'])

        if user is None:
            if not email:
                # Apple may hide email on subsequent logins; require email for brand-new users
                return action_response(
                    'Email is required to create a new account with Apple.',
                    status.HTTP_400_BAD_REQUEST,
                )
            user = User.objects.create_user(
                email=email,
                password=None,
                full_name=(provided_full_name or 'Apple User').strip() or 'Apple User',
                user_type=user_type if user_type in ('advertiser', 'media_owner') else 'advertiser',
                apple_sub=apple_sub,
                profile_setup_completed=False,
            )
            user.set_unusable_password()
            user.save()
        elif provided_full_name and (not user.full_name or user.full_name in ('Apple User', 'Google User')):
            user.full_name = provided_full_name.strip()
            user.save(update_fields=['full_name'])

        refresh = RefreshToken.for_user(user)
        return auth_response(
            'Apple login successful',
            status.HTTP_200_OK,
            str(refresh.access_token),
            str(refresh),
            _auth_user_payload(user),
        )


class ForgotPasswordView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email'].strip().lower()
        generic_message = 'If an account exists for this email, a reset code has been sent.'

        user = User.objects.filter(email__iexact=email).first()
        if not user:
            return Response({'message': generic_message}, status=status.HTTP_200_OK)

        otp = _generate_otp()
        PasswordResetOTP.objects.filter(email__iexact=email, is_used=False).update(is_used=True)
        PasswordResetOTP.objects.create(
            email=user.email,
            otp_hash=_hash_otp(otp),
        )

        try:
            send_otp_email(user.email, otp)
        except RuntimeError:
            return action_response(
                'Unable to send reset email. Please try again later.',
                status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response({'message': generic_message}, status=status.HTTP_200_OK)


class VerifyResetOTPView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        serializer = VerifyResetOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email'].strip().lower()
        otp = serializer.validated_data['otp'].strip()

        record = (
            PasswordResetOTP.objects
            .filter(email__iexact=email, is_used=False)
            .order_by('-created_at')
            .first()
        )
        if not record:
            return Response({'detail': 'Invalid or expired OTP.'}, status=status.HTTP_400_BAD_REQUEST)

        if record.attempts >= MAX_OTP_ATTEMPTS:
            return Response(
                {'detail': 'Maximum OTP attempts exceeded. Request a new code.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if timezone.now() - record.created_at > timedelta(minutes=OTP_EXPIRY_MINUTES):
            return Response({'detail': 'OTP has expired.'}, status=status.HTTP_400_BAD_REQUEST)

        if record.otp_hash != _hash_otp(otp):
            record.attempts += 1
            record.save(update_fields=['attempts'])
            return Response({'detail': 'Invalid or expired OTP.'}, status=status.HTTP_400_BAD_REQUEST)

        reset_token = uuid.uuid4()
        record.reset_token = reset_token
        record.reset_token_created_at = timezone.now()
        record.save(update_fields=['reset_token', 'reset_token_created_at'])

        return Response({
            'reset_token': str(reset_token),
            'expires_in_minutes': RESET_TOKEN_EXPIRY_MINUTES,
        }, status=status.HTTP_200_OK)


class ResetPasswordView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email'].strip().lower()
        reset_token = serializer.validated_data['reset_token']
        new_password = serializer.validated_data['new_password']

        record = (
            PasswordResetOTP.objects
            .filter(email__iexact=email, reset_token=reset_token, is_used=False)
            .order_by('-created_at')
            .first()
        )
        if not record or not record.reset_token_created_at:
            return Response({'detail': 'Invalid or expired reset token.'}, status=status.HTTP_400_BAD_REQUEST)

        if timezone.now() - record.reset_token_created_at > timedelta(minutes=RESET_TOKEN_EXPIRY_MINUTES):
            return Response({'detail': 'Reset token has expired.'}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(email__iexact=email).first()
        if not user:
            return Response({'detail': 'Invalid or expired reset token.'}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save(update_fields=['password'])
        record.is_used = True
        record.save(update_fields=['is_used'])

        return Response({'message': 'Password reset successfully.'}, status=status.HTTP_200_OK)


class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        if not user.has_usable_password() or not user.check_password(serializer.validated_data['current_password']):
            return Response(
                {'current_password': 'Current password is incorrect.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(serializer.validated_data['new_password'])
        user.save(update_fields=['password'])
        return Response({'message': 'Password changed successfully.'}, status=status.HTTP_200_OK)


class HealthCheckView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, format=None):
        from datetime import datetime
        return Response({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'message': 'Users backend is running'
        }, status=status.HTTP_200_OK)
