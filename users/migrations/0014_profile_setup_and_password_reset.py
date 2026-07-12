# Generated manually for Phase 2 profile setup + Phase 6 password reset / Apple login
# Idempotent for drifted EC2 DBs where columns/tables already exist.

import django.core.validators
from django.db import migrations, models

from core.migration_helpers import column_exists, table_exists


PROFILE_COLUMNS = [
    ('preferred_currency', 'varchar(3) NULL'),
    ('preferred_language', 'varchar(10) NULL'),
    ('profile_type', 'varchar(20) NULL'),
    ('company_name', 'varchar(200) NULL'),
    ('company_size', 'varchar(20) NULL'),
    ('company_website', 'varchar(255) NULL'),
    ('company_address', 'text NULL'),
    ('profile_setup_completed', 'boolean DEFAULT false NOT NULL'),
    ('apple_sub', 'varchar(255) NULL'),
]


def apply_profile_schema(apps, schema_editor):
    table = 'users_user'
    vendor = schema_editor.connection.vendor
    with schema_editor.connection.cursor() as cursor:
        if vendor == 'postgresql':
            cursor.execute(
                f'ALTER TABLE {table} ALTER COLUMN country_code DROP NOT NULL'
            )
            cursor.execute(
                f'ALTER TABLE {table} ALTER COLUMN phone DROP NOT NULL'
            )
        for column, typedef in PROFILE_COLUMNS:
            if column_exists(schema_editor, table, column):
                continue
            if vendor == 'sqlite' and column == 'profile_setup_completed':
                typedef = 'bool NOT NULL DEFAULT 0'
            cursor.execute(f'ALTER TABLE {table} ADD COLUMN {column} {typedef}')

        if vendor == 'postgresql' and column_exists(schema_editor, table, 'apple_sub'):
            cursor.execute(
                """
                SELECT 1 FROM pg_constraint
                WHERE conname = 'users_user_apple_sub_key'
                """
            )
            if not cursor.fetchone():
                cursor.execute(
                    f'ALTER TABLE {table} '
                    f'ADD CONSTRAINT users_user_apple_sub_key UNIQUE (apple_sub)'
                )

    otp_table = 'users_passwordresetotp'
    if not table_exists(schema_editor, otp_table):
        PasswordResetOTP = apps.get_model('users', 'PasswordResetOTP')
        schema_editor.create_model(PasswordResetOTP)


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0013_user_type_active_idx'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterField(
                    model_name='user',
                    name='country_code',
                    field=models.CharField(
                        blank=True,
                        help_text="ISO 3166-1 alpha-2 country code (e.g., 'US', 'GB', 'IN')",
                        max_length=3,
                        null=True,
                    ),
                ),
                migrations.AlterField(
                    model_name='user',
                    name='phone',
                    field=models.CharField(
                        blank=True,
                        help_text="International phone number (e.g., '+1234567890')",
                        max_length=20,
                        null=True,
                        validators=[
                            django.core.validators.RegexValidator(
                                message='Phone number must be in international format (e.g., +1234567890)',
                                regex='^(\\+[1-9]\\d{1,14})?$',
                            )
                        ],
                    ),
                ),
                migrations.AddField(
                    model_name='user',
                    name='preferred_currency',
                    field=models.CharField(
                        blank=True,
                        help_text='ISO 4217 currency code (e.g., USD, PKR)',
                        max_length=3,
                        null=True,
                    ),
                ),
                migrations.AddField(
                    model_name='user',
                    name='preferred_language',
                    field=models.CharField(
                        blank=True,
                        help_text='Preferred language code (e.g., en, ur)',
                        max_length=10,
                        null=True,
                    ),
                ),
                migrations.AddField(
                    model_name='user',
                    name='profile_type',
                    field=models.CharField(
                        blank=True,
                        choices=[('individual', 'Individual'), ('company', 'Company')],
                        help_text='Profile type: individual or company',
                        max_length=20,
                        null=True,
                    ),
                ),
                migrations.AddField(
                    model_name='user',
                    name='company_name',
                    field=models.CharField(blank=True, max_length=200, null=True),
                ),
                migrations.AddField(
                    model_name='user',
                    name='company_size',
                    field=models.CharField(blank=True, max_length=20, null=True),
                ),
                migrations.AddField(
                    model_name='user',
                    name='company_website',
                    field=models.CharField(blank=True, max_length=255, null=True),
                ),
                migrations.AddField(
                    model_name='user',
                    name='company_address',
                    field=models.TextField(blank=True, null=True),
                ),
                migrations.AddField(
                    model_name='user',
                    name='profile_setup_completed',
                    field=models.BooleanField(
                        default=False,
                        help_text='Whether the user has completed post-registration profile setup',
                    ),
                ),
                migrations.AddField(
                    model_name='user',
                    name='apple_sub',
                    field=models.CharField(
                        blank=True,
                        help_text='Apple Sign In subject identifier',
                        max_length=255,
                        null=True,
                        unique=True,
                    ),
                ),
                migrations.CreateModel(
                    name='PasswordResetOTP',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('email', models.EmailField(db_index=True, max_length=254)),
                        ('otp_hash', models.CharField(max_length=128)),
                        ('attempts', models.PositiveSmallIntegerField(default=0)),
                        ('created_at', models.DateTimeField(auto_now_add=True)),
                        ('is_used', models.BooleanField(default=False)),
                        ('reset_token', models.UUIDField(blank=True, null=True, unique=True)),
                        ('reset_token_created_at', models.DateTimeField(blank=True, null=True)),
                    ],
                    options={
                        'ordering': ['-created_at'],
                        'indexes': [
                            models.Index(fields=['email', 'is_used'], name='users_passw_email_4f8a1c_idx'),
                        ],
                    },
                ),
            ],
            database_operations=[
                migrations.RunPython(apply_profile_schema, noop_reverse),
            ],
        ),
    ]
