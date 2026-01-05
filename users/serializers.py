from rest_framework import serializers
from .models import User
from django.contrib.auth.password_validation import validate_password
from .country_codes import is_valid_country_code, validate_phone_for_country, get_country_info
import re

class UserSerializer(serializers.ModelSerializer):
    formatted_phone = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'phone', 'country_code', 'formatted_phone', 'name', 'first_name', 'last_name', 'profile_image', 'user_type']
    
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
        fields = ['id', 'username', 'email', 'phone', 'country_code', 'name', 'first_name', 'last_name', 'password', 'user_type']

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

    def create(self, validated_data):
        user = User.objects.create(
            username=validated_data['email'],
            email=validated_data['email'],
            phone=validated_data.get('phone', ''),
            country_code=validated_data.get('country_code', ''),
            name=validated_data.get('name', ''),
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            user_type=validated_data.get('user_type', 'advertiser'),
        )
        user.set_password(validated_data['password'])
        user.save()
        return user

class UserProfileUpdateSerializer(serializers.ModelSerializer):
    formatted_phone = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'phone', 'country_code', 'formatted_phone', 'name', 'first_name', 'last_name', 'profile_image', 'user_type']
        read_only_fields = ['id', 'username', 'email', 'user_type']
    
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