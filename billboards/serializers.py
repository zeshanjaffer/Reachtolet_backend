from rest_framework import serializers
from .models import Billboard, Wishlist

class BillboardSerializer(serializers.ModelSerializer):
    # OPTIMIZED: Add user_name field for better performance
    user_name = serializers.CharField(source='user.name', read_only=True)
    
    class Meta:
        model = Billboard
        fields = [
            'id', 'city', 'description', 'number_of_boards', 'average_daily_views',
            'traffic_direction', 'road_position', 'road_name', 'exposure_time',
            'price_range', 'display_height', 'display_width', 'advertiser_phone',
            'advertiser_whatsapp', 'company_name', 'company_website',
            'ooh_media_type', 'ooh_media_id', 'type', 'images', 'unavailable_dates',
            'latitude', 'longitude', 'views', 'leads', 'is_active', 'address',
            'generator_backup', 'created_at', 'user_name'
        ]
        read_only_fields = ('user', 'views', 'leads', 'created_at', 'is_active', 'user_name')

    def create(self, validated_data):
        # Set the user from the request
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class BillboardListSerializer(serializers.ModelSerializer):
    # OPTIMIZED: Lightweight serializer for list views with ALL fields
    user_name = serializers.CharField(source='user.name', read_only=True)
    
    class Meta:
        model = Billboard
        fields = [
            'id', 'city', 'description', 'number_of_boards', 'average_daily_views',
            'traffic_direction', 'road_position', 'road_name', 'exposure_time',
            'price_range', 'display_height', 'display_width', 'advertiser_phone',
            'advertiser_whatsapp', 'company_name', 'company_website',
            'ooh_media_type', 'ooh_media_id', 'type', 'images', 'unavailable_dates',
            'latitude', 'longitude', 'views', 'leads', 'is_active', 'address',
            'generator_backup', 'created_at', 'user_name'
        ]
        read_only_fields = ('user', 'views', 'leads', 'created_at', 'is_active', 'user_name')


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
