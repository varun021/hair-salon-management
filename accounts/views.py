from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.utils import timezone
from datetime import date, timedelta
import uuid
from .forms import SignUpForm, ForgotPasswordForm, ResetPasswordForm, SignInForm, AppointmentForm, ChangePasswordForm, \
    ProfileUpdateForm
from .models import User, Appointment, Service, LoyaltyPoint


def signin(request):
    """Handles user login"""
    if request.method == 'POST':
        form = SignInForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, "Login successful!")
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = SignInForm()
    return render(request, 'registration/signin.html', {'form': form})


def landing_page(request):
    """Displays the landing page"""
    return render(request, 'landing_page.html', {'range_six': range(6)})


def signup(request):
    """Handles user registration"""
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Account created successfully!")
            return redirect('dashboard')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = SignUpForm()
    return render(request, 'registration/signup.html', {'form': form})


def forgot_password(request):
    """Handles password reset request"""
    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            user = User.objects.filter(email=email).first()

            if user:
                token = str(uuid.uuid4())
                user.reset_password_token = token
                user.reset_password_expires = timezone.now() + timedelta(hours=24)
                user.save()

                reset_link = f"{request.scheme}://{request.get_host()}/reset-password/{token}"
                send_mail(
                    'Password Reset Request',
                    f'Click the following link to reset your password: {reset_link}',
                    'no-reply@hairsalon.com',
                    [email],
                    fail_silently=False,
                )

                messages.success(request, "Password reset link sent! Check your email.")
                return redirect('signin')
            else:
                messages.error(request, "No user found with this email address.")
    else:
        form = ForgotPasswordForm()
    return render(request, 'registration/forgot_password.html', {'form': form})


def reset_password(request, token):
    """Handles password reset via token"""
    user = get_object_or_404(User, reset_password_token=token, reset_password_expires__gt=timezone.now())

    if request.method == 'POST':
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            password1 = form.cleaned_data['password1']
            password2 = form.cleaned_data['password2']

            if password1 == password2:
                user.set_password(password1)
                user.reset_password_token = ''
                user.reset_password_expires = None
                user.save()
                messages.success(request, "Password reset successfully! You can now log in.")
                return redirect('signin')
            else:
                messages.error(request, "Passwords do not match.")
    else:
        form = ResetPasswordForm()
    return render(request, 'registration/reset_password.html', {'form': form})


@login_required
def book_appointment(request):
    """Allows users to book an appointment"""
    if request.method == "POST":
        form = AppointmentForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.client = request.user  # Assign logged-in user
            appointment.save()
            messages.success(request, "Your appointment has been booked successfully!")
            return redirect('client_dashboard')  # Redirect to the client dashboard
    else:
        form = AppointmentForm()

    services = Service.objects.all()  # Fetch available services
    return render(request, "appointments/book_appointment.html", {"form": form, "services": services})


@login_required
def cancel_appointment(request, appointment_id):
    """Allows users to cancel their appointment"""
    appointment = get_object_or_404(Appointment, id=appointment_id, client=request.user)

    if appointment.status != "Cancelled":
        appointment.status = "Cancelled"
        appointment.save()
        messages.success(request, "Your appointment has been cancelled.")

    return redirect("client_dashboard")


@login_required
def reschedule_appointment(request, appointment_id):
    """Allows users to reschedule their appointment"""
    appointment = get_object_or_404(Appointment, id=appointment_id, client=request.user)

    if request.method == "POST":
        form = AppointmentForm(request.POST, instance=appointment)
        if form.is_valid():
            form.save()
            messages.success(request, "Your appointment has been rescheduled.")
            return redirect("client_dashboard")
    else:
        form = AppointmentForm(instance=appointment)

    return render(request, "appointments/reschedule_appointment.html", {"form": form, "appointment": appointment})


@login_required
def complete_appointment(request, appointment_id):
    """Marks an appointment as completed and awards loyalty points"""
    appointment = get_object_or_404(Appointment, id=appointment_id, client=request.user)

    if appointment.status == "Confirmed":
        appointment.status = "Completed"
        appointment.save()

        # Award loyalty points (5 points per completed appointment)
        loyalty_points, created = LoyaltyPoint.objects.get_or_create(client=request.user)
        loyalty_points.points += 5
        loyalty_points.save()

        messages.success(request, "Your appointment has been marked as completed! You earned 5 loyalty points.")

    return redirect("client_dashboard")


def user_logout(request):
    """Logs out the user and redirects to landing page"""
    logout(request)
    messages.success(request, "Logged out successfully!")
    return redirect('landing_page')


@login_required
def dashboard(request):
    """Redirects users to their respective dashboards based on role"""
    user_type_redirects = {
        'CLIENT': 'client_dashboard',
        'EMPLOYEE': 'dashboards/employee_dashboard.html',
        'ADMIN': 'dashboards/admin_dashboard.html',
    }

    template = user_type_redirects.get(request.user.user_type, 'landing_page')

    if template == 'client_dashboard':
        return redirect('client_dashboard')

    return render(request, template)


@login_required
def client_dashboard(request):
    """Client Dashboard View"""

    # Get the logged-in user
    user = request.user

    # Fetch upcoming appointments (appointments in the future)
    upcoming_appointments = Appointment.objects.filter(client=user, date__gte=date.today()).order_by('date')

    # Fetch past appointments (appointments in the past)
    past_appointments = Appointment.objects.filter(client=user, date__lt=date.today()).order_by('-date')

    # Get all available salon services
    services = Service.objects.all()

    # Get user loyalty points (if applicable)
    loyalty_points, created = LoyaltyPoint.objects.get_or_create(client=user)

    # Pass data to the template
    context = {
        'user': user,
        'upcoming_appointments': upcoming_appointments,
        'past_appointments': past_appointments,
        'services': services,
        'loyalty_points': loyalty_points,
    }
    return render(request, 'dashboards/client_dashboard.html', context)



@login_required
def update_profile(request):
    """Allows users to update their profile details"""
    user = request.user

    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated successfully!")
            return redirect('update_profile')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ProfileUpdateForm(instance=user)

    return render(request, 'profile/update_profile.html', {'form': form})


@login_required
def change_password(request):
    """Allows users to change their password"""
    if request.method == 'POST':
        form = ChangePasswordForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Prevents logout after password change
            messages.success(request, "Your password has been changed successfully!")
            return redirect('update_profile')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ChangePasswordForm(request.user)

    return render(request, 'profile/change_password.html', {'form': form})