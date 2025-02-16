from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
    ('accounts', '0007_remove_profile_address_and_more'),
]

    operations = [
        # First add the ManyToMany field to Service
        migrations.AddField(
            model_name='service',
            name='stylists',
            field=models.ManyToManyField(
                to='accounts.user',
                limit_choices_to={'user_type': 'EMPLOYEE'},
                related_name='services',
            ),
        ),
        # Then add the nullable stylist field to Appointment
        migrations.AddField(
            model_name='appointment',
            name='stylist',
            field=models.ForeignKey(
                to='accounts.user',
                on_delete=django.db.models.deletion.CASCADE,
                related_name='stylist_appointments',
                null=True,
                blank=True,
            ),
        ),
    ] 