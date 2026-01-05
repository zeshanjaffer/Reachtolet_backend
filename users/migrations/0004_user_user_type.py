# Generated migration for user_type field

from django.db import migrations, models


def set_default_user_type(apps, schema_editor):
    """
    Set default user_type for existing users.
    All existing users default to 'advertiser' for safety.
    Admin can manually update users who should be media_owners.
    """
    User = apps.get_model('users', 'User')
    # Set all existing users as advertisers (safe default)
    User.objects.filter(user_type__isnull=True).update(user_type='advertiser')


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_alter_user_options_user_country_code_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='user_type',
            field=models.CharField(
                choices=[('advertiser', 'Advertiser'), ('media_owner', 'Media Owner')],
                default='advertiser',
                help_text='User role: advertiser or media_owner',
                max_length=20
            ),
        ),
        migrations.RunPython(set_default_user_type, migrations.RunPython.noop),
    ]

