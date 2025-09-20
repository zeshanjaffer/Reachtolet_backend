from rest_framework import generics, permissions, status
from .models import Billboard, Wishlist, Lead, View
from .serializers import BillboardSerializer, BillboardListSerializer, WishlistSerializer
from .filters import BillboardFilter
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from django.conf import settings
from django.core.files.storage import default_storage
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from core.pagination import CustomPagination
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_cookie
from rest_framework.decorators import api_view
from django.db.models import Prefetch
# WebSocket imports removed
import os
import uuid
import logging

logger = logging.getLogger(__name__)

class BillboardListCreateView(generics.ListCreateAPIView):
    # OPTIMIZED: Enhanced queryset with select_related and only for better performance
    def get_queryset(self):
        return Billboard.objects.filter(is_active=True)\
            .select_related('user')\
            .only(
                'id', 'city', 'description', 'number_of_boards', 'average_daily_views',
                'traffic_direction', 'road_position', 'road_name', 'exposure_time',
                'price_range', 'display_height', 'display_width', 'advertiser_phone',
                'advertiser_whatsapp', 'company_name', 'company_website',
                'ooh_media_type', 'ooh_media_id', 'type', 'images', 'unavailable_dates',
                'latitude', 'longitude', 'views', 'leads', 'is_active', 'created_at',
                'user__id', 'user__name', 'user__email'
            )\
            .order_by('-created_at')
    
    def get_serializer_class(self):
        # Use lightweight serializer for GET requests, full serializer for POST
        if self.request.method == 'GET':
            return BillboardListSerializer
        return BillboardSerializer
    
    permission_classes = [permissions.AllowAny]
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = BillboardFilter  # Use simple filter
    search_fields = ['city', 'description', 'company_name', 'road_name']
    ordering_fields = ['created_at', 'price_range', 'city', 'views']
    ordering = ['-created_at']

    def perform_create(self, serializer):
        user = self.request.user if self.request.user.is_authenticated else None
        billboard = serializer.save(user=user)
        # WebSocket notifications removed

    def notify_new_billboard(self, billboard):
        """WebSocket notifications removed - no longer needed"""
        pass

    @method_decorator(cache_page(60 * 5))  # Cache for 5 minutes
    @method_decorator(vary_on_cookie)
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

class BillboardDetailView(generics.RetrieveUpdateDestroyAPIView):
    # OPTIMIZED: Enhanced queryset for single billboard view
    def get_queryset(self):
        return Billboard.objects.select_related('user')\
            .only(
                'id', 'city', 'description', 'number_of_boards', 'average_daily_views',
                'traffic_direction', 'road_position', 'road_name', 'exposure_time',
                'price_range', 'display_height', 'display_width', 'advertiser_phone',
                'advertiser_whatsapp', 'company_name', 'company_website',
                'ooh_media_type', 'ooh_media_id', 'type', 'images', 'unavailable_dates',
                'latitude', 'longitude', 'views', 'leads', 'is_active', 'created_at',
                'user__id', 'user__name', 'user__email'
            )
    
    serializer_class = BillboardSerializer
    permission_classes = [permissions.AllowAny]

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        # WebSocket notifications removed
        return response

    def destroy(self, request, *args, **kwargs):
        billboard_id = str(self.get_object().id)
        response = super().destroy(request, *args, **kwargs)
        # WebSocket notifications removed
        return response

    def notify_billboard_updated(self, billboard_id, updates):
        """WebSocket notifications removed - no longer needed"""
        pass

    def notify_billboard_deleted(self, billboard_id):
        """WebSocket notifications removed - no longer needed"""
        pass

class MyBillboardsView(generics.ListAPIView):
    serializer_class = BillboardListSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['city', 'ooh_media_type', 'type', 'is_active']  # Added is_active filter
    search_fields = ['city', 'description', 'company_name']
    ordering_fields = ['created_at', 'price_range']
    ordering = ['-created_at']

    def get_queryset(self):
        # OPTIMIZED: Enhanced queryset for user's billboards with ALL fields
        return Billboard.objects.filter(user=self.request.user)\
            .select_related('user')\
            .only(
                'id', 'city', 'description', 'number_of_boards', 'average_daily_views',
                'traffic_direction', 'road_position', 'road_name', 'exposure_time',
                'price_range', 'display_height', 'display_width', 'advertiser_phone',
                'advertiser_whatsapp', 'company_name', 'company_website',
                'ooh_media_type', 'ooh_media_id', 'type', 'images', 'unavailable_dates',
                'latitude', 'longitude', 'views', 'leads', 'is_active', 'created_at',
                'user__id', 'user__name', 'user__email'
            )


class WishlistView(generics.ListCreateAPIView):
    """View for managing user's wishlist"""
    serializer_class = WishlistSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['billboard__city', 'billboard__description', 'billboard__company_name']
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        return Wishlist.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        """Add a billboard to wishlist"""
        billboard_id = request.data.get('billboard_id')
        
        # Check if already in wishlist
        if Wishlist.objects.filter(user=request.user, billboard_id=billboard_id).exists():
            return Response({
                'message': 'Billboard is already in your wishlist'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return super().create(request, *args, **kwargs)


class WishlistRemoveView(APIView):
    """View for removing items from wishlist"""
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, billboard_id):
        try:
            wishlist_item = Wishlist.objects.get(
                user=request.user, 
                billboard_id=billboard_id
            )
            wishlist_item.delete()
            return Response({
                'message': 'Removed from wishlist successfully'
            }, status=status.HTTP_200_OK)
        except Wishlist.DoesNotExist:
            return Response({
                'message': 'Item not found in wishlist'
            }, status=status.HTTP_404_NOT_FOUND)


class WishlistToggleView(APIView):
    """View for toggling wishlist status"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, billboard_id):
        try:
            # Check if already in wishlist
            wishlist_item = Wishlist.objects.filter(
                user=request.user, 
                billboard_id=billboard_id
            ).first()
            
            if wishlist_item:
                # Remove from wishlist
                wishlist_item.delete()
                return Response({
                    'message': 'Removed from wishlist',
                    'in_wishlist': False
                }, status=status.HTTP_200_OK)
            else:
                # Add to wishlist
                billboard = Billboard.objects.get(id=billboard_id)
                Wishlist.objects.create(user=request.user, billboard=billboard)
                return Response({
                    'message': 'Added to wishlist',
                    'in_wishlist': True
                }, status=status.HTTP_201_CREATED)
                
        except Billboard.DoesNotExist:
            return Response({
                'message': 'Billboard not found'
            }, status=status.HTTP_404_NOT_FOUND)


# Updated Lead Tracking View with Duplicate Prevention
@api_view(['POST'])
def track_billboard_lead(request, billboard_id):
    """Track a lead for a specific billboard (phone or WhatsApp) - Only 1 lead per IP per billboard"""
    try:
        billboard = Billboard.objects.get(id=billboard_id)
        
        # Get client IP address
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            user_ip = x_forwarded_for.split(',')[0]
        else:
            user_ip = request.META.get('REMOTE_ADDR')
        
        # Get user agent
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Check if lead already exists for this IP and billboard
        lead_exists = Lead.objects.filter(
            billboard=billboard,
            user_ip=user_ip
        ).exists()
        
        if lead_exists:
            # Lead already exists, don't increment counter
            return Response({
                'message': 'Lead already tracked for this billboard',
                'billboard_id': billboard_id,
                'current_leads': billboard.leads,
                'duplicate': True
            }, status=status.HTTP_200_OK)
        
        # Create new lead record
        Lead.objects.create(
            billboard=billboard,
            user_ip=user_ip,
            user_agent=user_agent
        )
        
        # Increment the leads counter
        billboard.increment_leads()
        
        # WebSocket notifications removed
        
        logger.info(f"New lead tracked for billboard {billboard_id} from IP {user_ip}")
        
        return Response({
            'message': 'Lead tracked successfully',
            'billboard_id': billboard_id,
            'current_leads': billboard.leads,
            'duplicate': False
        }, status=status.HTTP_200_OK)
        
    except Billboard.DoesNotExist:
        return Response({
            'error': 'Billboard not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error tracking lead for billboard {billboard_id}: {str(e)}")
        return Response({
            'error': 'Failed to track lead'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(csrf_exempt, name='dispatch')
class BillboardImageUploadView(APIView):
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, format=None):
        try:
            file_obj = request.FILES.get('image')
            if not file_obj:
                return Response({'detail': 'No image provided.'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Validate file type
            allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/jpg']
            if file_obj.content_type not in allowed_types:
                return Response({'detail': f'Invalid file type: {file_obj.content_type}'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Validate file size (10MB limit)
            max_size = 10 * 1024 * 1024
            if file_obj.size > max_size:
                return Response({'detail': 'File too large. Maximum size is 10MB.'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Generate unique filename
            file_extension = os.path.splitext(file_obj.name)[1] if file_obj.name else '.jpg'
            if not file_extension:
                if file_obj.content_type == 'image/png':
                    file_extension = '.png'
                elif file_obj.content_type in ['image/jpeg', 'image/jpg']:
                    file_extension = '.jpg'
                elif file_obj.content_type == 'image/gif':
                    file_extension = '.gif'
                elif file_obj.content_type == 'image/webp':
                    file_extension = '.webp'
                else:
                    file_extension = '.jpg'
            
            unique_filename = f"{uuid.uuid4().hex}{file_extension}"
            file_path = f'billboards/{unique_filename}'
            
            # Save file
            path = default_storage.save(file_path, file_obj)
            
            # Generate URL
            image_url = request.build_absolute_uri(f'{settings.MEDIA_URL}{path}')
            
            return Response({'url': image_url}, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({'detail': f'Upload failed: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# NEW: Toggle active status endpoint
@api_view(['PATCH'])
def toggle_billboard_active(request, billboard_id):
    """
    Toggle the active status of a billboard
    Only billboard owners can toggle their own billboards
    """
    try:
        # Get the billboard
        billboard = Billboard.objects.get(id=billboard_id)
        
        # Check ownership - only owners can toggle
        if billboard.user != request.user:
            return Response({
                'error': 'You can only toggle your own billboards'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Toggle the active status
        new_status = billboard.toggle_active()
        
        # WebSocket notifications removed
        
        # Prepare response message
        status_message = "active" if new_status else "inactive"
        
        return Response({
            'id': str(billboard.id),
            'is_active': new_status,
            'message': f'Billboard marked as {status_message}'
        }, status=status.HTTP_200_OK)
        
    except Billboard.DoesNotExist:
        return Response({
            'error': 'Billboard not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error toggling billboard {billboard_id} active status: {str(e)}")
        return Response({
            'error': 'Failed to toggle billboard status'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# UPDATED: View tracking endpoint with duplicate prevention
@api_view(['POST'])
def track_billboard_view(request, billboard_id):
    """
    Track a view for a specific billboard
    Excludes views from the billboard owner and prevents duplicates
    """
    try:
        billboard = Billboard.objects.get(id=billboard_id)
        
        # Check if the current user is the billboard owner
        if request.user.is_authenticated and billboard.user == request.user:
            return Response({
                'message': 'View not tracked - owner viewing own billboard',
                'billboard_id': billboard_id,
                'current_views': billboard.views,
                'owner_view': True
            }, status=status.HTTP_200_OK)
        
        # Get client IP address
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            user_ip = x_forwarded_for.split(',')[0]
        else:
            user_ip = request.META.get('REMOTE_ADDR')
        
        # Get user agent
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Check if view already exists for this IP and billboard
        view_exists = View.objects.filter(
            billboard=billboard,
            user_ip=user_ip
        ).exists()
        
        if view_exists:
            # View already exists, don't increment counter
            return Response({
                'message': 'View already tracked for this billboard',
                'billboard_id': billboard_id,
                'current_views': billboard.views,
                'owner_view': False,
                'duplicate': True
            }, status=status.HTTP_200_OK)
        
        # Create new view record
        View.objects.create(
            billboard=billboard,
            user_ip=user_ip,
            user_agent=user_agent
        )
        
        # Increment the views counter
        billboard.increment_views()
        
        # WebSocket notifications removed
        
        logger.info(f"New view tracked for billboard {billboard_id} from IP {user_ip}")
        
        return Response({
            'message': 'View tracked successfully',
            'billboard_id': billboard_id,
            'current_views': billboard.views,
            'owner_view': False,
            'duplicate': False
        }, status=status.HTTP_200_OK)
        
    except Billboard.DoesNotExist:
        return Response({
            'error': 'Billboard not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error tracking view for billboard {billboard_id}: {str(e)}")
        return Response({
            'error': 'Failed to track view'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class HealthCheckView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, format=None):
        from datetime import datetime
        return Response({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'message': 'Backend is running'
        }, status=status.HTTP_200_OK)