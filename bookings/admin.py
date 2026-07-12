from django.contrib import admin

from .models import Booking, BookingContent, Payment


class BookingContentInline(admin.StackedInline):
    model = BookingContent
    extra = 0


class PaymentInline(admin.StackedInline):
    model = Payment
    extra = 0


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'billboard',
        'advertiser',
        'media_owner',
        'start_date',
        'end_date',
        'status',
        'total_price',
        'currency',
        'created_at',
    )
    list_filter = ('status', 'currency', 'created_at')
    search_fields = ('id', 'advertiser__email', 'media_owner__email', 'billboard__city')
    raw_id_fields = ('billboard', 'advertiser', 'media_owner')
    inlines = [BookingContentInline, PaymentInline]


@admin.register(BookingContent)
class BookingContentAdmin(admin.ModelAdmin):
    list_display = ('id', 'booking', 'content_type', 'status', 'submitted_at', 'reviewed_at')
    list_filter = ('content_type', 'status')


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'booking', 'amount', 'currency', 'status', 'gateway_ref', 'created_at')
    list_filter = ('status', 'currency')
