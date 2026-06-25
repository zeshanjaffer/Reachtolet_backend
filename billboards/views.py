from rest_framework import generics, permissions, status
from .models import Billboard, Wishlist, Lead, View, OohMediaType
from .serializers import (
    BillboardSerializer,
    BillboardListSerializer,
    BillboardPublicSummarySerializer,
    BillboardPreviewSerializer,
    BillboardAvailabilityUpdateSerializer,
    WishlistSerializer,
)
from .availability_utils import build_availability_payload, parse_date_param
from .specifications_utils import parse_specifications_from_payload
from .filters import BillboardFilter
from .clustering import cluster_billboards, should_use_clustering
from django.core.cache import cache
from .signals import get_cache_version
import hashlib
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from django.conf import settings
from django.core.files.storage import default_storage
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from core.pagination import CustomPagination
from core.responses import action_response
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_cookie
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.db.models import Prefetch, Q
from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .permissions import IsMediaOwner, IsBillboardOwner
from .media_types_data import CATEGORY_LABELS
from .media_type_serializers import OohMediaTypePickerSerializer
# WebSocket imports removed
import os
import uuid
import logging

logger = logging.getLogger(__name__)

_CREATE_SKIP_FIELDS = frozenset({'unavailable_dates', 'booked_dates', 'availability'})


def _parse_images_form_field(raw):
    """Optional pre-uploaded URL list sent as JSON string in multipart `images` field."""
    if raw is None or raw == '':
        return []
    if isinstance(raw, list):
        return [u for u in raw if isinstance(u, str) and u]
    if isinstance(raw, str):
        import json
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            return []
        if isinstance(parsed, list):
            return [u for u in parsed if isinstance(u, str) and u]
    return []


def upload_billboard_images_from_request(request):
    """Upload images_0, images_1, … from multipart request. Returns (urls, error_response)."""
    image_urls = []
    if not request.FILES:
        return image_urls, None

    for file_key, file_obj in request.FILES.items():
        if not file_key.startswith('images'):
            continue
        try:
            allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/jpg']
            if file_obj.content_type not in allowed_types:
                return None, Response({
                    'detail': f'Invalid file type for {file_key}: {file_obj.content_type}',
                }, status=status.HTTP_400_BAD_REQUEST)

            max_size = 10 * 1024 * 1024
            if file_obj.size > max_size:
                return None, Response({
                    'detail': f'File too large for {file_key}. Maximum size is 10MB.',
                }, status=status.HTTP_400_BAD_REQUEST)

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
            path = default_storage.save(file_path, file_obj)
            image_urls.append(request.build_absolute_uri(f'{settings.MEDIA_URL}{path}'))
        except Exception as exc:
            return None, Response({
                'detail': f'Upload failed for {file_key}: {exc}',
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return image_urls, None


def build_billboard_write_payload(request, uploaded_image_urls, *, is_update=False, existing_images=None):
    """
    Build serializer payload from multipart form.
    File fields (images_0, images_1, …) are uploaded first; only URLs go to `images`.
    """
    payload = {}
    for key in request.data:
        if key in _CREATE_SKIP_FIELDS or key == 'images' or key.startswith('images_'):
            continue
        payload[key] = request.data.get(key)

    payload = parse_specifications_from_payload(payload)

    images_field = request.data.get('images')
    if is_update:
        if images_field not in (None, ''):
            payload['images'] = _parse_images_form_field(images_field) + list(uploaded_image_urls)
        elif uploaded_image_urls:
            payload['images'] = list(existing_images or []) + list(uploaded_image_urls)
    else:
        payload['images'] = _parse_images_form_field(images_field) + list(uploaded_image_urls)

    return payload


# Backward-compatible alias used by create flow
build_billboard_create_payload = build_billboard_write_payload


class OohMediaTypeListView(APIView):
    """
    Media type picker for media owners creating billboards.
    Returns grouped types (adbuq-style) plus a flat selectable list.
    """

    permission_classes = [IsMediaOwner]

    def get(self, request):
        types_qs = OohMediaType.objects.filter(is_active=True).order_by('sort_order', 'name')
        selectable_qs = types_qs.filter(is_selectable=True)

        search = (request.query_params.get('search') or '').strip()
        if search:
            selectable_qs = selectable_qs.filter(
                Q(name__icontains=search) | Q(slug__icontains=search.replace(' ', '-'))
            )

        children_by_parent = {}
        standalone_by_category = {}
        for media_type in selectable_qs:
            if media_type.parent_id:
                children_by_parent.setdefault(media_type.parent_id, []).append(media_type)
            else:
                standalone_by_category.setdefault(media_type.category, []).append(media_type)

        groups = []
        for header_slug in ('all-digital', 'all-static'):
            header = types_qs.filter(slug=header_slug, is_selectable=False).first()
            if not header:
                continue
            group_types = children_by_parent.get(header.id, [])
            if search and not group_types:
                continue
            groups.append({
                'key': header.category,
                'label': CATEGORY_LABELS.get(header.category, header.category),
                'header': {
                    'id': header.id,
                    'name': header.name,
                    'slug': header.slug,
                    'is_selectable': False,
                },
                'types': OohMediaTypePickerSerializer(group_types, many=True).data,
            })

        for category in ('place', 'transit', 'other'):
            category_types = standalone_by_category.get(category, [])
            if not category_types:
                continue
            groups.append({
                'key': category,
                'label': CATEGORY_LABELS.get(category, category),
                'header': None,
                'types': OohMediaTypePickerSerializer(category_types, many=True).data,
            })

        message = 'Media types retrieved successfully'
        if search:
            message = f'Media types matching "{search}" retrieved successfully'

        return Response({
            'status_code': status.HTTP_200_OK,
            'message': message,
            'search': search or None,
            'groups': groups,
            'selectable': OohMediaTypePickerSerializer(selectable_qs, many=True).data,
            'count': selectable_qs.count(),
        }, status=status.HTTP_200_OK)


class BillboardListCreateView(generics.ListCreateAPIView):
    def get_queryset(self):
        # Only mappable billboards: approved, active, valid PostGIS location.
        return Billboard.objects.filter(
            is_active=True,
            approval_status='approved',
            location__isnull=False,
            latitude__isnull=False,
            longitude__isnull=False,
        ).only(
            'id',
            'latitude',
            'longitude',
            'created_at',
        ).order_by('-created_at')

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return BillboardPublicSummarySerializer
        return BillboardSerializer

    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = BillboardFilter  # Use simple filter
    search_fields = ['city', 'description', 'company_name', 'road_name']
    ordering_fields = ['created_at', 'price_range', 'city', 'views']
    ordering = ['-created_at']
    parser_classes = (MultiPartParser, FormParser)  # Add parsers for file uploads

    def paginate_queryset(self, queryset):
        """
        Disable pagination for map views (full bounds or cluster=true).
        """
        ne_lat = self.request.query_params.get('ne_lat')
        ne_lng = self.request.query_params.get('ne_lng')
        sw_lat = self.request.query_params.get('sw_lat')
        sw_lng = self.request.query_params.get('sw_lng')
        use_clustering = self.request.query_params.get('cluster', 'false').lower() == 'true'

        if ne_lat and ne_lng and sw_lat and sw_lng:
            return None
        if use_clustering:
            return None

        return super().paginate_queryset(queryset)

    @staticmethod
    def _empty_map_response(use_clustering, zoom_level=10.0):
        """Stable map JSON while the client is still sending partial bounds."""
        if use_clustering:
            return {
                'count': 0,
                'clustered_count': 0,
                'clusters': [],
                'clustering_enabled': True,
                'zoom_level': zoom_level,
            }
        return {
            'count': 0,
            'results': [],
            'clustering_enabled': False,
        }

    def list(self, request, *args, **kwargs):
        """
        Map-aware list endpoint with production-grade Supercluster clustering.

        Query params:
          cluster=true            — enable clustering (Supercluster algorithm)
          zoom=<float>            — current map zoom level (0–20, default 10)
          ne_lat, ne_lng,
          sw_lat, sw_lng          — visible map bounds; disables pagination and
                                    restricts clustering to the viewport

        Clustering response shape:
          { count, clustered_count, clusters: [...], clustering_enabled, zoom_level }
          Each cluster item: { type, cluster_id|id, latitude, longitude, count,
                               expansion_zoom? }

        Non-clustering (paginated) response:
          { links, count, total_pages, current_page, results: [{id, lat, lng, count}] }
        """
        queryset = self.filter_queryset(self.get_queryset())

        use_clustering = request.query_params.get('cluster', 'false').lower() == 'true'
        try:
            zoom_level = float(request.query_params.get('zoom', 10.0))
        except (ValueError, TypeError):
            zoom_level = 10.0

        ne_lat = request.query_params.get('ne_lat')
        ne_lng = request.query_params.get('ne_lng')
        sw_lat = request.query_params.get('sw_lat')
        sw_lng = request.query_params.get('sw_lng')
        bound_params = (ne_lat, ne_lng, sw_lat, sw_lng)
        has_bounds = all(bound_params)
        partial_bounds = any(bound_params) and not has_bounds

        # Fast map drag often sends incomplete bounds — return empty map shape, not paginated JSON.
        if partial_bounds:
            return Response(self._empty_map_response(use_clustering, zoom_level))

        page = self.paginate_queryset(queryset)

        # ── MAP VIEW (bounds provided, no pagination) ──────────────────────
        if page is None:
            bbox = (
                {'ne_lat': ne_lat, 'ne_lng': ne_lng, 'sw_lat': sw_lat, 'sw_lng': sw_lng}
                if has_bounds else None
            )

            cache_version = get_cache_version()
            cache_key = hashlib.md5(
                f"bbc_v{cache_version}_{ne_lat}_{ne_lng}_{sw_lat}_{sw_lng}_{zoom_level}_{use_clustering}".encode()
            ).hexdigest()

            if has_bounds:
                cached = cache.get(cache_key)
                if cached:
                    logger.debug("Cache HIT billboard map: %s", cache_key[:12])
                    return Response(cached)

            serializer = self.get_serializer(queryset, many=True)
            billboards_data = list(serializer.data)
            billboard_count = len(billboards_data)

            if use_clustering and should_use_clustering(zoom_level, billboard_count):
                clusters = cluster_billboards(billboards_data, zoom_level, bbox)
                response_data = {
                    'count': billboard_count,
                    'clustered_count': len(clusters),
                    'clusters': clusters,
                    'clustering_enabled': True,
                    'zoom_level': zoom_level,
                }
            else:
                response_data = {
                    'count': billboard_count,
                    'results': billboards_data,
                    'clustering_enabled': False,
                }

            if has_bounds:
                cache.set(cache_key, response_data, 120)

            return Response(response_data)

        # ── PAGINATED LIST VIEW ────────────────────────────────────────────
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    def create(self, request, *args, **kwargs):
        """
        Override create to handle image uploads and check user role
        """
        # Check if user is authenticated
        if not request.user.is_authenticated:
            return Response({
                'detail': 'Authentication required to create billboards'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Check if user is a media owner
        if request.user.user_type != 'media_owner':
            return Response({
                'detail': 'Only media owners can create billboards. You are registered as an advertiser.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Handle image uploads
        image_urls, upload_error = upload_billboard_images_from_request(request)
        if upload_error:
            return upload_error
        
        # Build payload: uploaded files become URL list; never pass raw multipart `images` to JSONField.
        payload = build_billboard_write_payload(request, image_urls)

        serializer = self.get_serializer(data=payload)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return action_response('Billboard created successfully', status.HTTP_201_CREATED)
    
    def perform_create(self, serializer):
        user = self.request.user
        # Admin approval workflow: pending → admin approves → visible on public map.
        # Development: BYPASS_BILLBOARD_APPROVAL skips pending (see core.settings).
        if getattr(settings, 'BYPASS_BILLBOARD_APPROVAL', False):
            serializer.save(
                user=user,
                approval_status='approved',
                approved_at=timezone.now(),
            )
        else:
            serializer.save(user=user, approval_status='pending')
        # WebSocket notifications removed

    def notify_new_billboard(self, billboard):
        """WebSocket notifications removed - no longer needed"""
        pass

    @method_decorator(cache_page(60 * 5))  # Cache for 5 minutes
    @method_decorator(vary_on_cookie)
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

class BillboardAvailabilityView(APIView):
    """Get or set booked dates for a billboard calendar."""

    permission_classes = [IsAuthenticated]

    def get(self, request, billboard_id):
        try:
            billboard = Billboard.objects.get(pk=billboard_id)
        except Billboard.DoesNotExist:
            return action_response('Billboard not found', status.HTTP_404_NOT_FOUND)

        from_date = None
        to_date = None
        try:
            from_date = parse_date_param(request.query_params.get('from'))
            to_date = parse_date_param(request.query_params.get('to'))
        except ValueError as exc:
            return action_response(str(exc), status.HTTP_400_BAD_REQUEST)

        if from_date and to_date and from_date > to_date:
            return action_response(
                'Invalid date range: from must be before or equal to to.',
                status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            build_availability_payload(billboard, from_date=from_date, to_date=to_date),
            status=status.HTTP_200_OK,
        )

    def put(self, request, billboard_id):
        if request.user.user_type != 'media_owner':
            return action_response(
                'Only media owners can set billboard availability.',
                status.HTTP_403_FORBIDDEN,
            )

        try:
            billboard = Billboard.objects.get(pk=billboard_id)
        except Billboard.DoesNotExist:
            return action_response('Billboard not found', status.HTTP_404_NOT_FOUND)

        if billboard.user != request.user:
            return action_response(
                'You can only set availability for your own billboards.',
                status.HTTP_403_FORBIDDEN,
            )

        serializer = BillboardAvailabilityUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        booked_dates = serializer.validated_data['booked_dates']

        billboard.unavailable_dates = booked_dates
        billboard.save(update_fields=['unavailable_dates'])

        payload = build_availability_payload(billboard)
        return Response(
            {
                'status_code': status.HTTP_200_OK,
                'message': 'Availability updated successfully',
                **payload,
            },
            status=status.HTTP_200_OK,
        )


class BillboardPreviewView(generics.RetrieveAPIView):
    """
    Lightweight preview for map pin tap (before full detail screen).
    Available to all authenticated users for approved+active billboards;
    media owners can also preview their own billboards.
    """

    serializer_class = BillboardPreviewSerializer
    permission_classes = [IsAuthenticated]
    lookup_url_kwarg = 'billboard_id'

    def get_queryset(self):
        user = self.request.user
        public_qs = Q(is_active=True, approval_status='approved')
        if user.is_authenticated and user.user_type == 'media_owner':
            return Billboard.objects.filter(public_qs | Q(user=user))
        return Billboard.objects.filter(public_qs)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        if self.request.user.is_authenticated:
            context['wishlist_billboard_ids'] = frozenset(
                Wishlist.objects.filter(user=self.request.user).values_list(
                    'billboard_id', flat=True
                )
            )
        else:
            context['wishlist_billboard_ids'] = frozenset()
        return context


class BillboardDetailView(generics.RetrieveUpdateDestroyAPIView):
    def get_queryset(self):
        return Billboard.objects.select_related(
            'user', 'approved_by', 'rejected_by', 'media_type',
        )

    serializer_class = BillboardSerializer
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        if self.request.user.is_authenticated:
            context['wishlist_billboard_ids'] = frozenset(
                Wishlist.objects.filter(user=self.request.user).values_list(
                    'billboard_id', flat=True
                )
            )
        else:
            context['wishlist_billboard_ids'] = frozenset()
        return context
    
    permission_classes = [IsAuthenticated]

    def _check_owner_can_modify(self, request, instance):
        if request.user.user_type != 'media_owner':
            return Response({
                'detail': 'Only media owners can update billboards.',
            }, status=status.HTTP_403_FORBIDDEN)
        if instance.user != request.user:
            return Response({
                'detail': 'You can only update your own billboards.',
            }, status=status.HTTP_403_FORBIDDEN)
        return None

    @staticmethod
    def _strip_reserved_update_fields(request):
        if hasattr(request.data, '_mutable'):
            request.data._mutable = True
        for field in ('unavailable_dates', 'booked_dates', 'availability', 'ooh_media_type'):
            if field in request.data:
                request.data.pop(field)

    def _save_multipart_update(self, request, instance, *, partial):
        image_urls, upload_error = upload_billboard_images_from_request(request)
        if upload_error:
            return upload_error

        payload = build_billboard_write_payload(
            request,
            image_urls,
            is_update=True,
            existing_images=instance.images or [],
        )
        serializer = self.get_serializer(instance, data=payload, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        denied = self._check_owner_can_modify(request, instance)
        if denied:
            return denied

        self._strip_reserved_update_fields(request)

        content_type = getattr(request, 'content_type', '') or ''
        if request.FILES or content_type.startswith('multipart/'):
            return self._save_multipart_update(request, instance, partial=False)

        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        denied = self._check_owner_can_modify(request, instance)
        if denied:
            return denied

        self._strip_reserved_update_fields(request)

        content_type = getattr(request, 'content_type', '') or ''
        if request.FILES or content_type.startswith('multipart/'):
            return self._save_multipart_update(request, instance, partial=True)

        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # Check if user is media_owner
        if request.user.user_type != 'media_owner':
            return Response({
                'detail': 'Only media owners can delete billboards.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Check if user owns this billboard
        if instance.user != request.user:
            return Response({
                'detail': 'You can only delete your own billboards.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        billboard_id = str(instance.id)
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
    filterset_fields = ['city', 'ooh_media_type', 'media_type_id', 'type', 'is_active', 'approval_status']
    search_fields = ['city', 'description', 'company_name', 'road_name']
    ordering_fields = ['created_at', 'price_range']
    ordering = ['-created_at']

    def get(self, request, *args, **kwargs):
        """
        Override get to check if user is media_owner before allowing access
        """
        # Check if user is media_owner
        if request.user.user_type != 'media_owner':
            return Response({
                'detail': 'Only media owners can access their billboards. You are registered as an advertiser.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        return Billboard.objects.filter(user=self.request.user).select_related(
            'user', 'approved_by', 'rejected_by', 'media_type',
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        context['wishlist_billboard_ids'] = frozenset(
            Wishlist.objects.filter(user=self.request.user).values_list(
                'billboard_id', flat=True
            )
        )
        return context


class WishlistView(generics.ListCreateAPIView):
    """View for managing user's wishlist"""
    serializer_class = WishlistSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = [
        'billboard__city',
        'billboard__description',
        'billboard__company_name',
        'billboard__road_name',
    ]
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        return Wishlist.objects.filter(user=self.request.user).select_related(
            'billboard__user',
            'billboard__approved_by',
            'billboard__rejected_by',
        )

    def create(self, request, *args, **kwargs):
        """Add a billboard to wishlist"""
        billboard_id = request.data.get('billboard_id')
        
        # Check if already in wishlist
        if Wishlist.objects.filter(user=request.user, billboard_id=billboard_id).exists():
            return action_response(
                'Billboard is already in your wishlist',
                status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return action_response('Added to wishlist successfully', status.HTTP_201_CREATED)


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
                wishlist_item.delete()
                return action_response('Removed from wishlist', status.HTTP_200_OK)

            billboard = Billboard.objects.get(id=billboard_id)
            Wishlist.objects.create(user=request.user, billboard=billboard)
            return action_response('Added to wishlist', status.HTTP_201_CREATED)

        except Billboard.DoesNotExist:
            return action_response('Billboard not found', status.HTTP_404_NOT_FOUND)


# Updated Lead Tracking View with Duplicate Prevention
@api_view(['POST'])
@permission_classes([IsAuthenticated])
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
            return action_response(
                'Lead not tracked - owner viewing own billboard',
                status.HTTP_200_OK,
            )
        
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
            return action_response(
                'Lead already tracked for this billboard',
                status.HTTP_200_OK,
            )
        
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
        
        return action_response('Lead tracked successfully', status.HTTP_200_OK)

    except Billboard.DoesNotExist:
        return action_response('Billboard not found', status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error tracking lead for billboard {billboard_id}: {str(e)}")
        return action_response('Failed to track lead', status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(csrf_exempt, name='dispatch')
class BillboardImageUploadView(APIView):
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, format=None):
        # Check if user is a media owner
        if request.user.user_type != 'media_owner':
            return Response({
                'detail': 'Only media owners can upload billboard images.'
            }, status=status.HTTP_403_FORBIDDEN)
        
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

@method_decorator(csrf_exempt, name='dispatch')
class BillboardImageUploadView(APIView):
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, format=None):
        # Check if user is a media owner
        if request.user.user_type != 'media_owner':
            return Response({
                'detail': 'Only media owners can upload billboard images.'
            }, status=status.HTTP_403_FORBIDDEN)
        
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
@permission_classes([IsAuthenticated])
def toggle_billboard_active(request, billboard_id):
    """
    Toggle the active status of a billboard
    Only billboard owners (media_owners) can toggle their own billboards
    """
    try:
        # Get the billboard
        billboard = Billboard.objects.get(id=billboard_id)
        
        # Check if user is media_owner
        if request.user.user_type != 'media_owner':
            return Response({
                'error': 'Only media owners can toggle billboard status.'
            }, status=status.HTTP_403_FORBIDDEN)
        
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
@permission_classes([IsAuthenticated])
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
            return action_response(
                'View not tracked - owner viewing own billboard',
                status.HTTP_200_OK,
            )
        
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
            return action_response(
                'View already tracked for this billboard',
                status.HTTP_200_OK,
            )
        
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
        
        return action_response('View tracked successfully', status.HTTP_200_OK)

    except Billboard.DoesNotExist:
        return action_response('Billboard not found', status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error tracking view for billboard {billboard_id}: {str(e)}")
        return action_response('Failed to track view', status.HTTP_500_INTERNAL_SERVER_ERROR)

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
        ).select_related(
            'user',
            'approved_by',
            'rejected_by',
        ).order_by('-created_at')
        wishlist_ids = frozenset()
        if request.user.is_authenticated:
            wishlist_ids = frozenset(
                Wishlist.objects.filter(user=request.user).values_list(
                    'billboard_id', flat=True
                )
            )
        serializer = BillboardSerializer(
            pending_billboards,
            many=True,
            context={'request': request, 'wishlist_billboard_ids': wishlist_ids},
        )
        
        return Response({
            'results': serializer.data,
            'count': pending_billboards.count()
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': f'Failed to fetch pending billboards: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)