# models.py
from django.utils import timezone
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from decimal import Decimal


class User(AbstractUser):
    USER_TYPES = (
        ('CLIENT', 'Client'),
        ('EMPLOYEE', 'Employee'),
        ('ADMIN', 'Admin'),
    )
    user_type = models.CharField(max_length=10, choices=USER_TYPES, default='CLIENT')  # Default to CLIENT
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    reset_password_token = models.CharField(max_length=100,null=True, blank=True)
    reset_password_expires = models.DateTimeField(null=True, blank=True)

    def get_user_type_display(self):
        """Return a display-friendly version of user type"""
        return self.user_type.capitalize()


class Service(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration = models.IntegerField(help_text="Duration in minutes", default=30)
    image = models.ImageField(upload_to='services/', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.name} - ${self.price}"

    class Meta:
        ordering = ['name']


class Payment(models.Model):
    PAYMENT_STATUS = (
        ('PENDING', 'Pending'),
        ('PAID', 'Paid'),
        ('FAILED', 'Failed'),
        ('REFUNDED', 'Refunded')
    )
    
    PAYMENT_METHOD = (
        ('CREDIT_CARD', 'Credit Card'),
        ('DEBIT_CARD', 'Debit Card'),
        ('PAYPAL', 'PayPal'),
        ('GOOGLE_PAY', 'Google Pay'),
        ('APPLE_PAY', 'Apple Pay')
    )
    
    appointment = models.OneToOneField('Appointment', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    tax = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='PENDING')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD)
    transaction_id = models.CharField(max_length=100, unique=True)
    payment_date = models.DateTimeField(default=timezone.now)
    receipt_number = models.CharField(max_length=50, unique=True)

    def generate_receipt_number(self):
        return f"RCPT-{self.appointment.id}-{timezone.now().strftime('%Y%m%d%H%M%S')}"

class AppointmentService(models.Model):
    appointment = models.ForeignKey('Appointment', on_delete=models.CASCADE, related_name='appointment_services')
    service = models.ForeignKey('Service', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Price at time of booking
    
    def save(self, *args, **kwargs):
        if not self.price:
            self.price = self.service.price
        super().save(*args, **kwargs)

    @property
    def total(self):
        return self.price * self.quantity

class Appointment(models.Model):
    client = models.ForeignKey(User, on_delete=models.CASCADE)
    services = models.ManyToManyField(Service, through=AppointmentService)
    date = models.DateField()
    time = models.TimeField()
    status = models.CharField(
        max_length=20,
        choices=[
            ("Pending", "Pending"),
            ("Confirmed", "Confirmed"),
            ("Completed", "Completed"),
            ("Paid", "Paid"),
            ("Cancelled", "Cancelled")
        ],
        default="Pending"
    )
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def calculate_total(self):
        """Calculate total before tax"""
        total = sum(
            appointment_service.service.price * appointment_service.quantity 
            for appointment_service in self.appointment_services.all()
        )
        return total

    def calculate_tax(self):
        """Calculate tax amount"""
        return self.calculate_total() * Decimal('0.13')  # 13% tax

    def calculate_grand_total(self):
        """Calculate total including tax"""
        return self.calculate_total() + self.calculate_tax()

    def __str__(self):
        return f"{self.client.username} - {self.date} at {self.time}"

    def complete_appointment(self):
        """Mark appointment as completed and award loyalty points"""
        if self.status != "Completed":
            self.status = "Completed"

            # Add loyalty points
            loyalty_points, created = LoyaltyPoint.objects.get_or_create(client=self.client)
            loyalty_points.points += 10  # Add 10 points for each completed appointment
            loyalty_points.save()

            self.save()


class LoyaltyPoint(models.Model):
    """Loyalty Points Model"""
    client = models.OneToOneField(User, on_delete=models.CASCADE)
    points = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.client.username} - {self.points} points"

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    loyalty_points = models.IntegerField(default=0)

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()

class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('APPOINTMENT', 'Appointment'),
        ('PAYMENT', 'Payment'),
        ('LOYALTY', 'Loyalty Points'),
        ('SYSTEM', 'System Message')
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=100)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.user.username}"