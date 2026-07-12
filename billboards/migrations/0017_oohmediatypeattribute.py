# Generated manually for OohMediaTypeAttribute (Phase 3)

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('billboards', '0016_billboard_currency'),
    ]

    operations = [
        migrations.CreateModel(
            name='OohMediaTypeAttribute',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.SlugField(max_length=80)),
                ('label', models.CharField(max_length=120)),
                ('field_type', models.CharField(
                    choices=[
                        ('text', 'Text'),
                        ('number', 'Number'),
                        ('integer', 'Integer'),
                        ('boolean', 'Boolean'),
                        ('select', 'Select'),
                        ('multiselect', 'Multi-select'),
                    ],
                    max_length=20,
                )),
                ('required', models.BooleanField(default=False)),
                ('options', models.JSONField(blank=True, null=True)),
                ('validation', models.JSONField(blank=True, null=True)),
                ('order', models.PositiveIntegerField(default=0)),
                ('help_text', models.CharField(blank=True, default='', max_length=255)),
                ('is_active', models.BooleanField(default=True)),
                ('media_type', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='attributes',
                    to='billboards.oohmediatype',
                )),
            ],
            options={
                'verbose_name': 'OOH media type attribute',
                'verbose_name_plural': 'OOH media type attributes',
                'ordering': ['order', 'id'],
                'unique_together': {('media_type', 'key')},
            },
        ),
    ]
