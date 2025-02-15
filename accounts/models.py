# models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


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


class Service(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name


class Appointment(models.Model):
    client = models.ForeignKey(User, on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    date = models.DateField()
    time = models.TimeField()
    status = models.CharField(
        max_length=20,
        choices=[
            ("Pending", "Pending"),
            ("Confirmed", "Confirmed"),
            ("Cancelled", "Cancelled"),
            ("Completed", "Completed")
        ],
        default="Pending"
    )

    def __str__(self):
        return f"{self.client.username} - {self.service.name} on {self.date} at {self.time}"

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