"""Helpers for idempotent migrations against drifted production DBs."""


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
