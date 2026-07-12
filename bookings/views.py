from django.db.models import Q
from rest_framework import permissions, status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404

from billboards.availability_utils import parse_date_param
from billboards.models import Billboard
from core.pagination import CustomPagination

from .models import Booking
from .serializers import (
    BookingAcceptSerializer,
    BookingCreateSerializer,
    BookingRejectSerializer,
    BookingSerializer,
    ContentApproveSerializer,
    ContentRejectSerializer,
)
from .services import (
    BookingError,
    accept_booking,
    approve_content,
    build_calendar_busy,
    cancel_booking,
    content_capabilities,
    create_booking_request,
    maybe_advance_live_and_completed,
    reject_booking,
    reject_content,
    submit_content,
)


def _err(exc: BookingError):
    return Response(
        {'status_code': exc.status_code, 'message': exc.message},
        status=exc.status_code,
    )


class BillboardCalendarView(APIView):
    """GET /api/billboards/{id}/calendar/?from=&to= — busy ranges (guest OK)."""

    permission_classes = [permissions.AllowAny]

    def get(self, request, billboard_id):
        billboard = get_object_or_404(Billboard, pk=billboard_id)
        try:
            from_date = parse_date_param(request.query_params.get('from'))
            to_date = parse_date_param(request.query_params.get('to'))
        except ValueError as exc:
            return Response(
                {'status_code': 400, 'message': str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if from_date and to_date and from_date > to_date:
            return Response(
                {'status_code': 400, 'message': 'from must be on or before to.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        busy = build_calendar_busy(billboard, from_date=from_date, to_date=to_date)
        payload = {
            'status_code': 200,
            'message': 'Calendar retrieved successfully',
            'billboard_id': billboard.id,
            'busy': busy,
            'content_capabilities': content_capabilities(billboard),
        }
        if from_date:
            payload['from'] = from_date
        if to_date:
            payload['to'] = to_date
        return Response(payload, status=status.HTTP_200_OK)


class BookingListCreateView(APIView):
    """GET list (paginated) + POST create request."""

    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomPagination

    def get(self, request):
        maybe_advance_live_and_completed()
        user = request.user
        role = (request.query_params.get('role') or '').strip().lower()
        status_filter = (request.query_params.get('status') or '').strip().lower()

        qs = Booking.objects.select_related(
            'billboard',
            'billboard__media_type',
            'advertiser',
            'media_owner',
        ).prefetch_related('content', 'payment')

        if role == 'owner' or (not role and user.user_type == 'media_owner'):
            qs = qs.filter(media_owner=user)
        elif role == 'advertiser' or (not role and user.user_type == 'advertiser'):
            qs = qs.filter(advertiser=user)
        else:
            qs = qs.filter(Q(advertiser=user) | Q(media_owner=user))

        if status_filter:
            qs = qs.filter(status=status_filter)

        qs = qs.order_by('-created_at')
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(qs, request, view=self)
        data = BookingSerializer(page, many=True, context={'request': request}).data
        resp = paginator.get_paginated_response(data)
        resp.data['status_code'] = 200
        resp.data['message'] = 'Bookings retrieved successfully'
        return resp

    def post(self, request):
        serializer = BookingCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            booking = create_booking_request(
                advertiser=request.user,
                billboard_id=serializer.validated_data['billboard_id'],
                start_date=serializer.validated_data['start_date'],
                end_date=serializer.validated_data['end_date'],
                message=serializer.validated_data.get('message') or '',
            )
        except BookingError as exc:
            return _err(exc)

        booking = (
            Booking.objects.select_related(
                'billboard', 'billboard__media_type', 'advertiser', 'media_owner'
            )
            .prefetch_related('content', 'payment')
            .get(pk=booking.pk)
        )
        return Response(
            {
                'status_code': 201,
                'message': 'Booking request created successfully',
                'booking': BookingSerializer(booking, context={'request': request}).data,
            },
            status=status.HTTP_201_CREATED,
        )


class BookingDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, booking_id):
        maybe_advance_live_and_completed()
        booking = (
            Booking.objects.select_related(
                'billboard', 'billboard__media_type', 'advertiser', 'media_owner'
            )
            .prefetch_related('content', 'payment')
            .filter(pk=booking_id)
            .first()
        )
        if not booking:
            return Response(
                {'status_code': 404, 'message': 'Booking not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        if request.user.id not in (booking.advertiser_id, booking.media_owner_id):
            return Response(
                {'status_code': 403, 'message': 'You are not a participant in this booking.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        return Response(
            {
                'status_code': 200,
                'message': 'Booking retrieved successfully',
                'booking': BookingSerializer(booking, context={'request': request}).data,
            },
            status=status.HTTP_200_OK,
        )


class BookingAcceptView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, booking_id):
        serializer = BookingAcceptSerializer(data=request.data or {})
        serializer.is_valid(raise_exception=True)
        try:
            booking, _content = accept_booking(
                request.user,
                booking_id,
                owner_note=serializer.validated_data.get('owner_note') or '',
            )
        except BookingError as exc:
            return _err(exc)
        booking.refresh_from_db()
        booking = (
            Booking.objects.select_related(
                'billboard', 'billboard__media_type', 'advertiser', 'media_owner'
            )
            .prefetch_related('content', 'payment')
            .get(pk=booking.pk)
        )
        return Response(
            {
                'status_code': 200,
                'message': 'Booking accepted successfully',
                'booking': BookingSerializer(booking, context={'request': request}).data,
            },
            status=status.HTTP_200_OK,
        )


class BookingRejectView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, booking_id):
        serializer = BookingRejectSerializer(data=request.data or {})
        serializer.is_valid(raise_exception=True)
        try:
            booking = reject_booking(
                request.user,
                booking_id,
                reason=serializer.validated_data.get('reason') or '',
            )
        except BookingError as exc:
            return _err(exc)
        booking = (
            Booking.objects.select_related(
                'billboard', 'billboard__media_type', 'advertiser', 'media_owner'
            )
            .prefetch_related('content', 'payment')
            .get(pk=booking.pk)
        )
        return Response(
            {
                'status_code': 200,
                'message': 'Booking rejected successfully',
                'booking': BookingSerializer(booking, context={'request': request}).data,
            },
            status=status.HTTP_200_OK,
        )


class BookingCancelView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, booking_id):
        try:
            booking = cancel_booking(request.user, booking_id)
        except BookingError as exc:
            return _err(exc)
        booking = (
            Booking.objects.select_related(
                'billboard', 'billboard__media_type', 'advertiser', 'media_owner'
            )
            .prefetch_related('content', 'payment')
            .get(pk=booking.pk)
        )
        return Response(
            {
                'status_code': 200,
                'message': 'Booking cancelled successfully',
                'booking': BookingSerializer(booking, context={'request': request}).data,
            },
            status=status.HTTP_200_OK,
        )


class BookingContentSubmitView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def post(self, request, booking_id):
        media_file = request.FILES.get('media_file') or request.FILES.get('file')
        try:
            content = submit_content(
                request.user,
                booking_id,
                data=request.data,
                media_file=media_file,
            )
        except BookingError as exc:
            return _err(exc)

        booking = (
            Booking.objects.select_related(
                'billboard', 'billboard__media_type', 'advertiser', 'media_owner'
            )
            .prefetch_related('content', 'payment')
            .get(pk=content.booking_id)
        )
        return Response(
            {
                'status_code': 200,
                'message': 'Content submitted successfully',
                'booking': BookingSerializer(booking, context={'request': request}).data,
            },
            status=status.HTTP_200_OK,
        )


class BookingContentApproveView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, booking_id):
        serializer = ContentApproveSerializer(data=request.data or {})
        serializer.is_valid(raise_exception=True)
        try:
            booking, _content = approve_content(
                request.user,
                booking_id,
                install_confirmed=serializer.validated_data.get('install_confirmed', False),
            )
        except BookingError as exc:
            return _err(exc)
        booking = (
            Booking.objects.select_related(
                'billboard', 'billboard__media_type', 'advertiser', 'media_owner'
            )
            .prefetch_related('content', 'payment')
            .get(pk=booking.pk)
        )
        return Response(
            {
                'status_code': 200,
                'message': 'Content approved; booking confirmed',
                'booking': BookingSerializer(booking, context={'request': request}).data,
            },
            status=status.HTTP_200_OK,
        )


class BookingContentRejectView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, booking_id):
        serializer = ContentRejectSerializer(data=request.data or {})
        serializer.is_valid(raise_exception=True)
        try:
            reject_content(
                request.user,
                booking_id,
                feedback=serializer.validated_data.get('feedback') or '',
            )
        except BookingError as exc:
            return _err(exc)
        booking = (
            Booking.objects.select_related(
                'billboard', 'billboard__media_type', 'advertiser', 'media_owner'
            )
            .prefetch_related('content', 'payment')
            .get(pk=booking_id)
        )
        return Response(
            {
                'status_code': 200,
                'message': 'Content rejected; advertiser may resubmit',
                'booking': BookingSerializer(booking, context={'request': request}).data,
            },
            status=status.HTTP_200_OK,
        )
