# Generated manually for OohMediaTypeAttribute (Phase 3)
# Idempotent: EC2 may already have the table from an earlier partial deploy.

import django.db.models.deletion
from django.db import migrations, models

from core.migration_helpers import table_exists


def create_ooh_media_type_attribute_if_missing(apps, schema_editor):
    table = 'billboards_oohmediatypeattribute'
    if table_exists(schema_editor, table):
        return
    Model = apps.get_model('billboards', 'OohMediaTypeAttribute')
    schema_editor.create_model(Model)


def delete_ooh_media_type_attribute_if_present(apps, schema_editor):
    table = 'billboards_oohmediatypeattribute'
    if not table_exists(schema_editor, table):
        return
    Model = apps.get_model('billboards', 'OohMediaTypeAttribute')
    schema_editor.delete_model(Model)


class Migration(migrations.Migration):

    dependencies = [
        ('billboards', '0016_billboard_currency'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
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
            ],
            database_operations=[
                migrations.RunPython(
                    create_ooh_media_type_attribute_if_missing,
                    delete_ooh_media_type_attribute_if_present,
                ),
            ],
        ),
    ]
