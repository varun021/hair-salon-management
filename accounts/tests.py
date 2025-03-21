from django.test import TestCase, Client
from django.urls import reverse
from .models import User, Appointment, Service

# Create your tests here.

class AppointmentTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            user_type='CLIENT'
        )
        self.service = Service.objects.create(
            name='Test Service',
            price=100,
            duration=60
        )

    def test_book_appointment(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(reverse('book_appointment'), {
            'service': self.service.id,
            'date': '2024-03-01',
            'time': '14:00'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Appointment.objects.filter(client=self.user).exists())
