"""
Seed ALL states, cities, lat/long coordinates, and boundaries from SQL dump files.
Imports every row from the dump with no row limit. Verifies counts match at the end.

Usage:
    python manage.py seed_locations
    python manage.py seed_locations --no-flush
    python manage.py seed_locations --only cities
"""
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from locations.models import City, CityBoundary, State, StateBoundary
from locations.sql_loader import (
    count_rows,
    iter_mysql_insert_rows,
    map_city_boundary_row,
    map_city_row,
    map_state_boundary_row,
    map_state_row,
)

DEFAULT_STATES_CITIES_SQL = 'states-and-cities.sql'
DEFAULT_BOUNDARIES_SQL = 'city-and-state-boundries.sql'

DATASETS = {
    'states': {
        'sql_key': 'states_cities',
        'table': 'states_capitals',
        'model': State,
    },
    'cities': {
        'sql_key': 'states_cities',
        'table': 'states_cities',
        'model': City,
    },
    'city-boundaries': {
        'sql_key': 'boundaries',
        'table': 'city_boundaries',
        'model': CityBoundary,
    },
    'state-boundaries': {
        'sql_key': 'boundaries',
        'table': 'state_boundaries',
        'model': StateBoundary,
    },
}


class Command(BaseCommand):
    help = 'Seed complete location data (all states, cities, coordinates, boundaries) from SQL dumps'

    def add_arguments(self, parser):
        parser.add_argument(
            '--states-cities-sql',
            default=DEFAULT_STATES_CITIES_SQL,
            help='Path to states-and-cities.sql dump (default: project root)',
        )
        parser.add_argument(
            '--boundaries-sql',
            default=DEFAULT_BOUNDARIES_SQL,
            help='Path to city-and-state-boundries.sql dump (default: project root)',
        )
        parser.add_argument(
            '--only',
            choices=['all', 'states', 'cities', 'city-boundaries', 'state-boundaries'],
            default='all',
            help='Seed only a specific dataset',
        )
        parser.add_argument(
            '--no-flush',
            action='store_true',
            help='Keep existing rows instead of clearing targeted tables before import',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=1000,
            help='Insert batch size for large tables (does not limit total rows imported)',
        )
        parser.add_argument(
            '--skip-verify',
            action='store_true',
            help='Skip post-import row count verification',
        )

    def handle(self, *args, **options):
        base_dir = Path(settings.BASE_DIR)
        sql_files = {
            'states_cities': self._resolve_path(base_dir, options['states_cities_sql']),
            'boundaries': self._resolve_path(base_dir, options['boundaries_sql']),
        }
        only = options['only']
        batch_size = max(1, options['batch_size'])
        targets = self._selected_targets(only)

        self._validate_files(targets, sql_files)

        if not options['no_flush']:
            self._flush_tables(targets)

        imported = {}

        if 'states' in targets:
            imported['states'] = self._seed_states(sql_files['states_cities'])

        if 'cities' in targets:
            imported['cities'] = self._seed_cities(sql_files['states_cities'], batch_size)

        if 'city-boundaries' in targets:
            imported['city-boundaries'] = self._seed_city_boundaries(
                sql_files['boundaries'],
                batch_size,
            )

        if 'state-boundaries' in targets:
            imported['state-boundaries'] = self._seed_state_boundaries(sql_files['boundaries'])

        if not options['skip_verify']:
            self._verify_complete_import(targets, sql_files, imported)

        self.stdout.write(self.style.SUCCESS('Complete location seeding finished.'))

    def _resolve_path(self, base_dir: Path, raw_path: str) -> Path:
        path = Path(raw_path)
        if path.is_absolute():
            return path
        return base_dir / path

    def _selected_targets(self, only: str) -> list[str]:
        if only == 'all':
            return ['states', 'cities', 'city-boundaries', 'state-boundaries']
        return [only]

    def _validate_files(self, targets: list[str], sql_files: dict[str, Path]):
        needs_states_cities = any(
            DATASETS[target]['sql_key'] == 'states_cities' for target in targets
        )
        needs_boundaries = any(
            DATASETS[target]['sql_key'] == 'boundaries' for target in targets
        )

        if needs_states_cities and not sql_files['states_cities'].exists():
            raise CommandError(f'File not found: {sql_files["states_cities"]}')

        if needs_boundaries and not sql_files['boundaries'].exists():
            raise CommandError(f'File not found: {sql_files["boundaries"]}')

    def _flush_tables(self, targets: list[str]):
        flush_order = ['state-boundaries', 'city-boundaries', 'cities', 'states']
        for target in flush_order:
            if target not in targets:
                continue
            model = DATASETS[target]['model']
            deleted, _ = model.objects.all().delete()
            self.stdout.write(f'Flushed {deleted} rows from {model.__name__}')

    def _seed_states(self, sql_path: Path) -> int:
        expected = count_rows(sql_path, 'states_capitals')
        self.stdout.write(f'Importing all {expected} states...')

        created = 0
        for row in iter_mysql_insert_rows(sql_path, 'states_capitals'):
            payload = map_state_row(row)
            legacy_id = payload.pop('legacy_id')
            State.objects.update_or_create(legacy_id=legacy_id, defaults=payload)
            created += 1

        self.stdout.write(self.style.SUCCESS(f'States imported: {created}/{expected}'))
        return created

    def _seed_cities(self, sql_path: Path, batch_size: int) -> int:
        expected = count_rows(sql_path, 'states_cities')
        self.stdout.write(f'Importing all {expected} cities (no row limit)...')

        batch: list[City] = []
        total = 0

        for row in iter_mysql_insert_rows(sql_path, 'states_cities'):
            batch.append(City(**map_city_row(row)))
            if len(batch) >= batch_size:
                total += self._insert_city_batch(batch, batch_size)
                self.stdout.write(f'  Cities imported: {total}/{expected}')
                batch.clear()

        if batch:
            total += self._insert_city_batch(batch, batch_size)
            self.stdout.write(f'  Cities imported: {total}/{expected}')

        self.stdout.write(self.style.SUCCESS(f'Cities imported: {total}/{expected}'))
        return total

    def _insert_city_batch(self, batch: list[City], batch_size: int) -> int:
        with transaction.atomic():
            City.objects.bulk_create(batch, batch_size=batch_size)
        return len(batch)

    def _seed_city_boundaries(self, sql_path: Path, batch_size: int) -> int:
        expected = count_rows(sql_path, 'city_boundaries')
        self.stdout.write(f'Importing all {expected} city boundaries (full polygon data)...')

        batch: list[CityBoundary] = []
        total = 0

        for row in iter_mysql_insert_rows(sql_path, 'city_boundaries'):
            batch.append(CityBoundary(**map_city_boundary_row(row)))
            if len(batch) >= batch_size:
                total += self._insert_city_boundary_batch(batch, batch_size)
                self.stdout.write(f'  City boundaries imported: {total}/{expected}')
                batch.clear()

        if batch:
            total += self._insert_city_boundary_batch(batch, batch_size)
            self.stdout.write(f'  City boundaries imported: {total}/{expected}')

        self.stdout.write(self.style.SUCCESS(f'City boundaries imported: {total}/{expected}'))
        return total

    def _insert_city_boundary_batch(self, batch: list[CityBoundary], batch_size: int) -> int:
        with transaction.atomic():
            CityBoundary.objects.bulk_create(batch, batch_size=batch_size)
        return len(batch)

    def _seed_state_boundaries(self, sql_path: Path) -> int:
        expected = count_rows(sql_path, 'state_boundaries')
        self.stdout.write(f'Importing all {expected} state boundaries (full polygon data)...')

        created = 0
        for row in iter_mysql_insert_rows(sql_path, 'state_boundaries'):
            payload = map_state_boundary_row(row)
            legacy_id = payload.pop('legacy_id')
            StateBoundary.objects.update_or_create(legacy_id=legacy_id, defaults=payload)
            created += 1

        self.stdout.write(self.style.SUCCESS(f'State boundaries imported: {created}/{expected}'))
        return created

    def _verify_complete_import(
        self,
        targets: list[str],
        sql_files: dict[str, Path],
        imported: dict[str, int],
    ):
        self.stdout.write('')
        self.stdout.write('=' * 60)
        self.stdout.write('VERIFICATION (SQL dump vs database)')
        self.stdout.write('=' * 60)

        mismatches = []

        for target in targets:
            config = DATASETS[target]
            sql_path = sql_files[config['sql_key']]
            expected = count_rows(sql_path, config['table'])
            actual = config['model'].objects.count()
            processed = imported.get(target, 0)

            status = 'OK' if expected == actual == processed else 'MISMATCH'
            line = (
                f'{target:18} expected={expected:6} imported={processed:6} '
                f'in_db={actual:6} [{status}]'
            )
            if status == 'OK':
                self.stdout.write(self.style.SUCCESS(line))
            else:
                self.stdout.write(self.style.ERROR(line))
                mismatches.append(target)

        if 'states' in targets or 'cities' in targets:
            state_lat = State.objects.exclude(latitude__isnull=True).count()
            state_lng = State.objects.exclude(longitude__isnull=True).count()
            city_lat = City.objects.exclude(latitude='').count()
            city_lng = City.objects.exclude(longitude='').count()
            city_coords = City.objects.exclude(coordinates='').count()

            self.stdout.write('')
            self.stdout.write(f'States with latitude : {state_lat}/{State.objects.count()}')
            self.stdout.write(f'States with longitude: {state_lng}/{State.objects.count()}')
            self.stdout.write(f'Cities with coordinates string: {city_coords}/{City.objects.count()}')
            self.stdout.write(f'Cities with latitude : {city_lat}/{City.objects.count()}')
            self.stdout.write(f'Cities with longitude: {city_lng}/{City.objects.count()}')

        if 'city-boundaries' in targets:
            empty_boundaries = CityBoundary.objects.filter(boundary=[]).count()
            self.stdout.write(
                f'City boundaries with polygon data: '
                f'{CityBoundary.objects.count() - empty_boundaries}/{CityBoundary.objects.count()}'
            )

        if 'state-boundaries' in targets:
            empty_boundaries = StateBoundary.objects.filter(boundary=[]).count()
            self.stdout.write(
                f'State boundaries with polygon data: '
                f'{StateBoundary.objects.count() - empty_boundaries}/{StateBoundary.objects.count()}'
            )

        self.stdout.write('=' * 60)

        if mismatches:
            raise CommandError(
                'Import incomplete. Mismatched datasets: ' + ', '.join(mismatches)
            )

        self.stdout.write(self.style.SUCCESS('All requested data imported completely.'))
