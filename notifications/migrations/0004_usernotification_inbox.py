# Generated manually for in-app notification inbox (Phase 5)

import uuid

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


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
]


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0003_performance_indexes'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='notificationpreference',
            name='chat_messages_enabled',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='notificationtemplate',
            name='notification_type',
            field=models.CharField(
                choices=NOTIFICATION_TYPE_CHOICES,
                db_index=True,
                max_length=50,
            ),
        ),
        migrations.AlterField(
            model_name='pushnotification',
            name='notification_type',
            field=models.CharField(
                choices=NOTIFICATION_TYPE_CHOICES,
                db_index=True,
                max_length=50,
            ),
        ),
        migrations.CreateModel(
            name='UserNotification',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('notification_type', models.CharField(choices=NOTIFICATION_TYPE_CHOICES, db_index=True, max_length=50)),
                ('title', models.CharField(max_length=255)),
                ('body', models.TextField()),
                ('data', models.JSONField(blank=True, default=dict)),
                ('related_object_type', models.CharField(blank=True, default='', max_length=50)),
                ('related_object_id', models.PositiveIntegerField(blank=True, null=True)),
                ('is_read', models.BooleanField(db_index=True, default=False)),
                ('read_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('recipient', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='inbox_notifications',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='usernotification',
            index=models.Index(fields=['recipient', 'is_read'], name='notificatio_recipie_inbox_r_idx'),
        ),
        migrations.AddIndex(
            model_name='usernotification',
            index=models.Index(fields=['recipient', 'created_at'], name='notificatio_recipie_inbox_c_idx'),
        ),
    ]
