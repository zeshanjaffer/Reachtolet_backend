from django.db import models
from django.conf import settings

class Billboard(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='billboards', null=True, blank=True
    )
    city = models.CharField(max_length=100, db_index=True)  # Added index for filtering
    description = models.TextField(blank=True, null=True)
    number_of_boards = models.CharField(max_length=10, blank=True, null=True)
    average_daily_views = models.CharField(max_length=20, blank=True, null=True)
    traffic_direction = models.CharField(max_length=100, blank=True, null=True)
    road_position = models.CharField(max_length=100, blank=True, null=True)
    road_name = models.CharField(max_length=100, blank=True, null=True)
    exposure_time = models.CharField(max_length=100, blank=True, null=True)
    price_range = models.CharField(max_length=100, blank=True, null=True)
    display_height = models.CharField(max_length=20, blank=True, null=True)
    display_width = models.CharField(max_length=20, blank=True, null=True)
    advertiser_phone = models.CharField(max_length=20, blank=True, null=True)
    advertiser_whatsapp = models.CharField(max_length=100, blank=True, null=True)
    company_name = models.CharField(max_length=100, blank=True, null=True, db_index=True)  # Added index for filtering
    company_website = models.CharField(max_length=200, blank=True, null=True)  # Changed from URLField to CharField
    ooh_media_type = models.CharField(max_length=100, db_index=True)  # Added index for filtering
    ooh_media_id = models.CharField(max_length=100, blank=True, null=True)
    type = models.CharField(max_length=50, db_index=True)  # Added index for filtering
    images = models.JSONField(default=list, blank=True)  # List of image URLs
    unavailable_dates = models.JSONField(default=list, blank=True)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    views = models.IntegerField(default=0)  # NEW: View count field
    leads = models.IntegerField(default=0, db_index=True)  # NEW: Simple leads counter
    is_active = models.BooleanField(default=True, db_index=True)  # NEW: Active/inactive toggle with index
    address = models.TextField(blank=True, null=True, help_text="Detailed address of the billboard location")
    generator_backup = models.CharField(
        max_length=3, 
        choices=[('Yes', 'Yes'), ('No', 'No')], 
        blank=True, 
        null=True,
        help_text="Whether the billboard has generator backup"
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)  # Added index for ordering

    def __str__(self):
        return f"{self.city} - {self.ooh_media_type}"

    def increment_views(self):
        """Increment the view count for this billboard"""
        self.views += 1
        self.save(update_fields=['views'])
    
    def increment_leads(self):
        """Increment the leads count for this billboard"""
        self.leads += 1
        self.save(update_fields=['leads'])
    
    def toggle_active(self):
        """Toggle the active status of the billboard"""
        self.is_active = not self.is_active
        self.save(update_fields=['is_active'])
        return self.is_active

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_active', 'created_at']),  # Composite index for common query
            models.Index(fields=['user', 'is_active']),  # Composite index for user's billboards
            models.Index(fields=['city', 'is_active']),  # Composite index for city filtering
            models.Index(fields=['leads']),  # Index for lead analytics
        ]


class Wishlist(models.Model):
    """Model to track user's saved billboards"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wishlist_items'
    )
    billboard = models.ForeignKey(
        Billboard, on_delete=models.CASCADE, related_name='wishlisted_by'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'billboard']  # Prevent duplicate entries
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} - {self.billboard.city}"


class Lead(models.Model):
    """Model to track individual lead interactions per user per billboard"""
    billboard = models.ForeignKey(
        Billboard, on_delete=models.CASCADE, related_name='lead_interactions'
    )
    user_ip = models.GenericIPAddressField(
        null=True, 
        blank=True,
        help_text="IP address of the user"
    )
    user_agent = models.TextField(
        blank=True, 
        null=True,
        help_text="Browser/device information"
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['billboard', 'user_ip']),
            models.Index(fields=['user_ip', 'created_at']),
        ]
        # Prevent duplicate leads from same IP for same billboard
        unique_together = ['billboard', 'user_ip']

    def __str__(self):
        return f"{self.billboard.city} - Lead from {self.user_ip} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"


class View(models.Model):
    """Model to track individual view interactions per user per billboard"""
    billboard = models.ForeignKey(
        Billboard, on_delete=models.CASCADE, related_name='view_interactions'
    )
    user_ip = models.GenericIPAddressField(
        null=True, 
        blank=True,
        help_text="IP address of the user"
    )
    user_agent = models.TextField(
        blank=True, 
        null=True,
        help_text="Browser/device information"
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['billboard', 'user_ip']),
            models.Index(fields=['user_ip', 'created_at']),
        ]
        # Prevent duplicate views from same IP for same billboard
        unique_together = ['billboard', 'user_ip']

    def __str__(self):
        return f"{self.billboard.city} - View from {self.user_ip} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"