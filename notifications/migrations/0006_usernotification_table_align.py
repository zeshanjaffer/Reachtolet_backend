# Align UserNotification with the live table name/schema.

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0005_booking_notification_types'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterModelTable(
                    name='usernotification',
                    table='notifications_user_notification',
                ),
            ],
            database_operations=[
                migrations.RunSQL(
                    sql="""
                    ALTER TABLE notifications_user_notification
                      ADD COLUMN IF NOT EXISTS related_object_type varchar(50) NOT NULL DEFAULT '';
                    ALTER TABLE notifications_user_notification
                      ADD COLUMN IF NOT EXISTS related_object_id integer NULL;
                    """,
                    reverse_sql=migrations.RunSQL.noop,
                ),
            ],
        ),
    ]
