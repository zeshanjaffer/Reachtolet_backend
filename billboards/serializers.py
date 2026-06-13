from rest_framework import serializers
from .availability_utils import build_availability_payload, normalize_booked_dates, get_availability_status
from .specifications_utils import normalize_specifications
from .models import Billboard, Wishlist


def _wishlist_ids_for_user(request):
    if not request or not request.user.is_authenticated:
        return frozenset()
    return frozenset(
        Wishlist.objects.filter(user=request.user).values_list('billboard_id', flat=True)
    )


class BillboardPublicSummarySerializer(serializers.ModelSerializer):
    """
    Minimal payload for public list/map endpoints.
    Full billboard data is returned only by GET /api/billboards/{id}/.
    """
    count = serializers.SerializerMethodField()

    class Meta:
        model = Billboard
        fields = ['id', 'latitude', 'longitude', 'count']

    def get_count(self, obj):
        return 1


class BillboardPreviewSerializer(serializers.ModelSerializer):
    """Lightweight payload for map pin preview dialog before full detail."""

    image = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    display_size = serializers.SerializerMethodField()
    views_per_day = serializers.SerializerMethodField()
    availability = serializers.SerializerMethodField()
    lighting = serializers.SerializerMethodField()
    is_in_wishlist = serializers.SerializerMethodField()

    class Meta:
        model = Billboard
        fields = [
            'id',
            'city',
            'road_name',
            'image',
            'price',
            'display_size',
            'views_per_day',
            'availability',
            'lighting',
            'is_in_wishlist',
        ]

    def get_image(self, obj):
        images = obj.images or []
        return images[0] if images else None

    def get_price(self, obj):
        period = (obj.exposure_time or '').strip() or 'per month'
        return {
            'amount': obj.price_range,
            'currency': 'PKR',
            'period': period,
        }

    def get_display_size(self, obj):
        width = obj.display_width
        height = obj.display_height
        if width and height:
            label = f'{width} × {height} meters'
        else:
            label = None
        return {
            'width': width,
            'height': height,
            'unit': 'meters',
            'label': label,
        }

    def get_views_per_day(self, obj):
        return obj.average_daily_views

    def get_availability(self, obj):
        status, label = get_availability_status(obj)
        payload = build_availability_payload(obj)
        return {
            'status': status,
            'label': label,
            'total_booked': payload['total_booked'],
        }

    def get_lighting(self, obj):
        has_lighting = (obj.generator_backup or '').lower() == 'yes'
        return {
            'has_lighting': has_lighting,
            'label': 'Lighting' if has_lighting else 'No lighting',
        }

    def get_is_in_wishlist(self, obj):
        ids = self.context.get('wishlist_billboard_ids')
        if ids is not None:
            return obj.pk in ids
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Wishlist.objects.filter(user=request.user, billboard=obj).exists()
        return False


class SpecificationsJSONField(serializers.JSONField):
    """Accept JSON object or string (multipart form-data) for type-specific billboard data."""

    def to_internal_value(self, data):
        try:
            return normalize_specifications(data)
        except ValueError as exc:
            raise serializers.ValidationError(str(exc)) from exc


class BillboardSerializer(serializers.ModelSerializer):
    # OPTIMIZED: Add user_name field for better performance
    user_name = serializers.CharField(source='user.name', read_only=True)
    
    # Approval workflow fields
    approval_status_display = serializers.CharField(source='get_approval_status_display', read_only=True)
    approved_by_username = serializers.CharField(source='approved_by.username', read_only=True)
    rejected_by_username = serializers.CharField(source='rejected_by.username', read_only=True)
    
    # Wishlist status - check if current user has this billboard in wishlist
    is_in_wishlist = serializers.SerializerMethodField()
    availability = serializers.SerializerMethodField()
    specifications = SpecificationsJSONField(required=False)
    
    class Meta:
        model = Billboard
        fields = [
            'id', 'city', 'description', 'number_of_boards', 'average_daily_views',
            'traffic_direction', 'road_position', 'road_name', 'exposure_time',
            'price_range', 'display_height', 'display_width', 'advertiser_phone',
            'advertiser_whatsapp', 'company_name', 'company_website',
            'ooh_media_type', 'ooh_media_id', 'type', 'images', 'specifications',
            'availability',
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
                           'is_in_wishlist', 'availability')

    def get_availability(self, obj):
        payload = build_availability_payload(obj)
        return {
            'booked_dates': payload['booked_dates'],
            'total_booked': payload['total_booked'],
        }

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
    availability = serializers.SerializerMethodField()
    specifications = SpecificationsJSONField(required=False)
    
    class Meta:
        model = Billboard
        fields = [
            'id', 'city', 'description', 'number_of_boards', 'average_daily_views',
            'traffic_direction', 'road_position', 'road_name', 'exposure_time',
            'price_range', 'display_height', 'display_width', 'advertiser_phone',
            'advertiser_whatsapp', 'company_name', 'company_website',
            'ooh_media_type', 'ooh_media_id', 'type', 'images', 'specifications',
            'availability',
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
                           'is_in_wishlist', 'availability')
    
    def get_availability(self, obj):
        payload = build_availability_payload(obj)
        return {
            'booked_dates': payload['booked_dates'],
            'total_booked': payload['total_booked'],
        }

    def get_is_in_wishlist(self, obj):
        """Check if the current user has this billboard in their wishlist"""
        ids = self.context.get('wishlist_billboard_ids')
        if ids is not None:
            return obj.pk in ids
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Wishlist.objects.filter(user=request.user, billboard=obj).exists()
        return False


class BillboardAvailabilityUpdateSerializer(serializers.Serializer):
    booked_dates = serializers.ListField(
        child=serializers.CharField(),
        allow_empty=True,
        required=True,
    )

    def validate_booked_dates(self, value):
        try:
            return normalize_booked_dates(value)
        except ValueError as exc:
            raise serializers.ValidationError(str(exc)) from exc


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
