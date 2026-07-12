from django.urls import path
from .views import (
    RegisterView,
    UserProfileView,
    ProfileSetupView,
    GoogleLoginView,
    AppleLoginView,
    HealthCheckView,
    validate_token,
    get_country_codes,
    CustomTokenObtainPairView,
    CustomTokenRefreshView,
    LogoutView,
    ForgotPasswordView,
    VerifyResetOTPView,
    ResetPasswordView,
    ChangePasswordView,
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('validate-token/', validate_token, name='validate_token'),
    path('country-codes/', get_country_codes, name='country_codes'),
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('profile/setup/', ProfileSetupView.as_view(), name='profile-setup'),
    path('google-login/', GoogleLoginView.as_view(), name='google-login'),
    path('apple-login/', AppleLoginView.as_view(), name='apple-login'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('verify-reset-otp/', VerifyResetOTPView.as_view(), name='verify-reset-otp'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset-password'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    # Profile image: multipart on PUT profile/setup/ or PUT/PATCH profile/ (no separate upload URL)
    path('logout/', LogoutView.as_view(), name='logout'),
    path('health/', HealthCheckView.as_view(), name='health-check'),
]
