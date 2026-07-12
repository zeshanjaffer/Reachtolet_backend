from rest_framework import serializers

from .models import OohMediaType, OohMediaTypeAttribute


class OohMediaTypeAttributeSerializer(serializers.ModelSerializer):
    """Attribute schema shape for Flutter dynamic forms."""

    class Meta:
        model = OohMediaTypeAttribute
        fields = [
            'key',
            'label',
            'field_type',
            'required',
            'order',
            'validation',
            'options',
            'help_text',
        ]


class OohMediaTypeSerializer(serializers.ModelSerializer):
    parent_id = serializers.IntegerField(source='parent_id', read_only=True, allow_null=True)

    class Meta:
        model = OohMediaType
        fields = [
            'id',
            'name',
            'slug',
            'category',
            'parent_id',
            'is_digital',
            'sort_order',
        ]


class OohMediaTypePickerSerializer(serializers.ModelSerializer):
    """Selectable type for create-billboard dropdown (includes active attributes)."""

    attributes = serializers.SerializerMethodField()
    content_type = serializers.SerializerMethodField()
    allows_in_app_media = serializers.SerializerMethodField()
    requires_slot_timing = serializers.SerializerMethodField()
    creative_hint = serializers.SerializerMethodField()

    class Meta:
        model = OohMediaType
        fields = [
            'id',
            'name',
            'slug',
            'category',
            'is_digital',
            'attributes',
            'content_type',
            'allows_in_app_media',
            'requires_slot_timing',
            'creative_hint',
        ]

    def get_attributes(self, obj):
        attrs = getattr(obj, '_prefetched_active_attributes', None)
        if attrs is None:
            attrs = obj.attributes.filter(is_active=True).order_by('order', 'id')
        return OohMediaTypeAttributeSerializer(attrs, many=True).data

    def _booking_caps(self, obj):
        digital = bool(obj.is_digital or obj.category == 'digital')
        return {
            'content_type': 'digital' if digital else 'static',
            'allows_in_app_media': digital,
            'requires_slot_timing': digital,
            'creative_hint': (
                'Upload MP4/JPG and optionally set daypart / duration.'
                if digital
                else 'Poster/print is handled offline. Share install notes with the media owner.'
            ),
        }

    def get_content_type(self, obj):
        return self._booking_caps(obj)['content_type']

    def get_allows_in_app_media(self, obj):
        return self._booking_caps(obj)['allows_in_app_media']

    def get_requires_slot_timing(self, obj):
        return self._booking_caps(obj)['requires_slot_timing']

    def get_creative_hint(self, obj):
        return self._booking_caps(obj)['creative_hint']


class OohMediaTypeGroupedSerializer(serializers.Serializer):
    """Grouped picker response built in the view."""

    key = serializers.CharField()
    label = serializers.CharField()
    types = OohMediaTypePickerSerializer(many=True)


class OohMediaTypeSchemaSerializer(serializers.ModelSerializer):
    """Full type + attributes for GET .../media-types/<id>/schema/."""

    attributes = serializers.SerializerMethodField()

    class Meta:
        model = OohMediaType
        fields = [
            'id',
            'name',
            'slug',
            'category',
            'is_digital',
            'is_selectable',
            'attributes',
        ]

    def get_attributes(self, obj):
        attrs = obj.attributes.filter(is_active=True).order_by('order', 'id')
        return OohMediaTypeAttributeSerializer(attrs, many=True).data
