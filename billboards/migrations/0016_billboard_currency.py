# Generated manually for billboard currency field (Phase 2)
# Idempotent: EC2 may already have the column from an earlier partial deploy.

from django.db import migrations, models


def add_currency_if_missing(apps, schema_editor):
    table = 'billboards_billboard'
    column = 'currency'
    with schema_editor.connection.cursor() as cursor:
        if schema_editor.connection.vendor == 'postgresql':
            cursor.execute(
                """
                SELECT 1
                FROM information_schema.columns
                WHERE table_name = %s AND column_name = %s
                """,
                [table, column],
            )
            if cursor.fetchone():
                return
            cursor.execute(
                f'ALTER TABLE {table} ADD COLUMN {column} varchar(3) NULL'
            )
        else:
            # SQLite / local: use Django schema editor path via state only when missing
            cursor.execute(f'PRAGMA table_info({table})')
            existing = {row[1] for row in cursor.fetchall()}
            if column in existing:
                return
            cursor.execute(
                f'ALTER TABLE {table} ADD COLUMN {column} varchar(3) NULL'
            )


def drop_currency_if_present(apps, schema_editor):
    table = 'billboards_billboard'
    column = 'currency'
    with schema_editor.connection.cursor() as cursor:
        if schema_editor.connection.vendor == 'postgresql':
            cursor.execute(
                f'ALTER TABLE {table} DROP COLUMN IF EXISTS {column}'
            )
        else:
            cursor.execute(f'PRAGMA table_info({table})')
            existing = {row[1] for row in cursor.fetchall()}
            if column in existing:
                cursor.execute(
                    f'ALTER TABLE {table} DROP COLUMN {column}'
                )


class Migration(migrations.Migration):

    dependencies = [
        ('billboards', '0015_oohmediatype_billboard_media_type'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddField(
                    model_name='billboard',
                    name='currency',
                    field=models.CharField(
                        blank=True,
                        help_text=(
                            'ISO 4217 currency code copied from owner '
                            'preferred_currency on create'
                        ),
                        max_length=3,
                        null=True,
                    ),
                ),
            ],
            database_operations=[
                migrations.RunPython(
                    add_currency_if_missing,
                    drop_currency_if_present,
                ),
            ],
        ),
    ]
