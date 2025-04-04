# forms.py
from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm, PasswordChangeForm
from .models import User, Appointment, Service, AppointmentService, Payment, TimeSlot
from django.utils import timezone
from datetime import date


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
    main_service = forms.ModelChoiceField(
        queryset=Service.objects.filter(service_type='MAIN', is_active=True),
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'main-service'}),
        required=True,
        label="Select Main Service"
    )
    
    sub_services = forms.ModelMultipleChoiceField(
        queryset=Service.objects.filter(service_type='SUB', is_active=True),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'sub-service-checkbox'}),
        required=True,
        label="Select Sub-Services"
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
        fields = ['main_service', 'sub_services', 'date', 'time_slot', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'id': 'appointment-date',
                'min': date.today().isoformat()  # Set minimum date to today
            }),
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
        
        # If we have POST data with a main_service, update sub_services queryset
        if self.data.get('main_service'):
            try:
                main_service_id = int(self.data.get('main_service'))
                self.fields['sub_services'].queryset = Service.objects.filter(
                    parent_service_id=main_service_id,
                    service_type='SUB',
                    is_active=True
                )
            except (ValueError, TypeError):
                self.fields['sub_services'].queryset = Service.objects.none()
        # If we're editing an existing appointment, populate the sub_services
        elif self.instance and self.instance.pk:
            main_services = self.instance.services.filter(service_type='MAIN')
            if main_services.exists():
                main_service = main_services.first()
                self.fields['main_service'].initial = main_service
                self.fields['sub_services'].queryset = Service.objects.filter(
                    parent_service=main_service,
                    service_type='SUB',
                    is_active=True
                )
                self.fields['sub_services'].initial = self.instance.services.filter(service_type='SUB')
        else:
            self.fields['sub_services'].queryset = Service.objects.none()

    def clean(self):
        cleaned_data = super().clean()
        main_service = cleaned_data.get('main_service')
        sub_services = cleaned_data.get('sub_services', [])

        if main_service and not sub_services:
            raise forms.ValidationError("Please select at least one sub-service.")

        # Validate that selected sub-services belong to the main service
        if main_service and sub_services:
            valid_sub_services = Service.objects.filter(
                parent_service=main_service,
                service_type='SUB',
                is_active=True
            )
            invalid_services = [s for s in sub_services if s not in valid_sub_services]
            if invalid_services:
                raise forms.ValidationError("Some selected sub-services are not valid for this main service.")

        return cleaned_data

    def clean_date(self):
        selected_date = self.cleaned_data.get('date')
        today = date.today()
        
        if selected_date and selected_date < today:
            raise forms.ValidationError("You cannot book appointments in the past.")
        
        return selected_date

    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.save()
            # Clear existing services
            instance.services.clear()
            # Add main service
            main_service = self.cleaned_data['main_service']
            instance.services.add(main_service)
            # Add sub services
            for sub_service in self.cleaned_data['sub_services']:
                instance.services.add(sub_service)
        return instance

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
        fields = ['name', 'description', 'price', 'duration', 'image', 'is_active', 'service_type', 'parent_service']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'duration': forms.NumberInput(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'service_type': forms.Select(attrs={'class': 'form-control', 'id': 'service-type'}),
            'parent_service': forms.Select(attrs={'class': 'form-control', 'id': 'parent-service'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show main services in parent_service dropdown
        self.fields['parent_service'].queryset = Service.objects.filter(service_type='MAIN', is_active=True)
        # Hide parent_service field initially (will be shown via JavaScript when SUB is selected)
        self.fields['parent_service'].required = False

    def clean(self):
        cleaned_data = super().clean()
        service_type = cleaned_data.get('service_type')
        parent_service = cleaned_data.get('parent_service')

        if service_type == 'SUB' and not parent_service:
            raise forms.ValidationError("Sub-services must have a parent service selected.")
        elif service_type == 'MAIN' and parent_service:
            cleaned_data['parent_service'] = None

        return cleaned_data

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