from rest_framework import serializers
from .models import Billboard, Wishlist


def _wishlist_ids_for_user(request):
    if not request or not request.user.is_authenticated:
        return frozenset()
    return frozenset(
        Wishlist.objects.filter(user=request.user).values_list('billboard_id', flat=True)
    )


class BillboardPublicSummarySerializer(serializers.ModelSerializer):
    """
    Minimal payload for public list/map endpoints — fewer columns and no N+1 wishlist queries.
    """
    name = serializers.CharField(source='company_name', read_only=True)
    price = serializers.CharField(source='price_range', read_only=True)
    image = serializers.SerializerMethodField()
    availability = serializers.SerializerMethodField()
    is_in_wishlist = serializers.SerializerMethodField()

    class Meta:
        model = Billboard
        fields = [
            'id',
            'name',
            'description',
            'price',
            'availability',
            'city',
            'address',
            'image',
            'latitude',
            'longitude',
            'type',
            'ooh_media_type',
            'is_in_wishlist',
        ]

    def get_image(self, obj):
        images = obj.images or []
        if isinstance(images, list) and len(images) > 0:
            return images[0]
        return None

    def get_availability(self, obj):
        return {
            'is_active': obj.is_active,
            'unavailable_dates': obj.unavailable_dates or [],
        }

    def get_is_in_wishlist(self, obj):
        ids = self.context.get('wishlist_billboard_ids')
        if ids is not None:
            return obj.pk in ids
        return obj.pk in _wishlist_ids_for_user(self.context.get('request'))


class BillboardSerializer(serializers.ModelSerializer):
    # OPTIMIZED: Add user_name field for better performance
    user_name = serializers.CharField(source='user.name', read_only=True)
    
    # Approval workflow fields
    approval_status_display = serializers.CharField(source='get_approval_status_display', read_only=True)
    approved_by_username = serializers.CharField(source='approved_by.username', read_only=True)
    rejected_by_username = serializers.CharField(source='rejected_by.username', read_only=True)
    
    # Wishlist status - check if current user has this billboard in wishlist
    is_in_wishlist = serializers.SerializerMethodField()
    
    class Meta:
        model = Billboard
        fields = [
            'id', 'city', 'description', 'number_of_boards', 'average_daily_views',
            'traffic_direction', 'road_position', 'road_name', 'exposure_time',
            'price_range', 'display_height', 'display_width', 'advertiser_phone',
            'advertiser_whatsapp', 'company_name', 'company_website',
            'ooh_media_type', 'ooh_media_id', 'type', 'images', 'unavailable_dates',
            'latitude', 'longitude', 'views', 'leads', 'is_active', 'address',
            'generator_backup', 'created_at', 'user_name',
            # Approval workflow fields
            'approval_status', 'approval_status_display', 'approved_at', 'rejected_at',
            'rejection_reason', 'approved_by_username', 'rejected_by_username',
            # Wishlist status
            'is_in_wishlist'
        ]
        read_only_fields = ('user', 'views', 'leads', 'created_at', 'is_active', 'user_name', 
                           'approved_at', 'rejected_at', 'approved_by', 'rejected_by', 
                           'approval_status_display', 'approved_by_username', 'rejected_by_username',
                           'is_in_wishlist')

    def get_is_in_wishlist(self, obj):
        """Check if the current user has this billboard in their wishlist"""
        ids = self.context.get('wishlist_billboard_ids')
        if ids is not None:
            return obj.pk in ids
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Wishlist.objects.filter(user=request.user, billboard=obj).exists()
        return False

    def create(self, validated_data):
        # Set the user from the request
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class BillboardListSerializer(serializers.ModelSerializer):
    # OPTIMIZED: Lightweight serializer for list views with ALL fields
    user_name = serializers.CharField(source='user.name', read_only=True)
    
    # Approval workflow fields
    approval_status_display = serializers.CharField(source='get_approval_status_display', read_only=True)
    approved_by_username = serializers.CharField(source='approved_by.username', read_only=True)
    rejected_by_username = serializers.CharField(source='rejected_by.username', read_only=True)
    
    # Wishlist status - check if current user has this billboard in wishlist
    is_in_wishlist = serializers.SerializerMethodField()
    
    class Meta:
        model = Billboard
        fields = [
            'id', 'city', 'description', 'number_of_boards', 'average_daily_views',
            'traffic_direction', 'road_position', 'road_name', 'exposure_time',
            'price_range', 'display_height', 'display_width', 'advertiser_phone',
            'advertiser_whatsapp', 'company_name', 'company_website',
            'ooh_media_type', 'ooh_media_id', 'type', 'images', 'unavailable_dates',
            'latitude', 'longitude', 'views', 'leads', 'is_active', 'address',
            'generator_backup', 'created_at', 'user_name',
            # Approval workflow fields
            'approval_status', 'approval_status_display', 'approved_at', 'rejected_at',
            'rejection_reason', 'approved_by_username', 'rejected_by_username',
            # Wishlist status
            'is_in_wishlist'
        ]
        read_only_fields = ('user', 'views', 'leads', 'created_at', 'is_active', 'user_name',
                           'approved_at', 'rejected_at', 'approved_by', 'rejected_by',
                           'approval_status_display', 'approved_by_username', 'rejected_by_username',
                           'is_in_wishlist')
    
    def get_is_in_wishlist(self, obj):
        """Check if the current user has this billboard in their wishlist"""
        ids = self.context.get('wishlist_billboard_ids')
        if ids is not None:
            return obj.pk in ids
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Wishlist.objects.filter(user=request.user, billboard=obj).exists()
        return False


class WishlistSerializer(serializers.ModelSerializer):
    billboard = BillboardSerializer(read_only=True)
    billboard_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Wishlist
        fields = ['id', 'billboard', 'billboard_id', 'created_at']
        read_only_fields = ('user', 'created_at')

    def create(self, validated_data):
        # Set the user from the request
        validated_data['user'] = self.context['request'].user
        
        # Get billboard_id and set billboard object
        billboard_id = validated_data.pop('billboard_id')
        validated_data['billboard'] = Billboard.objects.get(id=billboard_id)
        
        return super().create(validated_data)

    def validate_billboard_id(self, value):
        """Validate that the billboard exists"""
        try:
            Billboard.objects.get(id=value)
        except Billboard.DoesNotExist:
            raise serializers.ValidationError("Billboard does not exist")
        return value
