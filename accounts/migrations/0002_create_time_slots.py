from django.db import migrations
from datetime import time, timedelta, datetime

def create_initial_time_slots(apps, schema_editor):
    TimeSlot = apps.get_model('accounts', 'TimeSlot')
    
    # Define the working hours
    start_hour = 9  # 9 AM
    end_hour = 18   # 6 PM
    slot_duration = 30  # 30 minutes per slot
    
    # Create time slots from start_hour to end_hour with slot_duration minute intervals
    current_time = time(start_hour, 0)  # Start at 9:00 AM
    end_time = time(end_hour, 0)  # End at 6:00 PM
    
    while current_time < end_time:
        # Calculate the end time for this slot
        current_datetime = datetime.combine(datetime.now().date(), current_time)
        slot_end_datetime = current_datetime + timedelta(minutes=slot_duration)
        slot_end_time = slot_end_datetime.time()
        
        # Check if time slot already exists to avoid unique constraint violations
        if not TimeSlot.objects.filter(start_time=current_time, end_time=slot_end_time).exists():
            # Create the time slot
            TimeSlot.objects.create(
                start_time=current_time,
                end_time=slot_end_time,
                is_active=True
            )
        
        # Move to the next slot
        current_time = slot_end_time

def remove_time_slots(apps, schema_editor):
    TimeSlot = apps.get_model('accounts', 'TimeSlot')
    TimeSlot.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_initial_time_slots, remove_time_slots),
    ] 