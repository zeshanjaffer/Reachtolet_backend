from rest_framework import serializers
from .availability_utils import build_availability_payload, normalize_booked_dates, get_availability_status
from .specifications_utils import normalize_specifications
from .models import Billboard, Wishlist, OohMediaType


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
    media_type_id = serializers.PrimaryKeyRelatedField(
        queryset=OohMediaType.objects.filter(is_active=True, is_selectable=True),
        source='media_type',
        write_only=True,
        required=False,
    )
    media_type_detail = serializers.SerializerMethodField()
    
    class Meta:
        model = Billboard
        fields = [
            'id', 'city', 'description', 'number_of_boards', 'average_daily_views',
            'traffic_direction', 'road_position', 'road_name', 'exposure_time',
            'price_range', 'display_height', 'display_width', 'advertiser_phone',
            'advertiser_whatsapp', 'company_name', 'company_website',
            'ooh_media_type', 'media_type_id', 'media_type_detail', 'ooh_media_id', 'type',
            'images', 'specifications',
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
                           'ooh_media_type', 'media_type_detail',
                           'approved_at', 'rejected_at', 'approved_by', 'rejected_by',
                           'approval_status_display', 'approved_by_username', 'rejected_by_username',
                           'is_in_wishlist', 'availability')

    def get_media_type_detail(self, obj):
        if not obj.media_type_id:
            return None
        mt = obj.media_type
        return {
            'id': mt.id,
            'name': mt.name,
            'slug': mt.slug,
            'category': mt.category,
            'is_digital': mt.is_digital,
        }

    def validate(self, attrs):
        media_type = attrs.get('media_type')
        ooh_media_type = self.initial_data.get('ooh_media_type') if hasattr(self, 'initial_data') else None
        if not media_type and not ooh_media_type and self.instance is None:
            raise serializers.ValidationError({
                'media_type_id': 'This field is required. Pick a type from GET /api/billboards/media-types/.',
            })
        if media_type and not media_type.is_selectable:
            raise serializers.ValidationError({
                'media_type_id': f'"{media_type.name}" is a group header, not a selectable media type.',
            })
        return attrs

    def create(self, validated_data):
        if 'media_type' not in validated_data and self.initial_data.get('ooh_media_type'):
            name = str(self.initial_data.get('ooh_media_type')).strip()
            mt = OohMediaType.objects.filter(name__iexact=name, is_active=True).first()
            if mt:
                validated_data['media_type'] = mt
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if 'media_type' not in validated_data and self.initial_data.get('ooh_media_type'):
            name = str(self.initial_data.get('ooh_media_type')).strip()
            mt = OohMediaType.objects.filter(name__iexact=name, is_active=True, is_selectable=True).first()
            if mt:
                validated_data['media_type'] = mt
        return super().update(instance, validated_data)

    def get_availability(self, obj):
        payload = build_availability_payload(obj)
        return {
            'booked_dates': payload['booked_dates'],
            'total_booked': payload['total_booked'],
        }

    def get_is_in_wishlist(self, obj):
        ids = self.context.get('wishlist_billboard_ids')
        if ids is not None:
            return obj.pk in ids
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Wishlist.objects.filter(user=request.user, billboard=obj).exists()
        return False


class BillboardDetailSerializer(BillboardSerializer):
    """Public advertiser detail read — excludes owner analytics (views, leads)."""

    class Meta(BillboardSerializer.Meta):
        fields = [
            f for f in BillboardSerializer.Meta.fields
            if f not in ('views', 'leads')
        ]
        read_only_fields = tuple(
            f for f in BillboardSerializer.Meta.read_only_fields
            if f not in ('views', 'leads')
        )


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
    media_type_detail = serializers.SerializerMethodField()
    
    class Meta:
        model = Billboard
        fields = [
            'id', 'city', 'description', 'number_of_boards', 'average_daily_views',
            'traffic_direction', 'road_position', 'road_name', 'exposure_time',
            'price_range', 'display_height', 'display_width', 'advertiser_phone',
            'advertiser_whatsapp', 'company_name', 'company_website',
            'ooh_media_type', 'media_type_detail', 'ooh_media_id', 'type', 'images', 'specifications',
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

    def get_media_type_detail(self, obj):
        if not obj.media_type_id:
            return None
        mt = obj.media_type
        return {
            'id': mt.id,
            'name': mt.name,
            'slug': mt.slug,
            'category': mt.category,
            'is_digital': mt.is_digital,
        }
    
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


APPROVAL_STATUS_CHOICES = ('pending', 'approved', 'rejected')


class MyBillboardsListRequestSerializer(serializers.Serializer):
    """POST body for /my-billboards/ (pending / approved / rejected tabs)."""

    approval_status = serializers.ChoiceField(choices=APPROVAL_STATUS_CHOICES)
    page = serializers.IntegerField(min_value=1, default=1, required=False)
    page_size = serializers.IntegerField(min_value=1, max_value=100, default=20, required=False)
    search = serializers.CharField(required=False, allow_blank=True, default='')
    city = serializers.CharField(required=False, allow_blank=True, default='')
    media_type_id = serializers.IntegerField(required=False, allow_null=True, default=None)
    type = serializers.CharField(required=False, allow_blank=True, default='')
    is_active = serializers.BooleanField(required=False, allow_null=True, default=None)
    ordering = serializers.CharField(required=False, default='-created_at')

    def validate_ordering(self, value):
        field = value.lstrip('-')
        if field not in ('created_at', 'price_range'):
            raise serializers.ValidationError(
                'ordering must be created_at, -created_at, price_range, or -price_range'
            )
        return value


class BillboardOwnerTileSerializer(serializers.ModelSerializer):
    """Lightweight tile payload for media-owner approval tabs."""

    approval_status_display = serializers.CharField(
        source='get_approval_status_display', read_only=True,
    )
    image = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    display_size = serializers.SerializerMethodField()
    media_type_name = serializers.SerializerMethodField()
    subtitle = serializers.SerializerMethodField()

    class Meta:
        model = Billboard
        fields = [
            'id', 'city', 'road_name', 'image', 'price', 'display_size',
            'media_type_name', 'approval_status', 'approval_status_display',
            'is_active', 'created_at', 'subtitle',
            'views', 'leads', 'approved_at',
            'rejection_reason', 'rejected_at',
        ]
        read_only_fields = fields

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
        return {'label': label}

    def get_media_type_name(self, obj):
        if obj.media_type_id:
            return obj.media_type.name
        return obj.ooh_media_type or None

    def get_subtitle(self, obj):
        if obj.approval_status == 'pending':
            return 'Awaiting admin approval'
        if obj.approval_status == 'rejected' and obj.rejection_reason:
            reason = obj.rejection_reason.strip()
            return reason[:120] + ('…' if len(reason) > 120 else '')
        return None

    def to_representation(self, instance):
        data = super().to_representation(instance)
        status = instance.approval_status

        if status == 'pending':
            for key in ('views', 'leads', 'approved_at', 'rejection_reason', 'rejected_at'):
                data.pop(key, None)
        elif status == 'approved':
            for key in ('rejection_reason', 'rejected_at', 'subtitle'):
                if data.get(key) is None:
                    data.pop(key, None)
        elif status == 'rejected':
            for key in ('views', 'leads', 'approved_at'):
                data.pop(key, None)

        return {k: v for k, v in data.items() if v is not None or k in (
            'id', 'approval_status', 'approval_status_display', 'is_active', 'created_at',
            'image', 'price', 'display_size', 'media_type_name', 'city', 'road_name',
        )}


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
    billboard = BillboardDetailSerializer(read_only=True)
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
