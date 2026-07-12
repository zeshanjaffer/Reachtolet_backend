from django.urls import path

from .views import (
    BookingAcceptView,
    BookingCancelView,
    BookingContentApproveView,
    BookingContentRejectView,
    BookingContentSubmitView,
    BookingDetailView,
    BookingListCreateView,
    BookingRejectView,
)

urlpatterns = [
    path('', BookingListCreateView.as_view(), name='booking-list-create'),
    path('<int:booking_id>/', BookingDetailView.as_view(), name='booking-detail'),
    path('<int:booking_id>/accept/', BookingAcceptView.as_view(), name='booking-accept'),
    path('<int:booking_id>/reject/', BookingRejectView.as_view(), name='booking-reject'),
    path('<int:booking_id>/cancel/', BookingCancelView.as_view(), name='booking-cancel'),
    path(
        '<int:booking_id>/content/',
        BookingContentSubmitView.as_view(),
        name='booking-content-submit',
    ),
    path(
        '<int:booking_id>/content/approve/',
        BookingContentApproveView.as_view(),
        name='booking-content-approve',
    ),
    path(
        '<int:booking_id>/content/reject/',
        BookingContentRejectView.as_view(),
        name='booking-content-reject',
    ),
]
