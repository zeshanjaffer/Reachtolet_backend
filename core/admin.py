from django.contrib import admin
from django.contrib.admin import AdminSite
from django.utils.html import format_html
from django.urls import path
from django.shortcuts import render
from django.db.models import Count, Sum
from django.utils import timezone
from datetime import datetime, timedelta
from billboards.models import Billboard, Wishlist
from users.models import User

# Custom Admin Site
class ReachToLetAdminSite(AdminSite):
    site_header = "ReachToLet Administration"
    site_title = "ReachToLet Admin"
    index_title = "Welcome to ReachToLet Administration"
    site_url = "/"

admin_site = ReachToLetAdminSite(name='reachtolet_admin')

# Custom Admin Classes
@admin.register(Billboard)
class BillboardAdmin(admin.ModelAdmin):
    list_display = ('id', 'city', 'ooh_media_type', 'company_name', 'price_range', 'views', 'user', 'created_at', 'status_badge')
    list_filter = ('city', 'ooh_media_type', 'type', 'created_at', 'user')
    search_fields = ('city', 'company_name', 'description', 'road_name', 'ooh_media_id')
    list_editable = ('price_range',)
    readonly_fields = ('views', 'created_at', 'image_preview')
    date_hierarchy = 'created_at'
    list_per_page = 25
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'city', 'description', 'company_name', 'ooh_media_type', 'type')
        }),
        ('Location Details', {
            'fields': ('road_name', 'road_position', 'traffic_direction', 'latitude', 'longitude')
        }),
        ('Specifications', {
            'fields': ('number_of_boards', 'average_daily_views', 'display_height', 'display_width', 'exposure_time')
        }),
        ('Pricing & Contact', {
            'fields': ('price_range', 'advertiser_phone', 'advertiser_whatsapp', 'company_website')
        }),
        ('Media & Content', {
            'fields': ('images', 'image_preview', 'unavailable_dates')
        }),
        ('Analytics', {
            'fields': ('views', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def status_badge(self, obj):
        """Display status badge based on availability"""
        if obj.unavailable_dates and len(obj.unavailable_dates) > 0:
            return format_html('<span style="background-color: #f56565; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px;">Unavailable</span>')
        else:
            return format_html('<span style="background-color: #48bb78; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px;">Available</span>')
    status_badge.short_description = 'Status'
    
    def image_preview(self, obj):
        """Display image preview"""
        if obj.images and len(obj.images) > 0:
            return format_html('<img src="{}" style="max-width: 100px; max-height: 100px; border-radius: 8px;" />', obj.images[0])
        return "No image"
    image_preview.short_description = 'Image Preview'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related('user')
    
    actions = ['mark_as_featured', 'export_to_csv']
    
    def mark_as_featured(self, request, queryset):
        """Custom action to mark billboards as featured"""
        updated = queryset.update(type='Featured')
        self.message_user(request, f'{updated} billboards marked as featured.')
    mark_as_featured.short_description = "Mark selected billboards as featured"
    
    def export_to_csv(self, request, queryset):
        """Export selected billboards to CSV"""
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="billboards.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['ID', 'City', 'Type', 'Company', 'Price', 'Views', 'Created'])
        
        for billboard in queryset:
            writer.writerow([
                billboard.id,
                billboard.city,
                billboard.ooh_media_type,
                billboard.company_name,
                billboard.price_range,
                billboard.views,
                billboard.created_at.strftime('%Y-%m-%d')
            ])
        
        return response
    export_to_csv.short_description = "Export selected billboards to CSV"


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_email', 'billboard_city', 'billboard_type', 'created_at')
    list_filter = ('created_at', 'billboard__city', 'billboard__ooh_media_type')
    search_fields = ('user__email', 'billboard__city', 'billboard__company_name')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'
    list_per_page = 25
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User Email'
    user_email.admin_order_field = 'user__email'
    
    def billboard_city(self, obj):
        return obj.billboard.city
    billboard_city.short_description = 'Billboard City'
    billboard_city.admin_order_field = 'billboard__city'
    
    def billboard_type(self, obj):
        return obj.billboard.ooh_media_type
    billboard_type.short_description = 'Billboard Type'
    billboard_type.admin_order_field = 'billboard__ooh_media_type'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'billboard')


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'email', 'name', 'phone', 'is_active', 'date_joined', 'billboard_count')
    list_filter = ('is_active', 'is_staff', 'date_joined', 'last_login')
    search_fields = ('email', 'full_name', 'phone')
    readonly_fields = ('date_joined', 'last_login', 'profile_image_preview')
    list_editable = ('is_active',)
    date_hierarchy = 'date_joined'
    list_per_page = 25
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('email', 'full_name', 'phone', 'country_code')
        }),
        ('Profile', {
            'fields': ('profile_image', 'profile_image_preview')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Important Dates', {
            'fields': ('date_joined', 'last_login'),
            'classes': ('collapse',)
        }),
    )
    
    def billboard_count(self, obj):
        """Display number of billboards created by user"""
        count = obj.billboards.count()
        return format_html('<span style="background-color: #4299e1; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px;">{}</span>', count)
    billboard_count.short_description = 'Billboards'
    
    def profile_image_preview(self, obj):
        """Display profile image preview"""
        if obj.profile_image:
            return format_html('<img src="{}" style="max-width: 100px; max-height: 100px; border-radius: 50%;" />', obj.profile_image.url)
        return "No image"
    profile_image_preview.short_description = 'Profile Image'
    
    actions = ['activate_users', 'deactivate_users']
    
    def activate_users(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} users activated.')
    activate_users.short_description = "Activate selected users"
    
    def deactivate_users(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} users deactivated.')
    deactivate_users.short_description = "Deactivate selected users"


# Custom Admin Dashboard
class DashboardAdmin(admin.ModelAdmin):
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('dashboard/', self.admin_site.admin_view(self.dashboard_view), name='dashboard'),
        ]
        return custom_urls + urls
    
    def dashboard_view(self, request):
        """Custom dashboard view with analytics"""
        # Get statistics
        total_billboards = Billboard.objects.count()
        total_users = User.objects.count()
        total_wishlists = Wishlist.objects.count()
        
        # Recent activity
        recent_billboards = Billboard.objects.order_by('-created_at')[:5]
        recent_users = User.objects.order_by('-date_joined')[:5]
        
        # Views analytics
        total_views = Billboard.objects.aggregate(total=Sum('views'))['total'] or 0
        popular_billboards = Billboard.objects.order_by('-views')[:5]
        
        # City distribution
        city_stats = Billboard.objects.values('city').annotate(count=Count('id')).order_by('-count')[:10]
        
        context = {
            'total_billboards': total_billboards,
            'total_users': total_users,
            'total_wishlists': total_wishlists,
            'total_views': total_views,
            'recent_billboards': recent_billboards,
            'recent_users': recent_users,
            'popular_billboards': popular_billboards,
            'city_stats': city_stats,
        }
        
        return render(request, 'admin/dashboard.html', context)


# Register models with custom admin site
admin_site.register(Billboard, BillboardAdmin)
admin_site.register(Wishlist, WishlistAdmin)
admin_site.register(User, UserAdmin)

# Override default admin site
admin.site = admin_site
