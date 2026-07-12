# Generated manually for in-app notification inbox (Phase 5)
# Idempotent for drifted EC2 DBs where columns/tables already exist.

import uuid

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

from core.migration_helpers import RunPythonToState, column_exists, index_exists, table_exists


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


def apply_inbox_schema(apps, schema_editor):
    # Custom db_table from notifications.0001_initial (not the Django default name).
    pref_table = 'notifications_notification_preference'
    if table_exists(schema_editor, pref_table):
        if not column_exists(schema_editor, pref_table, 'chat_messages_enabled'):
            with schema_editor.connection.cursor() as cursor:
                if schema_editor.connection.vendor == 'postgresql':
                    cursor.execute(
                        f'ALTER TABLE {pref_table} '
                        f'ADD COLUMN chat_messages_enabled boolean DEFAULT true NOT NULL'
                    )
                else:
                    cursor.execute(
                        f'ALTER TABLE {pref_table} '
                        f'ADD COLUMN chat_messages_enabled bool NOT NULL DEFAULT 1'
                    )
    # If preference table is missing, skip column add — earlier notifications
    # migrations / schema must be repaired separately; inbox table can still be created.

    inbox_table = 'notifications_usernotification'
    if not table_exists(schema_editor, inbox_table):
        UserNotification = apps.get_model('notifications', 'UserNotification')
        schema_editor.create_model(UserNotification)

    if not table_exists(schema_editor, inbox_table):
        return

    for index_name, columns_sql in (
        ('notificatio_recipie_inbox_r_idx', '(recipient_id, is_read)'),
        ('notificatio_recipie_inbox_c_idx', '(recipient_id, created_at)'),
    ):
        if index_exists(schema_editor, index_name):
            continue
        with schema_editor.connection.cursor() as cursor:
            cursor.execute(
                f'CREATE INDEX {index_name} ON {inbox_table} {columns_sql}'
            )


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0003_performance_indexes'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
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
            ],
            database_operations=[
                RunPythonToState(apply_inbox_schema, noop_reverse),
            ],
        ),
    ]
