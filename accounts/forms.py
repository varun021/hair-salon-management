# forms.py
from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm, PasswordChangeForm
from .models import User, Appointment


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


class AppointmentForm(forms.ModelForm):
    date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    time = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time'}))

    class Meta:
        model = Appointment
        fields = ['service', 'date', 'time']

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