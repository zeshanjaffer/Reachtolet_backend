from rest_framework import serializers
from .models import User
from django.contrib.auth.password_validation import validate_password
from .country_codes import is_valid_country_code, validate_phone_for_country, get_country_info
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import authenticate
import re

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
                'user_type': user.user_type
            }
        }
        
        return data
class UserSerializer(serializers.ModelSerializer):
    formatted_phone = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'email', 'phone', 'country_code', 'formatted_phone', 'full_name', 'profile_image', 'user_type']
    
    def get_formatted_phone(self, obj):
        """Return formatted phone number with country code"""
        return obj.get_formatted_phone()

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    full_name = serializers.CharField(max_length=150, required=True)
    phone = serializers.CharField(max_length=20, required=True)
    country_code = serializers.CharField(max_length=3, required=True)
    user_type = serializers.ChoiceField(
        choices=User.USER_TYPE_CHOICES,
        required=True,
        help_text="User role: 'advertiser' or 'media_owner'"
    )

    class Meta:
        model = User
        fields = ['id', 'email', 'phone', 'country_code', 'full_name', 'password', 'user_type']


    def validate_country_code(self, value):
        """Validate country code format and existence"""
        if value:
            # Convert to uppercase
            value = value.upper()
            
            # Check format
            if not re.match(r'^[A-Z]{2}$', value):
                raise serializers.ValidationError("Country code must be 2 uppercase letters (e.g., 'US', 'GB')")
            
            # Check if country code exists in our database
            if not is_valid_country_code(value):
                raise serializers.ValidationError(f"Invalid country code: {value}. Please use a valid ISO 3166-1 alpha-2 country code.")
            
            return value
        return value

    def validate_phone(self, value):
        """Validate phone number format"""
        if value:
            # Remove any spaces or special characters except +
            cleaned_phone = re.sub(r'[^\d+]', '', value)
            
            # Ensure it starts with + and has valid format
            if not re.match(r'^\+[1-9]\d{1,14}$', cleaned_phone):
                raise serializers.ValidationError(
                    "Phone number must be in international format (e.g., '+1234567890')"
                )
            return cleaned_phone
        return value
    
    def validate_user_type(self, value):
        """Validate user_type field"""
        valid_types = ['advertiser', 'media_owner']
        if value not in valid_types:
            raise serializers.ValidationError(
                f"user_type must be one of: {', '.join(valid_types)}"
            )
        return value


    
    def validate(self, data):
        """Validate phone and country code consistency"""
        # Ensure required fields are provided
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
        
        if not data.get('phone'):
            raise serializers.ValidationError({
                'phone': 'Phone number is required.'
            })
        
        if not data.get('country_code'):
            raise serializers.ValidationError({
                'country_code': 'Country code is required.'
            })
        
        phone = data.get('phone', '').strip()
        country_code = data.get('country_code', '').strip()
        
        # Validate phone number for specific country
        if phone and country_code:
            is_valid, error_message = validate_phone_for_country(phone, country_code)
            if not is_valid:
                raise serializers.ValidationError({
                    "phone": error_message
                })
        
        return data

    def create(self, validated_data):
        # Create user with email
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            phone=validated_data['phone'],
            country_code=validated_data['country_code'],
            full_name=validated_data['full_name'],
            user_type=validated_data.get('user_type', 'advertiser'),
        )
        return user

class UserProfileUpdateSerializer(serializers.ModelSerializer):
    formatted_phone = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'email', 'phone', 'country_code', 'formatted_phone', 'full_name', 'profile_image', 'user_type']
        read_only_fields = ['id', 'email', 'user_type']
    
    def get_formatted_phone(self, obj):
        """Return formatted phone number with country code"""
        return obj.get_formatted_phone()
    
    def validate_user_type(self, value):
        """Prevent user_type changes after registration"""
        if self.instance and self.instance.user_type != value:
            raise serializers.ValidationError(
                "user_type cannot be changed after registration"
            )
        return value
    
    def validate_country_code(self, value):
        """Validate country code format and existence"""
        if value:
            # Convert to uppercase
            value = value.upper()
            
            # Check format
            if not re.match(r'^[A-Z]{2}$', value):
                raise serializers.ValidationError("Country code must be 2 uppercase letters (e.g., 'US', 'GB')")
            
            # Check if country code exists in our database
            if not is_valid_country_code(value):
                raise serializers.ValidationError(f"Invalid country code: {value}. Please use a valid ISO 3166-1 alpha-2 country code.")
            
            return value
        return value

    def validate_phone(self, value):
        """Validate phone number format"""
        if value:
            # Remove any spaces or special characters except +
            cleaned_phone = re.sub(r'[^\d+]', '', value)
            
            # Ensure it starts with + and has valid format
            if not re.match(r'^\+[1-9]\d{1,14}$', cleaned_phone):
                raise serializers.ValidationError(
                    "Phone number must be in international format (e.g., '+1234567890')"
                )
            return cleaned_phone
        return value

    def validate(self, data):
        """Validate phone and country code consistency"""
        phone = data.get('phone')
        country_code = data.get('country_code')
        
        # Phone and country_code are both required, so they should always be present
        # But in update, they might not be in data if not being updated
        if phone is not None and country_code is not None:
            # Validate phone number for specific country
            is_valid, error_message = validate_phone_for_country(phone, country_code)
            if not is_valid:
                raise serializers.ValidationError({
                    "phone": error_message
                })
        
        return data