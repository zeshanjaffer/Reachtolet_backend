from rest_framework import serializers

from .models import OohMediaType


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
    """Selectable type for create-billboard dropdown."""

    class Meta:
        model = OohMediaType
        fields = ['id', 'name', 'slug', 'category', 'is_digital']


class OohMediaTypeGroupedSerializer(serializers.Serializer):
    """Grouped picker response built in the view."""

    key = serializers.CharField()
    label = serializers.CharField()
    types = OohMediaTypePickerSerializer(many=True)
