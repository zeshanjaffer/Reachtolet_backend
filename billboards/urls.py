from django.urls import path
from .views import (
    BillboardListCreateView,
    BillboardDetailView,
    MyBillboardsView,
    OohMediaTypeListView,
    OohMediaTypeSchemaView,
    WishlistView,
    WishlistRemoveView,
    WishlistToggleView,
    track_billboard_lead,
    track_billboard_view,
    toggle_billboard_active,
    BillboardAvailabilityView,
    BillboardPreviewView,
    update_billboard_approval_status,
    get_pending_billboards,
)
from bookings.views import BillboardCalendarView

urlpatterns = [
    path('media-types/', OohMediaTypeListView.as_view(), name='billboard-media-types'),
    path(
        'media-types/<int:media_type_id>/schema/',
        OohMediaTypeSchemaView.as_view(),
        name='billboard-media-type-schema',
    ),
    path('', BillboardListCreateView.as_view(), name='billboard-list-create'),
    path('my-billboards/', MyBillboardsView.as_view(), name='my-billboards'),
    path('<int:billboard_id>/preview/', BillboardPreviewView.as_view(), name='billboard-preview'),
    path('<int:billboard_id>/calendar/', BillboardCalendarView.as_view(), name='billboard-calendar'),
    path('<int:pk>/', BillboardDetailView.as_view(), name='billboard-detail'),
    path('<int:billboard_id>/track-view/', track_billboard_view, name='track-billboard-view'),
    path('<int:billboard_id>/increment-view/', track_billboard_view, name='increment-billboard-view'),
    path('<int:billboard_id>/toggle-active/', toggle_billboard_active, name='toggle-billboard-active'),
    path('<int:billboard_id>/availability/', BillboardAvailabilityView.as_view(), name='billboard-availability'),
    path('pending/', get_pending_billboards, name='get-pending-billboards'),
    path('<int:billboard_id>/approval-status/', update_billboard_approval_status, name='update-billboard-approval-status'),
    path('wishlist/', WishlistView.as_view(), name='wishlist'),
    path('wishlist/<int:billboard_id>/remove/', WishlistRemoveView.as_view(), name='wishlist-remove'),
    path('wishlist/<int:billboard_id>/toggle/', WishlistToggleView.as_view(), name='wishlist-toggle'),
    path('<int:billboard_id>/track-lead/', track_billboard_lead, name='track-lead'),
]
