from django.core.management.base import BaseCommand
from django.utils import timezone
from accounts.models import TimeSlot
from datetime import time, timedelta, datetime

class Command(BaseCommand):
    help = 'Creates default time slots for salon appointments'

    def handle(self, *args, **kwargs):
        # Define the working hours
        start_hour = 9  # 9 AM
        end_hour = 18   # 6 PM
        slot_duration = 30  # 30 minutes per slot
        
        # Delete existing time slots if needed
        if TimeSlot.objects.exists():
            self.stdout.write(self.style.WARNING('Deleting existing time slots...'))
            TimeSlot.objects.all().delete()
        
        # Create time slots from start_hour to end_hour with slot_duration minute intervals
        slots_created = 0
        current_time = time(start_hour, 0)  # Start at 9:00 AM
        end_time = time(end_hour, 0)  # End at 6:00 PM
        
        while current_time < end_time:
            # Calculate the end time for this slot
            current_datetime = datetime.combine(timezone.now().date(), current_time)
            slot_end_datetime = current_datetime + timedelta(minutes=slot_duration)
            slot_end_time = slot_end_datetime.time()
            
            # Create the time slot
            TimeSlot.objects.create(
                start_time=current_time,
                end_time=slot_end_time,
                is_active=True
            )
            slots_created += 1
            
            # Move to the next slot
            current_time = slot_end_time
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {slots_created} time slots')
        ) 