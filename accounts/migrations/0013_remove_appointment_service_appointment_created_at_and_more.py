# Generated by Django 5.1.6 on 2025-02-15 15:22

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0012_service_duration_service_image_service_is_active'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='appointment',
            name='service',
        ),
        migrations.AddField(
            model_name='appointment',
            name='created_at',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name='appointment',
            name='notes',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='appointment',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='appointment',
            name='status',
            field=models.CharField(choices=[('Pending', 'Pending'), ('Confirmed', 'Confirmed'), ('Completed', 'Completed'), ('Paid', 'Paid'), ('Cancelled', 'Cancelled')], default='Pending', max_length=20),
        ),
        migrations.CreateModel(
            name='AppointmentService',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.PositiveIntegerField(default=1)),
                ('price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('appointment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='appointment_services', to='accounts.appointment')),
                ('service', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='accounts.service')),
            ],
        ),
        migrations.AddField(
            model_name='appointment',
            name='services',
            field=models.ManyToManyField(through='accounts.AppointmentService', to='accounts.service'),
        ),
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('tax', models.DecimalField(decimal_places=2, max_digits=10)),
                ('total_amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('status', models.CharField(choices=[('PENDING', 'Pending'), ('PAID', 'Paid'), ('FAILED', 'Failed'), ('REFUNDED', 'Refunded')], default='PENDING', max_length=20)),
                ('payment_method', models.CharField(blank=True, choices=[('CREDIT_CARD', 'Credit Card'), ('DEBIT_CARD', 'Debit Card'), ('PAYPAL', 'PayPal'), ('GOOGLE_PAY', 'Google Pay'), ('APPLE_PAY', 'Apple Pay')], max_length=20, null=True)),
                ('transaction_id', models.CharField(blank=True, max_length=100, null=True)),
                ('payment_date', models.DateTimeField(blank=True, null=True)),
                ('receipt_number', models.CharField(max_length=50, null=True, unique=True)),
                ('appointment', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='accounts.appointment')),
            ],
        ),
    ]
