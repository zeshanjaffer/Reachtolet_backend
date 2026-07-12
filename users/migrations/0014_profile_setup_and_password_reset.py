# Generated manually for Phase 2 profile setup + Phase 6 password reset / Apple login

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0013_user_type_active_idx'),
    ]

    operations = [
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
    ]
