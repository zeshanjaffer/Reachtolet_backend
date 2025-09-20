from django.urls import path
from .views import (
    BillboardListCreateView, 
    BillboardDetailView, 
    BillboardImageUploadView, 
    MyBillboardsView,
    WishlistView,
    WishlistRemoveView,
    WishlistToggleView,
    track_billboard_lead,
    track_billboard_view,  # NEW: Import the view tracking function
    toggle_billboard_active  # NEW: Import the toggle active function
)

urlpatterns = [
    # Billboard endpoints
    path('', BillboardListCreateView.as_view(), name='billboard-list-create'),
    path('my-billboards/', MyBillboardsView.as_view(), name='my-billboards'),
    path('<int:pk>/', BillboardDetailView.as_view(), name='billboard-detail'),
    path('upload-image/', BillboardImageUploadView.as_view(), name='billboard-upload-image'),
    path('<int:billboard_id>/track-view/', track_billboard_view, name='track-billboard-view'),
    path('<int:billboard_id>/increment-view/', track_billboard_view, name='increment-billboard-view'),
    path('<int:billboard_id>/toggle-active/', toggle_billboard_active, name='toggle-billboard-active'),
    
    # Wishlist endpoints
    path('wishlist/', WishlistView.as_view(), name='wishlist'),
    path('wishlist/<int:billboard_id>/remove/', WishlistRemoveView.as_view(), name='wishlist-remove'),
    path('wishlist/<int:billboard_id>/toggle/', WishlistToggleView.as_view(), name='wishlist-toggle'),
    
    # Simple lead tracking endpoint
    path('<int:billboard_id>/track-lead/', track_billboard_lead, name='track-lead'),
]