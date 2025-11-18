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
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.db.models import Prefetch
from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
# WebSocket imports removed
import os
import uuid
import logging

logger = logging.getLogger(__name__)

class BillboardListCreateView(generics.ListCreateAPIView):
    # OPTIMIZED: Enhanced queryset with select_related and only for better performance
    def get_queryset(self):
        # Only show approved and active billboards for public map
        return Billboard.objects.filter(
            is_active=True, 
            approval_status='approved'
        )\
            .select_related('user')\
            .only(
                'id', 'city', 'description', 'number_of_boards', 'average_daily_views',
                'traffic_direction', 'road_position', 'road_name', 'exposure_time',
                'price_range', 'display_height', 'display_width', 'advertiser_phone',
                'advertiser_whatsapp', 'company_name', 'company_website',
                'ooh_media_type', 'ooh_media_id', 'type', 'images', 'unavailable_dates',
                'latitude', 'longitude', 'views', 'leads', 'is_active', 'created_at',
                'user__id', 'user__name', 'user__email', 'approval_status'
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

    def paginate_queryset(self, queryset):
        """
        Disable pagination when map bounds are provided (for map views).
        Map views need all billboards in the visible area, not paginated results.
        """
        # Check if map bounds are provided
        ne_lat = self.request.query_params.get('ne_lat')
        ne_lng = self.request.query_params.get('ne_lng')
        sw_lat = self.request.query_params.get('sw_lat')
        sw_lng = self.request.query_params.get('sw_lng')
        
        # If map bounds are provided, disable pagination (return all results)
        if ne_lat and ne_lng and sw_lat and sw_lng:
            return None  # No pagination for map views
        
        # Otherwise, use normal pagination for list views
        return super().paginate_queryset(queryset)

    def list(self, request, *args, **kwargs):
        """
        Override list to handle non-paginated responses for map views.
        """
        queryset = self.filter_queryset(self.get_queryset())
        
        # Check if pagination should be disabled (map bounds provided)
        page = self.paginate_queryset(queryset)
        if page is None:
            # No pagination - return all results (for map views)
            serializer = self.get_serializer(queryset, many=True)
            return Response({
                'count': queryset.count(),
                'results': serializer.data
            })
        
        # Paginated response (for list views)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def perform_create(self, serializer):
        user = self.request.user if self.request.user.is_authenticated else None
        # Set default approval status to pending for new billboards
        billboard = serializer.save(user=user, approval_status='pending')
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
    filterset_fields = ['city', 'ooh_media_type', 'type', 'is_active', 'approval_status']  # Added approval_status filter
    search_fields = ['city', 'description', 'company_name']
    ordering_fields = ['created_at', 'price_range']
    ordering = ['-created_at']

    def get_queryset(self):
        # OPTIMIZED: Enhanced queryset for user's billboards with ALL fields and ALL statuses
        return Billboard.objects.filter(user=self.request.user)\
            .select_related('user')\
            .only(
                'id', 'city', 'description', 'number_of_boards', 'average_daily_views',
                'traffic_direction', 'road_position', 'road_name', 'exposure_time',
                'price_range', 'display_height', 'display_width', 'advertiser_phone',
                'advertiser_whatsapp', 'company_name', 'company_website',
                'ooh_media_type', 'ooh_media_id', 'type', 'images', 'unavailable_dates',
                'latitude', 'longitude', 'views', 'leads', 'is_active', 'created_at',
                'user__id', 'user__name', 'user__email', 'approval_status', 'approved_at',
                'rejected_at', 'rejection_reason', 'approved_by', 'rejected_by'
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
    """
    Track a lead for a specific billboard (phone or WhatsApp click)
    Owner's leads are never counted - simple and reliable check
    """
    try:
        billboard = Billboard.objects.get(id=billboard_id)
        
        # IMPORTANT: Check if the current user is the billboard owner
        # This prevents owners from inflating their own lead counts
        if billboard.user and request.user.is_authenticated and billboard.user.id == request.user.id:
            return Response({
                'message': 'Lead not tracked - owner viewing own billboard',
                'billboard_id': billboard_id,
                'current_leads': billboard.leads,
                'owner_lead': True
            }, status=status.HTTP_200_OK)
        
        # Get client IP address
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            user_ip = x_forwarded_for.split(',')[0].strip()
        else:
            user_ip = request.META.get('REMOTE_ADDR')
        
        # Get user agent
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Check for duplicate leads (same user or same IP for same billboard)
        lead_exists = False
        if request.user.is_authenticated:
            # Check by authenticated user
            lead_exists = Lead.objects.filter(
                billboard=billboard,
                user=request.user
            ).exists()
        else:
            # Check by IP for unauthenticated users
            if user_ip:
                lead_exists = Lead.objects.filter(
                    billboard=billboard,
                    user_ip=user_ip
                ).exists()
        
        if lead_exists:
            # Lead already tracked, don't increment counter
            return Response({
                'message': 'Lead already tracked for this billboard',
                'billboard_id': billboard_id,
                'current_leads': billboard.leads,
                'duplicate': True
            }, status=status.HTTP_200_OK)
        
        # Create new lead record
        Lead.objects.create(
            billboard=billboard,
            user=request.user if request.user.is_authenticated else None,
            user_ip=user_ip,
            user_agent=user_agent
        )
        
        # Increment the leads counter atomically
        billboard.increment_leads()
        
        user_info = request.user.email if request.user.is_authenticated else user_ip
        logger.info(f"New lead tracked for billboard {billboard_id} from {user_info}")
        
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
    Owner's views are never counted - simple and reliable check
    """
    try:
        billboard = Billboard.objects.get(id=billboard_id)
        
        # IMPORTANT: Check if the current user is the billboard owner
        # This prevents owners from inflating their own view counts
        if billboard.user and request.user.is_authenticated and billboard.user.id == request.user.id:
            return Response({
                'message': 'View not tracked - owner viewing own billboard',
                'billboard_id': billboard_id,
                'current_views': billboard.views,
                'owner_view': True
            }, status=status.HTTP_200_OK)
        
        # Get client IP address
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            user_ip = x_forwarded_for.split(',')[0].strip()
        else:
            user_ip = request.META.get('REMOTE_ADDR')
        
        # Get user agent
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Check for duplicate views (same user or same IP for same billboard)
        view_exists = False
        if request.user.is_authenticated:
            # Check by authenticated user
            view_exists = View.objects.filter(
                billboard=billboard,
                user=request.user
            ).exists()
        else:
            # Check by IP for unauthenticated users
            if user_ip:
                view_exists = View.objects.filter(
                    billboard=billboard,
                    user_ip=user_ip
                ).exists()
        
        if view_exists:
            # View already tracked, don't increment counter
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
            user=request.user if request.user.is_authenticated else None,
            user_ip=user_ip,
            user_agent=user_agent
        )
        
        # Increment the views counter atomically
        billboard.increment_views()
        
        user_info = request.user.email if request.user.is_authenticated else user_ip
        logger.info(f"New view tracked for billboard {billboard_id} from {user_info}")
        
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


# Billboard Approval Workflow Endpoints

@swagger_auto_schema(
    method='post',
    operation_description="""
    Approve or reject a pending billboard.
    
    This unified endpoint replaces the separate `/approve/` and `/reject/` endpoints.
    Use the `action` field to specify whether to approve or reject the billboard.
    
    **Requirements:**
    - Admin authentication required
    - Billboard must be in 'pending' status
    - Action must be either 'approve' or 'reject'
    """,
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['action'],
        properties={
            'action': openapi.Schema(
                type=openapi.TYPE_STRING,
                enum=['approve', 'reject'],
                description='Action to perform: "approve" or "reject"',
                example='approve'
            ),
            'rejection_reason': openapi.Schema(
                type=openapi.TYPE_STRING,
                description='Optional reason for rejection (recommended when action is "reject")',
                example='Poor image quality or incomplete information'
            )
        }
    ),
    responses={
        200: openapi.Response(
            description='Success',
            examples={
                'application/json': {
                    'approve': {
                        'message': 'Billboard approved successfully',
                        'billboard': {
                            'id': 1,
                            'approval_status': 'approved',
                            'approved_at': '2025-01-26T15:00:00Z',
                            'approved_by_username': 'admin@example.com'
                        }
                    },
                    'reject': {
                        'message': 'Billboard rejected successfully',
                        'billboard': {
                            'id': 1,
                            'approval_status': 'rejected',
                            'rejected_at': '2025-01-26T15:00:00Z',
                            'rejected_by_username': 'admin@example.com',
                            'rejection_reason': 'Poor image quality'
                        }
                    }
                }
            }
        ),
        400: openapi.Response(
            description='Bad Request',
            examples={
                'application/json': {
                    'error': 'Invalid action. Must be "approve" or "reject"'
                }
            }
        ),
        403: openapi.Response(
            description='Forbidden - Admin access required',
            examples={
                'application/json': {
                    'error': 'You do not have permission to perform this action.'
                }
            }
        ),
        404: openapi.Response(
            description='Billboard not found',
            examples={
                'application/json': {
                    'error': 'Billboard not found'
                }
            }
        )
    },
    tags=['Billboard Approval'],
    operation_summary='Update billboard approval status (Approve/Reject)'
)
@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def update_billboard_approval_status(request, billboard_id):
    """
    Approve or reject a pending billboard
    
    This unified endpoint replaces the separate approve and reject endpoints.
    Use the action field in the request body to specify the desired action.
    """
    try:
        billboard = Billboard.objects.get(id=billboard_id)
        
        if billboard.approval_status != 'pending':
            return Response({
                'error': f'Billboard is already {billboard.approval_status}. Only pending billboards can be approved or rejected.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get action from request body
        action = request.data.get('action', '').lower()
        
        if action not in ['approve', 'reject']:
            return Response({
                'error': 'Invalid action. Must be "approve" or "reject"'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Handle approve action
        if action == 'approve':
            billboard.approve(request.user)
            return Response({
                'message': 'Billboard approved successfully',
                'billboard': BillboardSerializer(billboard).data
            }, status=status.HTTP_200_OK)
        
        # Handle reject action
        elif action == 'reject':
            rejection_reason = request.data.get('rejection_reason', '')
            billboard.reject(request.user, rejection_reason)
            return Response({
                'message': 'Billboard rejected successfully',
                'billboard': BillboardSerializer(billboard).data
            }, status=status.HTTP_200_OK)
        
    except Billboard.DoesNotExist:
        return Response({
            'error': 'Billboard not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'error': f'Failed to update billboard approval status: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@swagger_auto_schema(
    method='get',
    operation_description="""
    Get all pending billboards for admin review.
    
    Returns a list of all billboards that are awaiting approval.
    Only billboards with 'pending' approval status are returned.
    
    **Requirements:**
    - Admin authentication required
    """,
    responses={
        200: openapi.Response(
            description='Success',
            examples={
                'application/json': {
                    'results': [
                        {
                            'id': 1,
                            'city': 'Karachi',
                            'description': 'Premium location billboard',
                            'approval_status': 'pending',
                            'user_name': 'John Doe',
                            'created_at': '2025-01-26T14:30:00Z'
                        }
                    ],
                    'count': 1
                }
            }
        ),
        403: openapi.Response(
            description='Forbidden - Admin access required',
            examples={
                'application/json': {
                    'error': 'You do not have permission to perform this action.'
                }
            }
        )
    },
    tags=['Billboard Approval'],
    operation_summary='Get pending billboards for review'
)
@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def get_pending_billboards(request):
    """
    Get all pending billboards for admin review
    
    Returns a list of billboards awaiting approval.
    """
    try:
        pending_billboards = Billboard.objects.filter(
            approval_status='pending'
        ).select_related('user').order_by('-created_at')
        
        serializer = BillboardSerializer(pending_billboards, many=True)
        
        return Response({
            'results': serializer.data,
            'count': pending_billboards.count()
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': f'Failed to fetch pending billboards: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)