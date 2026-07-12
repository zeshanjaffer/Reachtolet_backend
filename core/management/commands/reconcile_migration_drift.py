"""
Fake pending migrations when the DB already has the objects (schema drift).

Use on EC2 when Postgres was updated earlier but django_migrations is behind:

  python manage.py reconcile_migration_drift
  python manage.py migrate
"""

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.db.migrations.recorder import MigrationRecorder

from core.migration_helpers import column_exists, table_exists


def _preference_ready(schema_editor):
    return table_exists(schema_editor, 'notifications_notification_preference')


def _inbox_ready(schema_editor):
    return table_exists(schema_editor, 'notifications_usernotification') or column_exists(
        schema_editor, 'notifications_notification_preference', 'chat_messages_enabled'
    )


def _profile_ready(schema_editor):
    return column_exists(schema_editor, 'users_user', 'preferred_currency') or table_exists(
        schema_editor, 'users_passwordresetotp'
    )


# (app, migration_name) -> predicate(schema_editor) that means "already applied in DB"
DRIFT_CHECKS = {
    ('notifications', '0004_usernotification_inbox'): _inbox_ready,
    ('users', '0014_profile_setup_and_password_reset'): _profile_ready,
}


class Command(BaseCommand):
    help = 'Fake-apply pending migrations that already exist in the database'

    def handle(self, *args, **options):
        executor = MigrationExecutor(connection)
        plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
        if not plan:
            self.stdout.write(self.style.SUCCESS('No pending migrations.'))
            return

        class _Editor:
            connection = connection

        schema_editor = _Editor()
        faked = []

        for migration, _backwards in plan:
            key = (migration.app_label, migration.name)
            checker = DRIFT_CHECKS.get(key)
            if checker is None:
                continue
            if not checker(schema_editor):
                self.stdout.write(
                    f'Skip fake {migration.app_label}.{migration.name} '
                    f'(DB objects not detected — will try real migrate)'
                )
                continue
            self.stdout.write(
                self.style.WARNING(
                    f'Faking {migration.app_label}.{migration.name} '
                    f'(objects already in Postgres)'
                )
            )
            call_command(
                'migrate',
                migration.app_label,
                migration.name,
                fake=True,
                verbosity=1,
            )
            faked.append(key)

        if faked:
            self.stdout.write(self.style.SUCCESS(f'Faked {len(faked)} migration(s).'))
        else:
            self.stdout.write('Nothing needed faking from the drift list.')

        self.stdout.write('Now run: python manage.py migrate')
