"""
Seed dynamic specification attributes for digital/static OOH media types.

Usage:
  python manage.py seed_media_type_attributes
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from billboards.models import OohMediaType, OohMediaTypeAttribute

DIGITAL_ATTRIBUTES = [
    {
        'key': 'loop_duration_seconds',
        'label': 'Loop duration (seconds)',
        'field_type': 'integer',
        'required': True,
        'options': None,
        'validation': {'min': 1, 'max': 3600},
        'order': 10,
        'help_text': 'Total loop length in seconds (e.g. 60).',
    },
    {
        'key': 'allowed_video_lengths',
        'label': 'Allowed video lengths',
        'field_type': 'multiselect',
        'required': True,
        'options': [10, 20, 30, 40, 60],
        'validation': None,
        'order': 20,
        'help_text': 'Permitted spot durations within the loop.',
    },
    {
        'key': 'price_per_second',
        'label': 'Price per second',
        'field_type': 'number',
        'required': True,
        'options': None,
        'validation': {'min': 0},
        'order': 30,
        'help_text': 'Price per second of airtime (currency is on the billboard).',
    },
    {
        'key': 'slots',
        'label': 'Slots',
        'field_type': 'text',
        'required': False,
        'options': None,
        'validation': None,
        'order': 40,
        'help_text': 'JSON array of slot objects (slot_number, duration_seconds, status).',
    },
]

STATIC_ATTRIBUTES = [
    {
        'key': 'price_per_month',
        'label': 'Price per month',
        'field_type': 'number',
        'required': True,
        'options': None,
        'validation': {'min': 0},
        'order': 10,
        'help_text': 'Monthly rental price (currency is on the billboard).',
    },
    {
        'key': 'printing_cost',
        'label': 'Printing cost',
        'field_type': 'number',
        'required': False,
        'options': None,
        'validation': {'min': 0},
        'order': 20,
        'help_text': 'One-time printing / production cost.',
    },
]


class Command(BaseCommand):
    help = 'Seed OohMediaTypeAttribute rows for digital/static media types'

    def add_arguments(self, parser):
        parser.add_argument(
            '--replace',
            action='store_true',
            help='Delete existing attributes for matched types before seeding',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        digital_qs = OohMediaType.objects.filter(
            is_active=True, is_selectable=True, slug__icontains='digital'
        )
        static_qs = OohMediaType.objects.filter(
            is_active=True, is_selectable=True, slug__icontains='static'
        )

        created = 0
        updated = 0

        for media_type in digital_qs:
            c, u = self._seed_type(media_type, DIGITAL_ATTRIBUTES, options['replace'])
            created += c
            updated += u

        for media_type in static_qs:
            c, u = self._seed_type(media_type, STATIC_ATTRIBUTES, options['replace'])
            created += c
            updated += u

        self.stdout.write(self.style.SUCCESS(
            f'Seeded attributes: {created} created, {updated} updated '
            f'(digital types={digital_qs.count()}, static types={static_qs.count()})'
        ))

    def _seed_type(self, media_type, attribute_defs, replace):
        created = 0
        updated = 0
        if replace:
            media_type.attributes.all().delete()

        for defn in attribute_defs:
            obj, was_created = OohMediaTypeAttribute.objects.update_or_create(
                media_type=media_type,
                key=defn['key'],
                defaults={
                    'label': defn['label'],
                    'field_type': defn['field_type'],
                    'required': defn['required'],
                    'options': defn['options'],
                    'validation': defn['validation'],
                    'order': defn['order'],
                    'help_text': defn['help_text'],
                    'placeholder': defn.get('placeholder', ''),
                    'is_active': True,
                },
            )
            if was_created:
                created += 1
            else:
                updated += 1
        return created, updated
