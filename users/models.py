from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.core.validators import RegexValidator
import re


class UserManager(BaseUserManager):
    """Custom user manager where email is the unique identifier"""

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular user with the given email and password."""
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a superuser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    # Use email as the username field instead of username
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []  # Remove username from required fields

    # Set custom manager
    objects = UserManager()

    # Override username field - remove it
    username = None

    # Make email required and unique
    email = models.EmailField(
        unique=True,
        verbose_name='email address',
        help_text='Email address used for login'
    )

    # Full name field (required)
    full_name = models.CharField(
        max_length=150,
        help_text="User's full name"
    )

    # Country code field (e.g., 'US', 'GB', 'IN') — optional until profile setup
    country_code = models.CharField(
        max_length=3,
        blank=True,
        null=True,
        help_text="ISO 3166-1 alpha-2 country code (e.g., 'US', 'GB', 'IN')"
    )

    # Phone number field with validation — optional until profile setup
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        validators=[
            RegexValidator(
                regex=r'^(\+[1-9]\d{1,14})?$',
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

    PROFILE_TYPE_CHOICES = [
        ('individual', 'Individual'),
        ('company', 'Company'),
    ]
    profile_type = models.CharField(
        max_length=20,
        choices=PROFILE_TYPE_CHOICES,
        blank=True,
        null=True,
        help_text='Profile type: individual or company'
    )

    preferred_currency = models.CharField(
        max_length=3,
        blank=True,
        null=True,
        help_text='ISO 4217 currency code (e.g., USD, PKR)'
    )
    preferred_language = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        help_text='Preferred language code (e.g., en, ur)'
    )

    company_name = models.CharField(max_length=200, blank=True, null=True)
    company_size = models.CharField(max_length=20, blank=True, null=True)
    company_website = models.CharField(max_length=255, blank=True, null=True)
    company_address = models.TextField(blank=True, null=True)

    profile_setup_completed = models.BooleanField(
        default=False,
        help_text='Whether the user has completed post-registration profile setup'
    )

    apple_sub = models.CharField(
        max_length=255,
        unique=True,
        blank=True,
        null=True,
        help_text='Apple Sign In subject identifier'
    )

    def __str__(self):
        return self.email

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

        # Phone/country required only after profile setup is completed
        if not self.profile_setup_completed:
            return

        if not self.phone:
            raise models.ValidationError("Phone number is required")

        if not self.country_code:
            raise models.ValidationError("Country code is required")

        # Validate country code format
        if not re.match(r'^[A-Z]{2}$', self.country_code):
            raise models.ValidationError("Country code must be 2 uppercase letters (e.g., 'US', 'GB')")

    class Meta:
        db_table = 'users_user'
        indexes = [
            models.Index(fields=['user_type', 'is_active']),
        ]


class PasswordResetOTP(models.Model):
    """OTP + reset-token flow for forgot-password."""

    email = models.EmailField(db_index=True)
    otp_hash = models.CharField(max_length=128)
    attempts = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)
    reset_token = models.UUIDField(default=None, null=True, blank=True, unique=True)
    reset_token_created_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email', 'is_used']),
        ]

    def __str__(self):
        return f"PasswordResetOTP({self.email}, used={self.is_used})"
