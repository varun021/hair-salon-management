from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
    ('accounts', '0008_add_stylist_and_services'),
]

    operations = [
        migrations.AlterField(
            model_name='appointment',
            name='stylist',
            field=models.ForeignKey(
                to='accounts.user',
                on_delete=django.db.models.deletion.CASCADE,
                related_name='stylist_appointments',
            ),
        ),
    ] 