# Generated manually for billboard currency field (Phase 2)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('billboards', '0015_oohmediatype_billboard_media_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='billboard',
            name='currency',
            field=models.CharField(
                blank=True,
                help_text='ISO 4217 currency code copied from owner preferred_currency on create',
                max_length=3,
                null=True,
            ),
        ),
    ]
