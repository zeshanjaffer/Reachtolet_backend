# Generated manually for OOH media type catalog

import django.db.models.deletion
from django.db import migrations, models


def seed_media_types(apps, schema_editor):
    OohMediaType = apps.get_model('billboards', 'OohMediaType')
    from billboards.media_types_data import MEDIA_TYPE_SEED

    slug_to_id = {}
    for name, slug, category, is_digital, is_selectable, sort_order, parent_slug in MEDIA_TYPE_SEED:
        obj, _ = OohMediaType.objects.update_or_create(
            slug=slug,
            defaults={
                'name': name,
                'category': category,
                'is_digital': is_digital,
                'is_selectable': is_selectable,
                'sort_order': sort_order,
                'is_active': True,
            },
        )
        slug_to_id[slug] = obj.pk

    for name, slug, category, is_digital, is_selectable, sort_order, parent_slug in MEDIA_TYPE_SEED:
        if parent_slug:
            OohMediaType.objects.filter(slug=slug).update(parent_id=slug_to_id[parent_slug])


def backfill_billboard_media_types(apps, schema_editor):
    Billboard = apps.get_model('billboards', 'Billboard')
    OohMediaType = apps.get_model('billboards', 'OohMediaType')

    for billboard in Billboard.objects.filter(media_type__isnull=True).exclude(ooh_media_type=''):
        media_type = OohMediaType.objects.filter(
            name__iexact=billboard.ooh_media_type,
            is_active=True,
        ).first()
        if media_type:
            billboard.media_type_id = media_type.pk
            billboard.save(update_fields=['media_type_id'])


class Migration(migrations.Migration):

    dependencies = [
        ('billboards', '0014_billboard_location_postgis'),
    ]

    operations = [
        migrations.CreateModel(
            name='OohMediaType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('slug', models.SlugField(max_length=120, unique=True)),
                ('category', models.CharField(
                    choices=[
                        ('digital', 'Digital'),
                        ('static', 'Static'),
                        ('place', 'Place Based'),
                        ('transit', 'Transit & Mobile'),
                        ('other', 'Other'),
                    ],
                    db_index=True,
                    max_length=20,
                )),
                ('is_selectable', models.BooleanField(
                    default=True,
                    help_text='False for group headers like "All Digital" (picker only shows selectable types).',
                )),
                ('is_digital', models.BooleanField(
                    default=False,
                    help_text='True = use digital specifications JSON form on create.',
                )),
                ('sort_order', models.PositiveIntegerField(default=0)),
                ('is_active', models.BooleanField(db_index=True, default=True)),
                ('parent', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='children',
                    to='billboards.oohmediatype',
                )),
            ],
            options={
                'verbose_name': 'OOH media type',
                'verbose_name_plural': 'OOH media types',
                'ordering': ['sort_order', 'name'],
            },
        ),
        migrations.AddField(
            model_name='billboard',
            name='media_type',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='billboards',
                to='billboards.oohmediatype',
            ),
        ),
        migrations.RunPython(seed_media_types, migrations.RunPython.noop),
        migrations.RunPython(backfill_billboard_media_types, migrations.RunPython.noop),
    ]
