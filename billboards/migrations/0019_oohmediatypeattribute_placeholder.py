# Align OohMediaTypeAttribute.placeholder with existing EC2 column.

from django.db import migrations, models

from core.migration_helpers import RunPythonToState, column_exists, table_exists


def ensure_placeholder(apps, schema_editor):
    table = 'billboards_oohmediatypeattribute'
    if not table_exists(schema_editor, table):
        return

    with schema_editor.connection.cursor() as cursor:
        if not column_exists(schema_editor, table, 'placeholder'):
            if schema_editor.connection.vendor == 'postgresql':
                cursor.execute(
                    f"ALTER TABLE {table} "
                    f"ADD COLUMN placeholder varchar(255) NOT NULL DEFAULT ''"
                )
            else:
                cursor.execute(
                    f"ALTER TABLE {table} "
                    f"ADD COLUMN placeholder varchar(255) NOT NULL DEFAULT ''"
                )
            return

        if schema_editor.connection.vendor == 'postgresql':
            cursor.execute(
                f"ALTER TABLE {table} ALTER COLUMN placeholder SET DEFAULT ''"
            )
            cursor.execute(
                f"UPDATE {table} SET placeholder = '' WHERE placeholder IS NULL"
            )
            cursor.execute(
                f"ALTER TABLE {table} ALTER COLUMN placeholder SET NOT NULL"
            )


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('billboards', '0018_oohmediatypeattribute_ensure_columns'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddField(
                    model_name='oohmediatypeattribute',
                    name='placeholder',
                    field=models.CharField(blank=True, default='', max_length=255),
                ),
            ],
            database_operations=[
                RunPythonToState(ensure_placeholder, noop_reverse),
            ],
        ),
    ]
