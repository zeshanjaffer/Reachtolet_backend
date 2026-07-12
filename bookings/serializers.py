from rest_framework import serializers

from .models import Booking, BookingContent, Payment
from .services import content_capabilities


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['id', 'amount', 'currency', 'status', 'gateway_ref', 'created_at', 'updated_at']
        read_only_fields = fields


class BookingContentSerializer(serializers.ModelSerializer):
    media_file_url = serializers.SerializerMethodField()

    class Meta:
        model = BookingContent
        fields = [
            'id',
            'content_type',
            'status',
            'video_url',
            'media_file_url',
            'slot_daypart',
            'duration_seconds',
            'digital_notes',
            'install_notes',
            'install_confirmed_by_owner',
            'external_link',
            'owner_feedback',
            'submitted_at',
            'reviewed_at',
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields

    def get_media_file_url(self, obj):
        if not obj.media_file:
            return None
        request = self.context.get('request')
        url = obj.media_file.url
        if request:
            return request.build_absolute_uri(url)
        return url


class BillboardMiniSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    city = serializers.CharField(allow_null=True)
    road_name = serializers.CharField(allow_null=True)
    ooh_media_type = serializers.CharField(allow_null=True)
    currency = serializers.CharField(allow_null=True)
    image = serializers.SerializerMethodField()
    content_capabilities = serializers.SerializerMethodField()

    def get_image(self, obj):
        images = obj.images or []
        return images[0] if images else None

    def get_content_capabilities(self, obj):
        return content_capabilities(obj)


class UserMiniSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    email = serializers.EmailField()
    full_name = serializers.CharField(allow_null=True)
    user_type = serializers.CharField()


class BookingSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    billboard = serializers.SerializerMethodField()
    advertiser = serializers.SerializerMethodField()
    media_owner = serializers.SerializerMethodField()
    content = serializers.SerializerMethodField()
    payment = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = [
            'id',
            'billboard_id',
            'billboard',
            'advertiser_id',
            'advertiser',
            'media_owner_id',
            'media_owner',
            'start_date',
            'end_date',
            'status',
            'status_display',
            'total_price',
            'currency',
            'advertiser_message',
            'rejection_reason',
            'owner_note',
            'expires_at',
            'content',
            'payment',
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields

    def get_billboard(self, obj):
        return BillboardMiniSerializer(obj.billboard, context=self.context).data

    def get_advertiser(self, obj):
        u = obj.advertiser
        return {
            'id': u.id,
            'email': u.email,
            'full_name': u.full_name,
            'user_type': u.user_type,
        }

    def get_media_owner(self, obj):
        u = obj.media_owner
        return {
            'id': u.id,
            'email': u.email,
            'full_name': u.full_name,
            'user_type': u.user_type,
        }

    def get_content(self, obj):
        content = getattr(obj, 'content', None)
        if content is None:
            return None
        return BookingContentSerializer(content, context=self.context).data

    def get_payment(self, obj):
        payment = getattr(obj, 'payment', None)
        if payment is None:
            return None
        return PaymentSerializer(payment).data


class BookingCreateSerializer(serializers.Serializer):
    billboard_id = serializers.IntegerField()
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    message = serializers.CharField(required=False, allow_blank=True, default='')


class BookingRejectSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True, default='')


class BookingAcceptSerializer(serializers.Serializer):
    owner_note = serializers.CharField(required=False, allow_blank=True, default='')


class ContentRejectSerializer(serializers.Serializer):
    feedback = serializers.CharField(required=False, allow_blank=True, default='')


class ContentApproveSerializer(serializers.Serializer):
    install_confirmed = serializers.BooleanField(required=False, default=False)
