from rest_framework import serializers
from .models import User
from django.contrib.auth.password_validation import validate_password
from .country_codes import is_valid_country_code, validate_phone_for_country, get_country_info
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import authenticate
import re

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom token serializer that accepts email only (no username)"""
    username_field = 'email'  # Use email as username field
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove username field, only use email
        if 'username' in self.fields:
            del self.fields['username']
        # Add email field
        self.fields['email'] = serializers.EmailField()
    
    def validate(self, attrs):
        # Get email (required field now)
        email = attrs.get('email')
        password = attrs.get('password')
        
        if not email or not password:
            raise serializers.ValidationError({
                'email': 'Email is required.',
                'password': 'Password is required.'
            })
        
        # Authenticate using email (email is now the USERNAME_FIELD)
        user = authenticate(username=email, password=password)
        
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
        fields = ['id', 'email', 'phone', 'country_code', 'formatted_phone', 'name', 'first_name', 'last_name', 'profile_image', 'user_type']
    
    def get_formatted_phone(self, obj):
        """Return formatted phone number with country code"""
        return obj.get_formatted_phone()

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    country_code = serializers.CharField(max_length=3, required=False, allow_blank=True)
    user_type = serializers.ChoiceField(
        choices=User.USER_TYPE_CHOICES,
        required=True,
        help_text="User role: 'advertiser' or 'media_owner'"
    )
    
    class Meta:
        model = User
        fields = ['id', 'email', 'phone', 'country_code', 'name', 'first_name', 'last_name', 'password', 'user_type']
        extra_kwargs = {
            'username': {'required': False, 'allow_blank': True, 'allow_null': True, 'write_only': False}
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove username field completely from serializer
        if 'username' in self.fields:
            self.fields.pop('username')

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
        # Ensure user_type is provided
        if 'user_type' not in data:
            raise serializers.ValidationError({
                'user_type': 'This field is required.'
            })
        
        # Remove username from data if present (we don't use it)
        data.pop('username', None)
        
        phone = data.get('phone', '').strip()
        country_code = data.get('country_code', '').strip()
        
        # Both phone and country_code are optional, but if one is provided, both should be
        if phone and not country_code:
            raise serializers.ValidationError({
                "country_code": "Country code is required when phone number is provided"
            })
        
        if country_code and not phone:
            raise serializers.ValidationError({
                "phone": "Phone number is required when country code is provided"
            })
        
        # Validate phone number for specific country only if both are provided
        if phone and country_code:
            is_valid, error_message = validate_phone_for_country(phone, country_code)
            if not is_valid:
                raise serializers.ValidationError({
                    "phone": error_message
                })
        
        return data

    def create(self, validated_data):
        # Clean phone and country_code - set to empty string if None
        phone = validated_data.get('phone', '') or ''
        country_code = validated_data.get('country_code', '') or ''
        
        # Create user with email as username (USERNAME_FIELD is email)
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            phone=phone,
            country_code=country_code,
            name=validated_data.get('name', ''),
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            user_type=validated_data.get('user_type', 'advertiser'),
        )
        return user

class UserProfileUpdateSerializer(serializers.ModelSerializer):
    formatted_phone = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'email', 'phone', 'country_code', 'formatted_phone', 'name', 'first_name', 'last_name', 'profile_image', 'user_type']
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
        
        if phone and not country_code:
            raise serializers.ValidationError({
                "country_code": "Country code is required when phone number is provided"
            })
        
        if country_code and not phone:
            raise serializers.ValidationError({
                "phone": "Phone number is required when country code is provided"
            })
        
        # Validate phone number for specific country
        if phone and country_code:
            is_valid, error_message = validate_phone_for_country(phone, country_code)
            if not is_valid:
                raise serializers.ValidationError({
                    "phone": error_message
                })
        
        return data