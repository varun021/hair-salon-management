from django.core.management.base import BaseCommand
from django.utils import timezone
from accounts.models import User, Service, Appointment, Payment, AppointmentService, TimeSlot
from datetime import timedelta
from decimal import Decimal
import random

class Command(BaseCommand):
    help = 'Creates dummy data for testing reports'

    def handle(self, *args, **kwargs):
        # Ensure we have at least one client and one service
        try:
            client = User.objects.filter(user_type='CLIENT').first()
            if not client:
                client = User.objects.create_user(
                    username='testclient',
                    email='testclient@example.com',
                    password='testpass123',
                    user_type='CLIENT'
                )
                self.stdout.write(self.style.SUCCESS('Created test client'))

            # Get all main services
            main_services = Service.objects.filter(service_type='MAIN')
            if not main_services.exists():
                self.stdout.write(self.style.ERROR('No main services found. Please run create_dummy_services first.'))
                return

            # Create time slots if they don't exist
            if not TimeSlot.objects.exists():
                for hour in range(9, 18):  # 9 AM to 5 PM
                    TimeSlot.objects.get_or_create(
                        hour=hour,
                        minute=0
                    )
                    TimeSlot.objects.get_or_create(
                        hour=hour,
                        minute=30
                    )

            # Generate appointments and payments for the last 30 days
            today = timezone.now().date()
            statuses = ['Pending', 'Confirmed', 'Completed', 'Cancelled']
            status_weights = [0.2, 0.3, 0.4, 0.1]  # Weights for random selection

            for days_ago in range(30):
                date = today - timedelta(days=days_ago)
                
                # Create 2-5 appointments per day
                for _ in range(random.randint(2, 5)):
                    # Get a random time slot
                    time_slot = random.choice(TimeSlot.objects.all())
                    
                    # Get a random main service
                    main_service = random.choice(main_services)
                    
                    # Create appointment
                    appointment = Appointment.objects.create(
                        client=client,
                        date=date,
                        time_slot=time_slot,
                        status=random.choices(statuses, weights=status_weights)[0]
                    )

                    # Add main service to appointment
                    AppointmentService.objects.create(
                        appointment=appointment,
                        service=main_service,
                        price=main_service.price
                    )

                    # Add 1-3 sub-services
                    sub_services = main_service.sub_services.all()
                    if sub_services.exists():
                        for sub_service in random.sample(list(sub_services), min(random.randint(1, 3), sub_services.count())):
                            AppointmentService.objects.create(
                                appointment=appointment,
                                service=sub_service,
                                price=sub_service.price
                            )

                    # Create payment for completed appointments
                    if appointment.status == 'Completed':
                        total = sum(app_service.price for app_service in appointment.appointment_services.all())
                        tax = total * Decimal('0.1')  # 10% tax
                        Payment.objects.create(
                            appointment=appointment,
                            amount=total,
                            tax=tax,
                            total_amount=total + tax,
                            payment_method=random.choice(['CASH', 'CARD']),
                            status='PAID',
                            payment_date=timezone.now() - timedelta(days=days_ago),
                            transaction_id=f'TXN-{appointment.id}',
                            receipt_number=f'RCPT-{appointment.id}'
                        )

            self.stdout.write(self.style.SUCCESS(f'Successfully created dummy data'))
            self.stdout.write(f'Total Appointments: {Appointment.objects.count()}')
            self.stdout.write(f'Total Payments: {Payment.objects.count()}')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating dummy data: {str(e)}')) 