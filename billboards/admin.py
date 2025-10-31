from django.contrib import admin
from django.utils import timezone
from .models import Billboard, Wishlist, Lead, View

@admin.register(Billboard)
class BillboardAdmin(admin.ModelAdmin):
    # Main list display with all important fields
    list_display = (
        'id', 'get_user_email', 'ooh_media_id', 'city', 'ooh_media_type', 'type', 'company_name', 
        'price_range', 'road_name', 'number_of_boards', 'views', 'leads', 'is_active', 
        'approval_status', 'approved_at', 'approved_by', 'address', 'generator_backup', 'created_at'
    )
    
    def get_user_email(self, obj):
        return obj.user.email if obj.user else '-'
    get_user_email.short_description = 'Email'
    get_user_email.admin_order_field = 'user__email'
    
    # Search functionality
    search_fields = (
        'city', 'ooh_media_type', 'company_name', 'road_name', 
        'description', 'advertiser_phone', 'advertiser_whatsapp', 'address'
    )
    
    # Filters for easy data management
    list_filter = (
        'city', 'ooh_media_type', 'type', 'is_active', 'approval_status', 'generator_backup', 'created_at',
        ('user', admin.RelatedOnlyFieldListFilter),
    )
    
    # Fields to display in detail view
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'city', 'description', 'company_name', 'company_website')
        }),
        ('Media Details', {
            'fields': ('ooh_media_type', 'ooh_media_id', 'type', 'number_of_boards')
        }),
        ('Location & Traffic', {
            'fields': ('road_name', 'road_position', 'traffic_direction', 'latitude', 'longitude', 'address')
        }),
        ('Pricing & Performance', {
            'fields': ('price_range', 'average_daily_views', 'exposure_time', 'views', 'leads', 'is_active', 'generator_backup')
        }),
        ('Contact Information', {
            'fields': ('advertiser_phone', 'advertiser_whatsapp')
        }),
        ('Media & Dates', {
            'fields': ('images', 'unavailable_dates', 'display_height', 'display_width')
        }),
        ('Approval Status', {
            'fields': (
                'approval_status', 'approved_at', 'approved_by',
                'rejected_at', 'rejected_by', 'rejection_reason'
            )
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    # Read-only fields
    readonly_fields = ('views', 'leads', 'created_at', 'approved_at', 'rejected_at')
    
    # List per page
    list_per_page = 25
    
    # Ordering
    ordering = ('-created_at',)
    
    # Date hierarchy
    date_hierarchy = 'created_at'
    
    # Actions
    actions = ['mark_as_lighting', 'mark_as_non_lighting', 'reset_views', 'reset_leads', 'activate_billboards', 'deactivate_billboards', 'approve_billboards', 'reject_billboards']
    
    def mark_as_lighting(self, request, queryset):
        updated = queryset.update(type='Lighting')
        self.message_user(request, f'{updated} billboards marked as Lighting.')
    mark_as_lighting.short_description = "Mark selected billboards as Lighting"
    
    def mark_as_non_lighting(self, request, queryset):
        updated = queryset.update(type='Non-Lighting')
        self.message_user(request, f'{updated} billboards marked as Non-Lighting.')
    mark_as_non_lighting.short_description = "Mark selected billboards as Non-Lighting"
    
    # NEW: Action to reset view counts
    def reset_views(self, request, queryset):
        updated = queryset.update(views=0)
        self.message_user(request, f'View count reset to 0 for {updated} billboards.')
    reset_views.short_description = "Reset view count to 0 for selected billboards"
    
    # NEW: Action to reset lead counts
    def reset_leads(self, request, queryset):
        updated = queryset.update(leads=0)
        self.message_user(request, f'Lead counts reset to 0 for {updated} billboards.')
    reset_leads.short_description = "Reset lead counts to 0 for selected billboards"
    
    # NEW: Action to activate billboards
    def activate_billboards(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} billboards activated successfully.')
    activate_billboards.short_description = "Activate selected billboards"
    
    # NEW: Action to deactivate billboards
    def deactivate_billboards(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} billboards deactivated successfully.')
    deactivate_billboards.short_description = "Deactivate selected billboards"
    
    # NEW: Action to approve billboards
    def approve_billboards(self, request, queryset):
        updated = queryset.filter(approval_status='pending').update(
            approval_status='approved',
            approved_at=timezone.now(),
            approved_by=request.user
        )
        self.message_user(request, f'{updated} billboards approved successfully.')
    approve_billboards.short_description = "Approve selected pending billboards"
    
    # NEW: Action to reject billboards
    def reject_billboards(self, request, queryset):
        updated = queryset.filter(approval_status='pending').update(
            approval_status='rejected',
            rejected_at=timezone.now(),
            rejected_by=request.user,
            rejection_reason='Bulk rejection by admin'
        )
        self.message_user(request, f'{updated} billboards rejected successfully.')
    reject_billboards.short_description = "Reject selected pending billboards"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


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


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'billboard_city', 'billboard_company', 'user_ip', 'created_at'
    )
    list_filter = (
        'created_at', 'billboard__city', 'billboard__ooh_media_type',
        ('billboard', admin.RelatedOnlyFieldListFilter),
    )
    search_fields = (
        'billboard__city', 'billboard__company_name', 'user_ip', 'user_agent'
    )
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'
    list_per_page = 50
    ordering = ('-created_at',)
    
    # Fieldsets for detail view
    fieldsets = (
        ('Lead Information', {
            'fields': ('billboard', 'user_ip', 'user_agent')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def billboard_city(self, obj):
        return obj.billboard.city
    billboard_city.short_description = 'City'
    billboard_city.admin_order_field = 'billboard__city'
    
    def billboard_company(self, obj):
        return obj.billboard.company_name
    billboard_company.short_description = 'Company'
    billboard_company.admin_order_field = 'billboard__company_name'
    
    # Actions
    actions = ['export_leads_csv', 'delete_old_leads']
    
    def export_leads_csv(self, request, queryset):
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="leads_export.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'ID', 'Billboard City', 'Billboard Company', 'User IP', 'Created At'
        ])
        
        for lead in queryset.select_related('billboard'):
            writer.writerow([
                lead.id,
                lead.billboard.city,
                lead.billboard.company_name,
                lead.user_ip,
                lead.created_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
        
        return response
    export_leads_csv.short_description = "Export selected leads to CSV"
    
    def delete_old_leads(self, request, queryset):
        from django.utils import timezone
        from datetime import timedelta
        
        # Delete leads older than 90 days
        cutoff_date = timezone.now() - timedelta(days=90)
        old_leads = queryset.filter(created_at__lt=cutoff_date)
        count = old_leads.count()
        old_leads.delete()
        
        self.message_user(request, f'{count} leads older than 90 days have been deleted.')
    delete_old_leads.short_description = "Delete leads older than 90 days"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('billboard')


@admin.register(View)
class ViewAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'billboard_city', 'billboard_company', 'user_ip', 'created_at'
    )
    list_filter = (
        'created_at', 'billboard__city', 'billboard__ooh_media_type',
        ('billboard', admin.RelatedOnlyFieldListFilter),
    )
    search_fields = (
        'billboard__city', 'billboard__company_name', 'user_ip', 'user_agent'
    )
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'
    list_per_page = 50
    ordering = ('-created_at',)
    
    # Fieldsets for detail view
    fieldsets = (
        ('View Information', {
            'fields': ('billboard', 'user_ip', 'user_agent')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def billboard_city(self, obj):
        return obj.billboard.city
    billboard_city.short_description = 'City'
    billboard_city.admin_order_field = 'billboard__city'
    
    def billboard_company(self, obj):
        return obj.billboard.company_name
    billboard_company.short_description = 'Company'
    billboard_company.admin_order_field = 'billboard__company_name'
    
    # Actions
    actions = ['export_views_csv', 'delete_old_views']
    
    def export_views_csv(self, request, queryset):
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="views_export.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'ID', 'Billboard City', 'Billboard Company', 'User IP', 'Created At'
        ])
        
        for view in queryset.select_related('billboard'):
            writer.writerow([
                view.id,
                view.billboard.city,
                view.billboard.company_name,
                view.user_ip,
                view.created_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
        
        return response
    export_views_csv.short_description = "Export selected views to CSV"
    
    def delete_old_views(self, request, queryset):
        from django.utils import timezone
        from datetime import timedelta
        
        # Delete views older than 90 days
        cutoff_date = timezone.now() - timedelta(days=90)
        old_views = queryset.filter(created_at__lt=cutoff_date)
        count = old_views.count()
        old_views.delete()
        
        self.message_user(request, f'{count} views older than 90 days have been deleted.')
    delete_old_views.short_description = "Delete views older than 90 days"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('billboard')