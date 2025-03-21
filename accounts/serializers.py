from rest_framework import serializers
from .models import Appointment, Service, User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ['id', 'name', 'description', 'price', 'duration', 'is_active']

class AppointmentSerializer(serializers.ModelSerializer):
    client = UserSerializer(read_only=True)
    services = ServiceSerializer(many=True, read_only=True)

    class Meta:
        model = Appointment
        fields = [
            'id', 
            'client', 
            'services', 
            'date', 
            'time', 
            'status', 
            'notes',
            'created_at'
        ] 