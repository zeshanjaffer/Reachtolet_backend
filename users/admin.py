from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    # List display with all important fields
    list_display = (
        'username', 'email', 'name', 'get_formatted_phone_display', 'first_name', 'last_name', 
        'is_staff', 'is_active', 'date_joined'
    )
    
    # Search functionality
    search_fields = ('username', 'email', 'name', 'first_name', 'last_name', 'phone', 'country_code')
    
    # Filters
    list_filter = (
        'is_staff', 'is_active', 'is_superuser', 'date_joined', 'last_login', 'country_code'
    )
    
    # Fieldsets for detail view
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Information', {
            'fields': ('name', 'first_name', 'last_name', 'email', 'country_code', 'phone', 'profile_image')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Important dates', {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',)
        }),
    )
    
    # Add user fieldsets
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'name', 'country_code', 'phone', 'password1', 'password2'),
        }),
    )
    
    # Read-only fields
    readonly_fields = ('last_login', 'date_joined', 'get_formatted_phone_display')
    
    # List per page
    list_per_page = 25
    
    # Ordering
    ordering = ('-date_joined',)
    
    # Date hierarchy
    date_hierarchy = 'date_joined'
    
    # Actions
    actions = ['activate_users', 'deactivate_users']
    
    def get_formatted_phone_display(self, obj):
        """Display formatted phone number in admin"""
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