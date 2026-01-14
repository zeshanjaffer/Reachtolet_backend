# Generated manually on 2026-01-14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0007_remove_username_completely'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='username',
            field=models.CharField(blank=True, help_text='Optional username. Email can also be used for login.', max_length=150, null=True, unique=True),
        ),
    ]

