from rest_framework import serializers
from .models import User
from django.contrib.auth.password_validation import validate_password
from .country_codes import is_valid_country_code, validate_phone_for_country
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import authenticate
import re

ALLOWED_LANGUAGES = {'en', 'ur', 'ar', 'hi', 'fr', 'es', 'de', 'tr', 'zh', 'pt'}
ALLOWED_CURRENCIES = {
    'USD', 'PKR', 'EUR', 'GBP', 'AED', 'SAR', 'INR', 'CAD', 'AUD',
    'CHF', 'JPY', 'CNY', 'TRY', 'QAR', 'KWD', 'BHD', 'OMR', 'EGP',
    'NZD', 'SGD', 'HKD', 'MYR', 'THB', 'ZAR', 'BRL', 'MXN',
}
COMPANY_SIZE_CHOICES = ['1-10', '11-50', '51-200', '201-500', '500+']
PROFILE_NULLABLE_STRING_FIELDS = (
    'phone', 'country_code', 'full_name', 'profile_type',
    'preferred_language', 'preferred_currency',
    'company_name', 'company_size', 'company_website', 'company_address',
)


def _nullify_empty(value):
    if value == '' or value is None:
        return None
    return value


def normalize_profile_representation(data):
    """Convert empty strings to null for profile API responses."""
    for key in PROFILE_NULLABLE_STRING_FIELDS:
        if key in data and data[key] == '':
            data[key] = None
    if 'formatted_phone' in data and data['formatted_phone'] == '':
        data['formatted_phone'] = None
    return data


def validate_language_code(value):
    if value in (None, ''):
        return None
    value = str(value).strip().lower()
    if value not in ALLOWED_LANGUAGES:
        raise serializers.ValidationError(
            f"preferred_language must be one of: {', '.join(sorted(ALLOWED_LANGUAGES))}"
        )
    return value


def validate_currency_code(value):
    if value in (None, ''):
        return None
    value = str(value).strip().upper()
    if not re.match(r'^[A-Z]{3}$', value):
        raise serializers.ValidationError('preferred_currency must be a 3-letter ISO currency code.')
    if value not in ALLOWED_CURRENCIES:
        raise serializers.ValidationError(
            f"Unsupported currency: {value}. Use a common ISO 4217 code (e.g. USD, PKR, EUR)."
        )
    return value


def validate_company_size_value(value):
    if value in (None, ''):
        return None
    value = str(value).strip()
    if value not in COMPANY_SIZE_CHOICES:
        raise serializers.ValidationError(
            f"company_size must be one of: {', '.join(COMPANY_SIZE_CHOICES)}"
        )
    return value


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom token serializer that accepts both email and username"""
    username_field = 'email'  # Use email as username field

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Keep username field but make it optional
        # Add email field
        self.fields['email'] = serializers.EmailField(required=False, allow_blank=True)

    def validate(self, attrs):
        # Get email
        email = attrs.get('email', '').strip()
        password = attrs.get('password')

        if not password:
            raise serializers.ValidationError({
                'password': 'Password is required.'
            })

        if not email:
            raise serializers.ValidationError({
                'email': 'Email is required.'
            })

        # Authenticate using email
        login_email = email

        if not login_email:
            raise serializers.ValidationError({
                'detail': 'No active account found with the given credentials'
            })

        # Authenticate using email (email is the USERNAME_FIELD)
        user = authenticate(username=login_email, password=password)

        if not user:
            raise serializers.ValidationError({
                'detail': 'No active account found with the given credentials'
            })

        if not user.is_active:
            raise serializers.ValidationError({
                'detail': 'User account is disabled.'
            })

        # Get the token
        refresh = self.get_token(user)

        data = {
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': {
                'id': user.id,
                'email': user.email,
                'full_name': user.full_name,
                'phone': user.phone or None,
                'country_code': user.country_code or None,
                'user_type': user.user_type,
                'preferred_currency': user.preferred_currency or None,
                'profile_setup_completed': user.profile_setup_completed,
            }
        }

        return data


class UserSerializer(serializers.ModelSerializer):
    formatted_phone = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'email', 'phone', 'country_code', 'formatted_phone', 'full_name',
            'profile_image', 'user_type', 'profile_type', 'preferred_language',
            'preferred_currency', 'company_name', 'company_size', 'company_website',
            'company_address', 'profile_setup_completed',
        ]

    def get_formatted_phone(self, obj):
        return obj.get_formatted_phone()

    def to_representation(self, instance):
        data = super().to_representation(instance)
        return normalize_profile_representation(data)


class RegisterSerializer(serializers.ModelSerializer):
    """Slim registration: email, password, full_name, user_type only."""

    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    full_name = serializers.CharField(max_length=150, required=True)
    user_type = serializers.ChoiceField(
        choices=User.USER_TYPE_CHOICES,
        required=True,
        help_text="User role: 'advertiser' or 'media_owner'"
    )

    class Meta:
        model = User
        fields = ['id', 'email', 'full_name', 'password', 'user_type']

    def validate_user_type(self, value):
        valid_types = ['advertiser', 'media_owner']
        if value not in valid_types:
            raise serializers.ValidationError(
                f"user_type must be one of: {', '.join(valid_types)}"
            )
        return value

    def validate(self, data):
        if 'user_type' not in data:
            raise serializers.ValidationError({
                'user_type': 'This field is required.'
            })

        if not data.get('email'):
            raise serializers.ValidationError({
                'email': 'Email is required.'
            })

        if not data.get('full_name'):
            raise serializers.ValidationError({
                'full_name': 'Full name is required.'
            })

        return data

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            full_name=validated_data['full_name'],
            user_type=validated_data.get('user_type', 'advertiser'),
            profile_setup_completed=False,
        )
        return user


class ProfileSetupSerializer(serializers.Serializer):
    """First-time profile setup after slim registration / social login."""

    profile_type = serializers.ChoiceField(choices=['individual', 'company'], required=True)
    preferred_language = serializers.CharField(required=True)
    preferred_currency = serializers.CharField(required=True)
    phone = serializers.CharField(required=True)
    country_code = serializers.CharField(required=True)
    profile_image = serializers.ImageField(required=False, allow_null=True)

    company_name = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    company_size = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    company_website = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    company_address = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    def validate_preferred_language(self, value):
        return validate_language_code(value)

    def validate_preferred_currency(self, value):
        return validate_currency_code(value)

    def validate_country_code(self, value):
        if not value:
            raise serializers.ValidationError('Country code is required.')
        value = value.upper().strip()
        if not re.match(r'^[A-Z]{2}$', value):
            raise serializers.ValidationError("Country code must be 2 uppercase letters (e.g., 'US', 'GB')")
        if not is_valid_country_code(value):
            raise serializers.ValidationError(f"Invalid country code: {value}.")
        return value

    def validate_phone(self, value):
        if not value:
            raise serializers.ValidationError('Phone number is required.')
        cleaned_phone = re.sub(r'[^\d+]', '', value)
        if not re.match(r'^\+[1-9]\d{1,14}$', cleaned_phone):
            raise serializers.ValidationError(
                "Phone number must be in international format (e.g., '+1234567890')"
            )
        return cleaned_phone

    def validate_company_size(self, value):
        return validate_company_size_value(value)

    def validate(self, data):
        phone = data.get('phone')
        country_code = data.get('country_code')
        if phone and country_code:
            is_valid, error_message = validate_phone_for_country(phone, country_code)
            if not is_valid:
                raise serializers.ValidationError({'phone': error_message})

        profile_type = data.get('profile_type')
        if profile_type == 'company':
            errors = {}
            if not data.get('company_name'):
                errors['company_name'] = 'This field is required for company profiles.'
            if not data.get('company_size'):
                errors['company_size'] = 'This field is required for company profiles.'
            if not data.get('company_address'):
                errors['company_address'] = 'This field is required for company profiles.'
            if errors:
                raise serializers.ValidationError(errors)
        else:
            data['company_name'] = None
            data['company_size'] = None
            data['company_website'] = None
            data['company_address'] = None

        return data

    def update(self, instance, validated_data):
        instance.profile_type = validated_data['profile_type']
        instance.preferred_language = validated_data['preferred_language']
        instance.preferred_currency = validated_data['preferred_currency']
        instance.phone = validated_data['phone']
        instance.country_code = validated_data['country_code']
        instance.company_name = validated_data.get('company_name')
        instance.company_size = validated_data.get('company_size')
        instance.company_website = _nullify_empty(validated_data.get('company_website'))
        instance.company_address = validated_data.get('company_address')
        if 'profile_image' in validated_data and validated_data['profile_image'] is not None:
            instance.profile_image = validated_data['profile_image']
        instance.profile_setup_completed = True
        instance.save()
        return instance


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    formatted_phone = serializers.SerializerMethodField()
    remove_profile_image = serializers.BooleanField(required=False, write_only=True, default=False)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'phone', 'country_code', 'formatted_phone', 'full_name',
            'profile_image', 'user_type', 'profile_type', 'preferred_language',
            'preferred_currency', 'company_name', 'company_size', 'company_website',
            'company_address', 'profile_setup_completed', 'remove_profile_image',
        ]
        read_only_fields = ['id', 'email', 'user_type', 'profile_setup_completed']

    def get_formatted_phone(self, obj):
        return obj.get_formatted_phone()

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data.pop('remove_profile_image', None)
        return normalize_profile_representation(data)

    def validate_user_type(self, value):
        if self.instance and self.instance.user_type != value:
            raise serializers.ValidationError(
                "user_type cannot be changed after registration"
            )
        return value

    def validate_preferred_language(self, value):
        return validate_language_code(value)

    def validate_preferred_currency(self, value):
        return validate_currency_code(value)

    def validate_profile_type(self, value):
        if value in (None, ''):
            return None
        if value not in ('individual', 'company'):
            raise serializers.ValidationError("profile_type must be 'individual' or 'company'")
        return value

    def validate_company_size(self, value):
        return validate_company_size_value(value)

    def validate_country_code(self, value):
        if value in (None, ''):
            return None
        value = value.upper()
        if not re.match(r'^[A-Z]{2}$', value):
            raise serializers.ValidationError("Country code must be 2 uppercase letters (e.g., 'US', 'GB')")
        if not is_valid_country_code(value):
            raise serializers.ValidationError(f"Invalid country code: {value}. Please use a valid ISO 3166-1 alpha-2 country code.")
        return value

    def validate_phone(self, value):
        if value in (None, ''):
            return None
        cleaned_phone = re.sub(r'[^\d+]', '', value)
        if not re.match(r'^\+[1-9]\d{1,14}$', cleaned_phone):
            raise serializers.ValidationError(
                "Phone number must be in international format (e.g., '+1234567890')"
            )
        return cleaned_phone

    def validate(self, data):
        phone = data.get('phone', getattr(self.instance, 'phone', None) if self.instance else None)
        country_code = data.get('country_code', getattr(self.instance, 'country_code', None) if self.instance else None)

        if phone is not None and country_code is not None:
            is_valid, error_message = validate_phone_for_country(phone, country_code)
            if not is_valid:
                raise serializers.ValidationError({
                    "phone": error_message
                })

        profile_type = data.get(
            'profile_type',
            getattr(self.instance, 'profile_type', None) if self.instance else None,
        )
        if profile_type == 'company':
            company_name = data.get(
                'company_name',
                getattr(self.instance, 'company_name', None) if self.instance else None,
            )
            company_size = data.get(
                'company_size',
                getattr(self.instance, 'company_size', None) if self.instance else None,
            )
            company_address = data.get(
                'company_address',
                getattr(self.instance, 'company_address', None) if self.instance else None,
            )
            errors = {}
            if not company_name:
                errors['company_name'] = 'This field is required for company profiles.'
            if not company_size:
                errors['company_size'] = 'This field is required for company profiles.'
            if not company_address:
                errors['company_address'] = 'This field is required for company profiles.'
            # Only enforce when switching to / staying company and sending related fields
            if 'profile_type' in data or any(
                k in data for k in ('company_name', 'company_size', 'company_address')
            ):
                if errors:
                    raise serializers.ValidationError(errors)

        return data

    def update(self, instance, validated_data):
        remove_image = validated_data.pop('remove_profile_image', False)
        profile_type = validated_data.get('profile_type', instance.profile_type)

        if profile_type == 'individual':
            validated_data['company_name'] = None
            validated_data['company_size'] = None
            validated_data['company_website'] = None
            validated_data['company_address'] = None

        for field in (
            'phone', 'country_code', 'full_name', 'profile_type',
            'preferred_language', 'preferred_currency',
            'company_name', 'company_size', 'company_website', 'company_address',
        ):
            if field in validated_data:
                value = validated_data[field]
                setattr(instance, field, _nullify_empty(value) if isinstance(value, str) else value)

        if remove_image:
            if instance.profile_image:
                instance.profile_image.delete(save=False)
            instance.profile_image = None
        elif 'profile_image' in validated_data and validated_data['profile_image'] is not None:
            instance.profile_image = validated_data['profile_image']

        instance.save()
        return instance


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)


class VerifyResetOTPSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    otp = serializers.CharField(required=True, min_length=6, max_length=6)


class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    reset_token = serializers.UUIDField(required=True)
    new_password = serializers.CharField(required=True, write_only=True, validators=[validate_password])
    confirm_password = serializers.CharField(required=True, write_only=True)

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({'confirm_password': 'Passwords do not match.'})
        return data


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True, validators=[validate_password])
    confirm_password = serializers.CharField(required=True, write_only=True)

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({'confirm_password': 'Passwords do not match.'})
        return data


class AppleLoginSerializer(serializers.Serializer):
    identity_token = serializers.CharField(required=True)
    user_type = serializers.ChoiceField(
        choices=User.USER_TYPE_CHOICES,
        required=False,
        default='advertiser',
    )
    full_name = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    email = serializers.EmailField(required=False, allow_blank=True, allow_null=True)
