# Generated manually for bookings app (V1)

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('billboards', '0017_oohmediatypeattribute'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Booking',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_date', models.DateField(db_index=True)),
                ('end_date', models.DateField(db_index=True)),
                ('status', models.CharField(
                    choices=[
                        ('pending', 'Pending'),
                        ('accepted', 'Accepted'),
                        ('paid', 'Paid'),
                        ('confirmed', 'Confirmed'),
                        ('live', 'Live'),
                        ('completed', 'Completed'),
                        ('rejected', 'Rejected'),
                        ('cancelled', 'Cancelled'),
                    ],
                    db_index=True,
                    default='pending',
                    max_length=20,
                )),
                ('total_price', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ('currency', models.CharField(blank=True, default='', max_length=3)),
                ('advertiser_message', models.TextField(blank=True, default='')),
                ('rejection_reason', models.TextField(blank=True, default='')),
                ('owner_note', models.TextField(blank=True, default='')),
                ('expires_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('advertiser', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='advertiser_bookings',
                    to=settings.AUTH_USER_MODEL,
                )),
                ('billboard', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='bookings',
                    to='billboards.billboard',
                )),
                ('media_owner', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='owner_bookings',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='BookingContent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content_type', models.CharField(
                    choices=[('digital', 'Digital'), ('static', 'Static / physical')],
                    max_length=20,
                )),
                ('status', models.CharField(
                    choices=[
                        ('awaiting_input', 'Awaiting input'),
                        ('submitted', 'Submitted'),
                        ('owner_approved', 'Owner approved'),
                        ('owner_rejected', 'Owner rejected'),
                    ],
                    db_index=True,
                    default='awaiting_input',
                    max_length=20,
                )),
                ('video_url', models.URLField(blank=True, default='', max_length=500)),
                ('media_file', models.FileField(blank=True, null=True, upload_to='booking_content/%Y/%m/')),
                ('slot_daypart', models.CharField(blank=True, default='', max_length=100)),
                ('duration_seconds', models.PositiveIntegerField(blank=True, null=True)),
                ('digital_notes', models.TextField(blank=True, default='')),
                ('install_notes', models.TextField(blank=True, default='')),
                ('install_confirmed_by_owner', models.BooleanField(default=False)),
                ('external_link', models.URLField(blank=True, default='', max_length=500)),
                ('owner_feedback', models.TextField(blank=True, default='')),
                ('submitted_at', models.DateTimeField(blank=True, null=True)),
                ('reviewed_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('booking', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='content',
                    to='bookings.booking',
                )),
            ],
            options={
                'verbose_name': 'Booking content',
                'verbose_name_plural': 'Booking contents',
            },
        ),
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ('currency', models.CharField(blank=True, default='', max_length=3)),
                ('status', models.CharField(
                    choices=[
                        ('skipped', 'Skipped (V1)'),
                        ('held', 'Held'),
                        ('captured', 'Captured'),
                        ('released', 'Released to owner'),
                        ('refunded', 'Refunded'),
                        ('failed', 'Failed'),
                    ],
                    db_index=True,
                    default='skipped',
                    max_length=20,
                )),
                ('gateway_ref', models.CharField(blank=True, default='', max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('booking', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='payment',
                    to='bookings.booking',
                )),
            ],
        ),
        migrations.AddIndex(
            model_name='booking',
            index=models.Index(fields=['billboard', 'status', 'start_date', 'end_date'], name='bookings_bo_billboa_7f0a1c_idx'),
        ),
        migrations.AddIndex(
            model_name='booking',
            index=models.Index(fields=['advertiser', 'status'], name='bookings_bo_adverti_1a2b3c_idx'),
        ),
        migrations.AddIndex(
            model_name='booking',
            index=models.Index(fields=['media_owner', 'status'], name='bookings_bo_media_o_4d5e6f_idx'),
        ),
    ]
