from django.core.management.base import BaseCommand
from accounts.models import Service

class Command(BaseCommand):
    help = 'Creates dummy services for testing'

    def handle(self, *args, **kwargs):
        # Create main services
        main_services = [
            {
                'name': 'Haircut',
                'description': 'Professional haircut services',
                'price': 30.00,
                'duration': 30,
            },
            {
                'name': 'Hair Coloring',
                'description': 'Professional hair coloring services',
                'price': 80.00,
                'duration': 120,
            },
            {
                'name': 'Hair Styling',
                'description': 'Professional hair styling services',
                'price': 50.00,
                'duration': 60,
            },
            {
                'name': 'Hair Treatment',
                'description': 'Professional hair treatment services',
                'price': 70.00,
                'duration': 90,
            }
        ]

        # Create sub-services
        sub_services = {
            'Haircut': [
                {'name': 'Basic Trim', 'price': 25.00, 'duration': 30},
                {'name': 'Layered Cut', 'price': 35.00, 'duration': 45},
                {'name': 'Bangs Trim', 'price': 15.00, 'duration': 15},
                {'name': 'Kids Haircut', 'price': 20.00, 'duration': 30},
            ],
            'Hair Coloring': [
                {'name': 'Root Touch-up', 'price': 60.00, 'duration': 90},
                {'name': 'Full Color', 'price': 100.00, 'duration': 120},
                {'name': 'Highlights', 'price': 120.00, 'duration': 150},
                {'name': 'Balayage', 'price': 150.00, 'duration': 180},
            ],
            'Hair Styling': [
                {'name': 'Blowout', 'price': 40.00, 'duration': 45},
                {'name': 'Updo', 'price': 65.00, 'duration': 60},
                {'name': 'Curling', 'price': 45.00, 'duration': 45},
                {'name': 'Straightening', 'price': 45.00, 'duration': 45},
            ],
            'Hair Treatment': [
                {'name': 'Deep Conditioning', 'price': 50.00, 'duration': 60},
                {'name': 'Keratin Treatment', 'price': 200.00, 'duration': 180},
                {'name': 'Scalp Treatment', 'price': 60.00, 'duration': 60},
                {'name': 'Hair Mask', 'price': 45.00, 'duration': 45},
            ]
        }

        # Create main services
        for service_data in main_services:
            main_service, created = Service.objects.get_or_create(
                name=service_data['name'],
                defaults={
                    'description': service_data['description'],
                    'price': service_data['price'],
                    'duration': service_data['duration'],
                    'service_type': 'MAIN'
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created main service: {main_service.name}'))

            # Create sub-services for this main service
            for sub_service_data in sub_services[service_data['name']]:
                sub_service, created = Service.objects.get_or_create(
                    name=sub_service_data['name'],
                    parent_service=main_service,
                    defaults={
                        'description': f'Sub-service of {main_service.name}',
                        'price': sub_service_data['price'],
                        'duration': sub_service_data['duration'],
                        'service_type': 'SUB'
                    }
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f'Created sub-service: {sub_service.name}'))

        self.stdout.write(self.style.SUCCESS('Successfully created all dummy services')) 