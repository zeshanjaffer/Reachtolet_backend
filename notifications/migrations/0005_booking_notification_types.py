# Add booking-related notification type choices

from django.db import migrations, models


NOTIFICATION_TYPE_CHOICES = [
    ('new_lead', 'New Lead'),
    ('new_view', 'New View'),
    ('wishlist_added', 'Added to Wishlist'),
    ('billboard_activated', 'Billboard Activated'),
    ('billboard_deactivated', 'Billboard Deactivated'),
    ('billboard_approved', 'Billboard Approved'),
    ('billboard_rejected', 'Billboard Rejected'),
    ('price_update', 'Price Update'),
    ('system_message', 'System Message'),
    ('welcome', 'Welcome Message'),
    ('new_chat_message', 'New Chat Message'),
    ('booking_requested', 'Booking Requested'),
    ('booking_accepted', 'Booking Accepted'),
    ('booking_rejected', 'Booking Rejected'),
    ('booking_content_submitted', 'Booking Content Submitted'),
    ('booking_content_rejected', 'Booking Content Rejected'),
    ('booking_confirmed', 'Booking Confirmed'),
]


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0004_usernotification_inbox'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notificationtemplate',
            name='notification_type',
            field=models.CharField(choices=NOTIFICATION_TYPE_CHOICES, db_index=True, max_length=50),
        ),
        migrations.AlterField(
            model_name='pushnotification',
            name='notification_type',
            field=models.CharField(choices=NOTIFICATION_TYPE_CHOICES, db_index=True, max_length=50),
        ),
        migrations.AlterField(
            model_name='usernotification',
            name='notification_type',
            field=models.CharField(choices=NOTIFICATION_TYPE_CHOICES, db_index=True, max_length=50),
        ),
    ]
