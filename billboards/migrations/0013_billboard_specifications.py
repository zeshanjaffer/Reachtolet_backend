from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('billboards', '0012_add_map_indexes'),
    ]

    operations = [
        migrations.AddField(
            model_name='billboard',
            name='specifications',
            field=models.JSONField(
                blank=True,
                default=dict,
                help_text='Type-specific config from frontend (digital slots, static pricing, etc.)',
            ),
        ),
    ]
