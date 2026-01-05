from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator
import re

class User(AbstractUser):
    # Country code field (e.g., 'US', 'GB', 'IN')
    country_code = models.CharField(
        max_length=3, 
        blank=True, 
        null=True,
        help_text="ISO 3166-1 alpha-2 country code (e.g., 'US', 'GB', 'IN')"
    )
    
    # Phone number field with validation
    phone = models.CharField(
        max_length=20, 
        blank=True, 
        null=True,
        validators=[
            RegexValidator(
                regex=r'^\+[1-9]\d{1,14}$',
                message='Phone number must be in international format (e.g., +1234567890)'
            )
        ],
        help_text="International phone number (e.g., '+1234567890')"
    )
    
    name = models.CharField(max_length=150, blank=True, null=True)
    profile_image = models.ImageField(upload_to='profile_images/', null=True, blank=True)
    
    # User type field for role-based access control
    USER_TYPE_CHOICES = [
        ('advertiser', 'Advertiser'),
        ('media_owner', 'Media Owner'),
    ]
    user_type = models.CharField(
        max_length=20,
        choices=USER_TYPE_CHOICES,
        default='advertiser',
        help_text='User role: advertiser or media_owner'
    )

    def __str__(self):
        return self.username or self.email
    
    def is_media_owner(self):
        """Check if user is a media owner"""
        return self.user_type == 'media_owner'
    
    def is_advertiser(self):
        """Check if user is an advertiser"""
        return self.user_type == 'advertiser'
    
    def can_create_billboards(self):
        """Check if user can create billboards"""
        return self.is_media_owner()
    
    def get_formatted_phone(self):
        """Return formatted phone number with country code"""
        if self.phone and self.country_code:
            return f"{self.country_code} {self.phone}"
        return self.phone
    
    def clean(self):
        """Validate phone number and country code consistency"""
        super().clean()
        
        if self.phone and not self.country_code:
            raise models.ValidationError("Country code is required when phone number is provided")
        
        if self.country_code and not self.phone:
            raise models.ValidationError("Phone number is required when country code is provided")
        
        # Validate country code format
        if self.country_code:
            if not re.match(r'^[A-Z]{2}$', self.country_code):
                raise models.ValidationError("Country code must be 2 uppercase letters (e.g., 'US', 'GB')")
    
    class Meta:
        db_table = 'users_user'