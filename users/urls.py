from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import RegisterView, UserProfileView, GoogleLoginView, upload_profile_image, HealthCheckView, validate_token, get_country_codes

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('validate-token/', validate_token, name='validate_token'),
    path('country-codes/', get_country_codes, name='country_codes'),
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('google-login/', GoogleLoginView.as_view(), name='google-login'),
    path('upload-profile-image/', upload_profile_image, name='upload-profile-image'),
    path('health/', HealthCheckView.as_view(), name='health-check'),
]