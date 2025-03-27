# forms.py
from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm, PasswordChangeForm
from .models import User, Appointment, Service, AppointmentService, Payment, TimeSlot


class SignInForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))


class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)
    phone_number = forms.CharField(required=False)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'phone_number')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = 'CLIENT'  # Ensure new users are CLIENT by default
        if commit:
            user.save()
        return user

class ForgotPasswordForm(forms.Form):
    email = forms.EmailField(required=True)

class ResetPasswordForm(forms.Form):
    password1 = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput)


class AppointmentServiceForm(forms.ModelForm):
    class Meta:
        model = AppointmentService
        fields = ['service', 'quantity']
        widgets = {
            'quantity': forms.NumberInput(attrs={'min': 1, 'class': 'form-control'})
        }

class AppointmentForm(forms.ModelForm):
    services = forms.ModelMultipleChoiceField(
        queryset=Service.objects.filter(is_active=True),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'service-checkbox'}),
        required=True,
        label="Select Services"
    )
    
    time_slot = forms.ModelChoiceField(
        queryset=TimeSlot.objects.none(),
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Select Time Slot",
        empty_label="Select a date first"
    )
    
    class Meta:
        model = Appointment
        fields = ['services', 'date', 'time_slot', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control', 'id': 'appointment-date'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Any special requests?'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # If we have an instance and it has a date, load the available time slots
        if self.instance and self.instance.pk and self.instance.date:
            self.fields['time_slot'].queryset = TimeSlot.get_available_slots(self.instance.date)
            
            # If the instance already has a time_slot, include it in the queryset
            if self.instance.time_slot:
                current_slot = TimeSlot.objects.filter(pk=self.instance.time_slot.pk)
                self.fields['time_slot'].queryset = self.fields['time_slot'].queryset | current_slot

class ProfileUpdateForm(forms.ModelForm):
    """Form for users to update their profile information."""
    class Meta:
        model = User
        fields = ['username', 'email', 'phone_number']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
        }


class ChangePasswordForm(PasswordChangeForm):
    """Form for users to change their password."""
    old_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Old Password'}),
        label="Old Password"
    )
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'New Password'}),
        label="New Password"
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm New Password'}),
        label="Confirm New Password"
    )

class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ['name', 'description', 'price', 'duration', 'image', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'duration': forms.NumberInput(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['payment_method']
        widgets = {
            'payment_method': forms.Select(attrs={'class': 'form-control'})
        }

class EmployeeCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'phone_number', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
        }

class UserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'phone_number', 'user_type', 'is_active']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'user_type': forms.Select(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }