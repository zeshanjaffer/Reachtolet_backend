"""Helpers for idempotent migrations against drifted production DBs."""

from django.db import migrations


class RunPythonToState(migrations.RunPython):
    """
    Like RunPython, but passes to_state.apps.

    Required when used inside SeparateDatabaseAndState so CreateModel /
    AddField from state_operations are visible to apps.get_model().
    """

    def database_forwards(self, app_label, schema_editor, from_state, to_state):
        to_state.clear_delayed_apps_cache()
        if self.code is not None:
            self.code(to_state.apps, schema_editor)

    def database_backwards(self, app_label, schema_editor, from_state, to_state):
        to_state.clear_delayed_apps_cache()
        if self.reverse_code is not None:
            self.reverse_code(to_state.apps, schema_editor)


def table_exists(schema_editor, table_name: str) -> bool:
    with schema_editor.connection.cursor() as cursor:
        if schema_editor.connection.vendor == 'postgresql':
            cursor.execute(
                """
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = %s
                """,
                [table_name],
            )
        else:
            cursor.execute(
                "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = %s",
                [table_name],
            )
        return cursor.fetchone() is not None


def column_exists(schema_editor, table_name: str, column_name: str) -> bool:
    with schema_editor.connection.cursor() as cursor:
        if schema_editor.connection.vendor == 'postgresql':
            cursor.execute(
                """
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = %s
                  AND column_name = %s
                """,
                [table_name, column_name],
            )
        else:
            cursor.execute(f'PRAGMA table_info({table_name})')
            return any(row[1] == column_name for row in cursor.fetchall())
        return cursor.fetchone() is not None


def index_exists(schema_editor, index_name: str) -> bool:
    with schema_editor.connection.cursor() as cursor:
        if schema_editor.connection.vendor == 'postgresql':
            cursor.execute(
                'SELECT 1 FROM pg_indexes WHERE indexname = %s',
                [index_name],
            )
            return cursor.fetchone() is not None
        cursor.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'index' AND name = %s",
            [index_name],
        )
        return cursor.fetchone() is not None
