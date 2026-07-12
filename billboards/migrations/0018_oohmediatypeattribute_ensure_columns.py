# Ensure OohMediaTypeAttribute columns match the model (drifted EC2 schema).

from django.db import migrations, models

from core.migration_helpers import column_exists, table_exists


REQUIRED_COLUMNS = [
    ('key', 'varchar(80) NOT NULL DEFAULT \'\''),
    ('label', 'varchar(120) NOT NULL DEFAULT \'\''),
    ('field_type', 'varchar(20) NOT NULL DEFAULT \'text\''),
    ('required', 'boolean NOT NULL DEFAULT false'),
    ('options', 'jsonb NULL'),
    ('validation', 'jsonb NULL'),
    ('order', 'integer NOT NULL DEFAULT 0'),
    ('help_text', 'varchar(255) NOT NULL DEFAULT \'\''),
    ('is_active', 'boolean NOT NULL DEFAULT true'),
]


def ensure_attribute_columns(apps, schema_editor):
    table = 'billboards_oohmediatypeattribute'
    if not table_exists(schema_editor, table):
        return

    vendor = schema_editor.connection.vendor
    with schema_editor.connection.cursor() as cursor:
        for column, typedef in REQUIRED_COLUMNS:
            if column_exists(schema_editor, table, column):
                continue
            if vendor == 'sqlite':
                if column in ('required', 'is_active'):
                    typedef = 'bool NOT NULL DEFAULT 0' if column == 'required' else 'bool NOT NULL DEFAULT 1'
                elif column in ('options', 'validation'):
                    typedef = 'TEXT NULL'
                elif column == 'order':
                    typedef = 'integer NOT NULL DEFAULT 0'
            cursor.execute(f'ALTER TABLE {table} ADD COLUMN {column} {typedef}')


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('billboards', '0017_oohmediatypeattribute'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[],
            database_operations=[
                migrations.RunPython(ensure_attribute_columns, noop_reverse),
            ],
        ),
    ]
