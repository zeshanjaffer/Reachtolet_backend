from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, PasswordResetOTP


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        'email', 'full_name', 'get_formatted_phone_display',
        'user_type', 'profile_setup_completed',
        'is_staff', 'is_active', 'date_joined'
    )
    search_fields = ('email', 'full_name', 'phone', 'country_code', 'apple_sub')
    list_filter = (
        'is_staff', 'is_active', 'is_superuser', 'user_type',
        'profile_setup_completed', 'date_joined', 'last_login', 'country_code'
    )
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Information', {
            'fields': (
                'full_name', 'country_code', 'phone', 'profile_image',
                'user_type', 'profile_type', 'preferred_language', 'preferred_currency',
                'profile_setup_completed', 'apple_sub',
            )
        }),
        ('Company', {
            'fields': ('company_name', 'company_size', 'company_website', 'company_address'),
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Important dates', {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',)
        }),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'full_name', 'user_type', 'password1', 'password2'),
        }),
    )
    readonly_fields = ('last_login', 'date_joined', 'get_formatted_phone_display')
    list_per_page = 25
    ordering = ('-date_joined',)
    date_hierarchy = 'date_joined'
    actions = ['activate_users', 'deactivate_users']

    def get_formatted_phone_display(self, obj):
        return obj.get_formatted_phone() or '-'
    get_formatted_phone_display.short_description = 'Phone Number'

    def activate_users(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} users activated successfully.')
    activate_users.short_description = "Activate selected users"

    def deactivate_users(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} users deactivated successfully.')
    deactivate_users.short_description = "Deactivate selected users"


@admin.register(PasswordResetOTP)
class PasswordResetOTPAdmin(admin.ModelAdmin):
    list_display = ('email', 'attempts', 'is_used', 'created_at', 'reset_token')
    list_filter = ('is_used', 'created_at')
    search_fields = ('email',)
    readonly_fields = ('otp_hash', 'created_at', 'reset_token', 'reset_token_created_at')
