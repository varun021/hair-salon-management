from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.mail import send_mail
from django.utils import timezone
from datetime import date, timedelta, datetime
import uuid
from .forms import SignUpForm, ForgotPasswordForm, ResetPasswordForm, SignInForm, AppointmentForm, ChangePasswordForm, \
    ProfileUpdateForm, ServiceForm, PaymentForm, EmployeeCreationForm, UserEditForm, TimeSlotForm
from .models import User, Appointment, Service, LoyaltyPoint, Payment, AppointmentService, Notification, TimeSlot
from django.http import HttpResponseForbidden, JsonResponse
from django.template.loader import render_to_string
from .utils import create_notification
from django.db import models
from rest_framework import viewsets, permissions
from .serializers import AppointmentSerializer, ServiceSerializer
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from django.db.models.functions import TruncMonth
from django.db.models import Count, Sum


def is_employee(user):
    """Check if user is an employee"""
    return user.user_type == 'EMPLOYEE'


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
            appointment.client = request.user
            appointment.save()
            
            # Save the selected services
            services = form.cleaned_data['services']
            for service in services:
                AppointmentService.objects.create(
                    appointment=appointment,
                    service=service,
                    price=service.price,
                    quantity=1  # Default quantity
                )
            
            # Format time from time_slot for notification
            appointment_time = appointment.time_slot.start_time.strftime('%I:%M %p')
            
            create_notification(
                request.user,
                'APPOINTMENT',
                'Appointment Booked',
                f'Your appointment for {appointment.date} at {appointment_time} has been booked successfully.'
            )
            
            messages.success(request, "Your appointment has been booked successfully!")
            return redirect('client_dashboard')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = AppointmentForm()

    context = {
        "form": form,
        "services": Service.objects.filter(is_active=True)
    }
    return render(request, "appointments/book_appointment.html", context)

@login_required
def cancel_appointment(request, appointment_id):
    """Allows users to cancel their appointment"""
    # Get appointment based on user type
    if request.user.user_type == 'EMPLOYEE':
        appointment = get_object_or_404(Appointment, id=appointment_id)
    else:
        appointment = get_object_or_404(Appointment, id=appointment_id, client=request.user)

    # Only allow cancellation of pending or confirmed appointments
    if appointment.status in ["Pending", "Confirmed"]:
        appointment.status = "Cancelled"
        appointment.save()
        messages.success(request, "Appointment has been cancelled.")
    else:
        messages.error(request, "This appointment cannot be cancelled.")

    # Redirect based on user type
    if request.user.user_type == 'EMPLOYEE':
        return redirect('employee_dashboard')
    return redirect('client_dashboard')


@login_required
def reschedule_appointment(request, appointment_id):
    """Allows users to reschedule their appointment"""
    # Get appointment based on user type
    if request.user.user_type == 'EMPLOYEE':
        appointment = get_object_or_404(Appointment, id=appointment_id)
    else:
        appointment = get_object_or_404(Appointment, id=appointment_id, client=request.user)

    # Only allow rescheduling of pending or confirmed appointments
    if appointment.status not in ["Pending", "Confirmed"]:
        messages.error(request, "This appointment cannot be rescheduled.")
        return redirect('client_dashboard')

    if request.method == "POST":
        form = AppointmentForm(request.POST, instance=appointment)
        if form.is_valid():
            form.save()
            messages.success(request, "Appointment has been rescheduled.")
            if request.user.user_type == 'EMPLOYEE':
                return redirect('employee_dashboard')
            return redirect('client_dashboard')
    else:
        form = AppointmentForm(instance=appointment)

    return render(request, "appointments/reschedule_appointment.html", {
        "form": form, 
        "appointment": appointment
    })


@login_required
@user_passes_test(is_employee)
def complete_appointment(request, appointment_id):
    """Marks an appointment as completed (employee only)"""
    appointment = get_object_or_404(Appointment, id=appointment_id)

    if appointment.status == "Confirmed":
        appointment.status = "Completed"
        appointment.save()

        # Award loyalty points
        loyalty_points, created = LoyaltyPoint.objects.get_or_create(client=appointment.client)
        loyalty_points.points += 5
        loyalty_points.save()

        create_notification(
            appointment.client,
            'LOYALTY',
            'Points Earned',
            f'You earned 5 loyalty points for your completed appointment.'
        )

        messages.success(request, "Appointment marked as completed and loyalty points awarded!")
    else:
        messages.error(request, "Only confirmed appointments can be marked as completed.")

    return redirect('employee_dashboard')


def user_logout(request):
    """Logs out the user and redirects to landing page"""
    logout(request)
    messages.success(request, "Logged out successfully!")
    return redirect('landing_page')


@login_required
@user_passes_test(is_employee)
def employee_dashboard(request):
    # Get today's date
    today = timezone.now().date()
    
    # Get all appointments for today onwards
    appointments = Appointment.objects.filter(
        date__gte=today
    ).select_related(
        'client', 'time_slot'
    ).prefetch_related(
        'services'
    ).order_by('date', 'time_slot__start_time')

    # Get upcoming appointments (next 7 days)
    upcoming_appointments = appointments.filter(
        date__range=[today, today + timedelta(days=7)]
    )

    # Get pending appointments
    pending_appointments = appointments.filter(status='Pending')

    context = {
        'appointments': appointments,
        'upcoming_appointments': upcoming_appointments,
        'pending_appointments': pending_appointments,
        'today': today,
    }
    
    return render(request, 'dashboards/employee_dashboard.html', context)

@login_required
@user_passes_test(lambda u: u.user_type in ['ADMIN', 'EMPLOYEE'])
def add_service(request):
    """Add new service - accessible by both admin and employees"""
    if request.method == 'POST':
        form = ServiceForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Service added successfully!")
            return redirect('admin_dashboard' if request.user.user_type == 'ADMIN' else 'employee_dashboard')
    else:
        form = ServiceForm()
    
    return render(request, 'services/add_service.html', {'form': form})

@login_required
@user_passes_test(lambda u: u.user_type in ['ADMIN', 'EMPLOYEE'])
def edit_service(request, service_id):
    """Edit existing service - accessible by both admin and employees"""
    service = get_object_or_404(Service, id=service_id)
    
    if request.method == 'POST':
        form = ServiceForm(request.POST, request.FILES, instance=service)
        if form.is_valid():
            form.save()
            messages.success(request, "Service updated successfully!")
            return redirect('admin_dashboard' if request.user.user_type == 'ADMIN' else 'employee_dashboard')
    else:
        form = ServiceForm(instance=service)
    
    return render(request, 'services/edit_service.html', {'form': form, 'service': service})

@login_required
@user_passes_test(is_employee)
def delete_service(request, service_id):
    """Delete service"""
    service = get_object_or_404(Service, id=service_id)
    
    try:
        service.delete()
        messages.success(request, "Service deleted successfully!")
    except Exception as e:
        messages.error(request, "Cannot delete this service as it has associated appointments.")
    
    return redirect('employee_dashboard')

@login_required
@user_passes_test(is_employee)
def update_appointment_status(request, appointment_id, new_status):
    """Update appointment status (employee only)"""
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    # Define allowed status transitions
    allowed_transitions = {
        'Pending': ['Confirmed', 'Cancelled'],
        'Confirmed': ['Completed', 'Cancelled'],
        'Completed': [],  # No transitions allowed from completed
        'Cancelled': []   # No transitions allowed from cancelled
    }
    
    current_status = appointment.status
    if new_status in allowed_transitions.get(current_status, []):
        appointment.status = new_status
        appointment.save()
        
        # If completing appointment, award loyalty points
        if new_status == 'Completed':
            appointment.complete_appointment()
            
        messages.success(request, f"Appointment status updated to {new_status}")
    else:
        messages.error(request, f"Cannot change status from {current_status} to {new_status}")
    
    return redirect('employee_dashboard')

@login_required
def dashboard(request):
    """Route users to appropriate dashboard based on user type"""
    if request.user.user_type == 'ADMIN':
        return redirect('admin_dashboard')
    elif request.user.user_type == 'EMPLOYEE':
        return redirect('employee_dashboard')
    else:
        return redirect('client_dashboard')


@login_required
def client_dashboard(request):
    """Client Dashboard View"""
    user = request.user
    today = date.today()
    
    # Fetch notifications
    all_notifications = Notification.objects.filter(user=user).order_by('-created_at')
    unread_notifications = all_notifications.filter(is_read=False)
    notifications = all_notifications[:5]
    
    # Fetch upcoming appointments (pending and confirmed)
    upcoming_appointments = Appointment.objects.filter(
        client=user,
        date__gte=today,
        status__in=['Pending', 'Confirmed']
    ).select_related('time_slot').prefetch_related(
        'appointment_services__service'
    ).order_by('date', 'time_slot__start_time')
    
    # Fetch completed and past appointments
    past_appointments = Appointment.objects.filter(
        client=user
    ).filter(
        models.Q(status__in=['Completed', 'Paid']) |  # Completed or paid appointments
        models.Q(date__lt=today)  # Past appointments
    ).select_related(
        'time_slot'
    ).prefetch_related(
        'appointment_services__service',
        'payment'  # Include payment information
    ).order_by('-date', '-time_slot__start_time')
    
    # Get loyalty points
    loyalty_points, _ = LoyaltyPoint.objects.get_or_create(client=user)
    
    context = {
        'user': user,
        'notifications': notifications,
        'unread_notifications': unread_notifications,
        'upcoming_appointments': upcoming_appointments,
        'past_appointments': past_appointments,
        'loyalty_points': loyalty_points,
    }
    return render(request, 'dashboards/client_dashboard.html', context)


@login_required
def update_profile(request):
    """Update user profile"""
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            if request.user.user_type == 'ADMIN':
                return redirect('admin_dashboard')
            elif request.user.user_type == 'EMPLOYEE':
                return redirect('employee_dashboard')
        else:
                return redirect('client_dashboard')
    else:
        form = ProfileUpdateForm(instance=request.user)

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
            return redirect('profile')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ChangePasswordForm(request.user)

    return render(request, 'profile/change_password.html', {'form': form})

@login_required
@user_passes_test(is_employee)
def get_appointment_counts(request):
    """API endpoint for appointment counts"""
    appointments = Appointment.objects.filter(date__gte=timezone.now().date())
    counts = {
        'pending': appointments.filter(status='Pending').count(),
        'confirmed': appointments.filter(status='Confirmed').count(),
        'completed': appointments.filter(status='Completed').count(),
        'cancelled': appointments.filter(status='Cancelled').count(),
    }
    return JsonResponse(counts)

@login_required
def process_payment(request, appointment_id):
    appointment = get_object_or_404(
        Appointment.objects.prefetch_related('appointment_services__service'),
        id=appointment_id, 
        client=request.user
    )
    
    if appointment.status != 'Completed':
        messages.error(request, "Payment can only be processed for completed appointments.")
        return redirect('client_dashboard')
    
    # Check if payment already exists
    if hasattr(appointment, 'payment'):
        messages.error(request, "Payment has already been processed for this appointment.")
        return redirect('client_dashboard')
    
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            try:
                payment = form.save(commit=False)
                payment.appointment = appointment
                payment.amount = appointment.calculate_total()
                payment.tax = appointment.calculate_tax()
                payment.total_amount = appointment.calculate_grand_total()
                payment.status = 'PAID'  # Set as paid immediately for simulation
                payment.payment_date = timezone.now()
                payment.transaction_id = f"TXN-{timezone.now().strftime('%Y%m%d%H%M%S')}"
                payment.receipt_number = f"RCPT-{appointment.id}-{timezone.now().strftime('%Y%m%d%H%M%S')}"
                payment.save()
                
                # Update appointment status
                appointment.status = 'Paid'
                appointment.save()
                
                # Award loyalty points
                loyalty_points, created = LoyaltyPoint.objects.get_or_create(client=request.user)
                loyalty_points.points += 5  # Award 5 points for payment
                loyalty_points.save()
                
                # Send payment confirmation email
                try:
                    send_payment_confirmation(payment)
                except Exception as e:
                    # Log the error but don't stop the process
                    print(f"Failed to send email: {str(e)}")
                
                create_notification(
                    request.user,
                    'PAYMENT',
                    'Payment Successful',
                    f'Payment of ${payment.total_amount} for your appointment on {payment.appointment.date} has been processed.'
                )
                
                messages.success(request, "Payment processed successfully!")
                return redirect('payment_confirmation', payment_id=payment.id)
                
            except Exception as e:
                messages.error(request, f"Payment processing failed: {str(e)}")
                return redirect('process_payment', appointment_id=appointment_id)
    else:
        form = PaymentForm()
    
    context = {
        'appointment': appointment,
        'form': form,
        'total': appointment.calculate_total(),
        'tax': appointment.calculate_tax(),
        'grand_total': appointment.calculate_grand_total(),
    }
    return render(request, 'payments/process_payment.html', context)

@login_required
def payment_confirmation(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id, appointment__client=request.user)
    return render(request, 'payments/confirmation.html', {'payment': payment})

def send_payment_confirmation(payment):
    subject = 'Payment Confirmation'
    message = render_to_string('emails/payment_confirmation.html', {
        'payment': payment,
        'appointment': payment.appointment
    })
    send_mail(
        subject,
        message,
        'noreply@salon.com',
        [payment.appointment.client.email],
        html_message=message,
    )

@login_required
def mark_notification_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    return JsonResponse({'success': True})

@login_required
def mark_all_notifications_read(request):
    if request.method == 'POST':
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})

@login_required
@user_passes_test(lambda u: u.user_type == 'ADMIN')
def admin_dashboard(request):
    """Admin Dashboard View"""
    context = {
        'total_users': User.objects.count(),
        'employee_count': User.objects.filter(user_type='EMPLOYEE').count(),
        'client_count': User.objects.filter(user_type='CLIENT').count(),
        'total_appointments': Appointment.objects.count(),
        'today_appointments': Appointment.objects.filter(date=timezone.now().date()).count(),
        'monthly_revenue': Payment.objects.filter(
            payment_date__month=timezone.now().month
        ).aggregate(total=models.Sum('total_amount'))['total'] or 0,
        'active_services': Service.objects.filter(is_active=True).count(),
        'users': User.objects.all().order_by('-date_joined'),
    }
    return render(request, 'dashboards/admin_dashboard.html', context)

@login_required
@user_passes_test(lambda u: u.user_type == 'ADMIN')
def admin_add_employee(request):
    if request.method == 'POST':
        form = EmployeeCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.user_type = 'EMPLOYEE'
            user.save()
            messages.success(request, 'Employee added successfully!')
            return redirect('admin_dashboard')
    else:
        form = EmployeeCreationForm()
    return render(request, 'admin/add_employee.html', {'form': form})

@login_required
@user_passes_test(lambda u: u.user_type == 'ADMIN')
def admin_edit_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'User updated successfully!')
            return redirect('admin_dashboard')
    else:
        form = UserEditForm(instance=user)
    return render(request, 'admin/edit_user.html', {'form': form, 'user': user})

@login_required
@user_passes_test(lambda u: u.user_type == 'ADMIN')
def admin_service_management(request):
    services = Service.objects.all().order_by('-created_at')
    return render(request, 'admin/service_management.html', {'services': services})

@login_required
@user_passes_test(lambda u: u.user_type == 'ADMIN')
def admin_reports(request):
    return render(request, 'admin/reports.html')

@login_required
@user_passes_test(lambda u: u.user_type == 'ADMIN')
def admin_settings(request):
    return render(request, 'admin/settings.html')

@login_required
@user_passes_test(lambda u: u.user_type == 'ADMIN')
def activate_user(request, user_id):
    if request.method == 'POST':
        user = get_object_or_404(User, id=user_id)
        user.is_active = True
        user.save()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})

@login_required
@user_passes_test(lambda u: u.user_type == 'ADMIN')
def deactivate_user(request, user_id):
    if request.method == 'POST':
        user = get_object_or_404(User, id=user_id)
        user.is_active = False
        user.save()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})

class AppointmentViewSet(viewsets.ModelViewSet):
    """API endpoint for appointments"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AppointmentSerializer

    def get_queryset(self):
        if self.request.user.user_type == 'CLIENT':
            return Appointment.objects.filter(client=self.request.user)
        elif self.request.user.user_type in ['EMPLOYEE', 'ADMIN']:
            return Appointment.objects.all()
        return Appointment.objects.none()

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reschedule_appointment_api(request, appointment_id):
    """API endpoint for rescheduling appointments"""
    appointment = get_object_or_404(Appointment, id=appointment_id)
    if request.user != appointment.client and request.user.user_type not in ['EMPLOYEE', 'ADMIN']:
        return Response({'error': 'Not authorized'}, status=403)
    
    serializer = AppointmentRescheduleSerializer(data=request.data)
    if serializer.is_valid():
        appointment.date = serializer.validated_data['date']
        appointment.time = serializer.validated_data['time']
        appointment.save()
        return Response({'success': True})
    return Response(serializer.errors, status=400)

@login_required
def search_appointments(request):
    """Search appointments with filters"""
    query = request.GET.get('q', '')
    status = request.GET.get('status', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    appointments = Appointment.objects.all()

    if query:
        appointments = appointments.filter(
            Q(client__username__icontains=query) |
            Q(client__email__icontains=query) |
            Q(services__name__icontains=query)
        ).distinct()    
    if status:
        appointments = appointments.filter(status=status)
    else:
        appointments = appointments.all()

    if date_from:
        appointments = appointments.filter(date__gte=date_from)

    if date_to:
        appointments = appointments.filter(date__lte=date_to)

    return render(request, 'appointments/search_results.html', {
        'appointments': appointments,
        'query': query,
        'status': status,
        'date_from': date_from,
        'date_to': date_to
    })
@login_required
@user_passes_test(lambda u: u.user_type == 'ADMIN')
def analytics_dashboard(request):
    """Advanced analytics dashboard"""
    # Monthly revenue trend
    monthly_revenue = Payment.objects.annotate(
        month=TruncMonth('payment_date')
    ).values('month').annotate(
        total=Sum('total_amount')
    ).order_by('month')

    # Service popularity
    popular_services = AppointmentService.objects.values(
        'service__name'
    ).annotate(
        count=Count('id')
    ).order_by('-count')[:5]

    # Customer retention
    repeat_customers = User.objects.filter(
        user_type='CLIENT'
    ).annotate(
        appointment_count=Count('appointment')
    ).filter(appointment_count__gt=1).count()

    context = {
        'monthly_revenue': monthly_revenue,
        'popular_services': popular_services,
        'repeat_customers': repeat_customers,
        # Add more analytics data...
    }
    return render(request, 'admin/analytics.html', context)

@login_required
def notifications_list(request):
    """Display all notifications for the user"""
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    
    # Mark all as read when visiting the page
    unread_notifications = notifications.filter(is_read=False)
    unread_notifications.update(is_read=True)
    
    context = {
        'notifications': notifications,
        'unread_count': unread_notifications.count()
    }
    return render(request, 'notifications/notifications_list.html', context)

# Add these views

@login_required
@user_passes_test(is_employee)
def manage_time_slots(request):
    """View for managing time slots"""
    time_slots = TimeSlot.objects.all().order_by('start_time')
    form = TimeSlotForm()

    if request.method == 'POST':
        form = TimeSlotForm(request.POST)
        if form.is_valid():
            time_slot = form.save(commit=False)
            time_slot.created_by = request.user
            time_slot.save()
            messages.success(request, 'Time slot added successfully!')
            return redirect('manage_time_slots')

    context = {
        'time_slots': time_slots,
        'form': form
    }
    return render(request, 'time_slots/manage_time_slots.html', context)

@login_required
@user_passes_test(is_employee)
def edit_time_slot(request, slot_id):
    """Edit existing time slot"""
    time_slot = get_object_or_404(TimeSlot, id=slot_id)
    
    if request.method == 'POST':
        form = TimeSlotForm(request.POST, instance=time_slot)
        if form.is_valid():
            form.save()
            messages.success(request, 'Time slot updated successfully!')
            return redirect('manage_time_slots')
    else:
        form = TimeSlotForm(instance=time_slot)
    
    return render(request, 'time_slots/edit_time_slot.html', {'form': form})

@login_required
@user_passes_test(is_employee)
def delete_time_slot(request, slot_id):
    """Delete time slot"""
    time_slot = get_object_or_404(TimeSlot, id=slot_id)
    time_slot.delete()
    messages.success(request, 'Time slot deleted successfully!')
    return redirect('manage_time_slots')

@login_required
def get_available_slots(request):
    """AJAX endpoint to get available time slots for a date"""
    date_str = request.GET.get('date')
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
        # Get already booked slots for the date
        booked_slots = Appointment.objects.filter(
            date=date
        ).values_list('time_slot', flat=True)
        
        # Get available time slots
        available_slots = TimeSlot.objects.filter(
            is_active=True
        ).exclude(id__in=booked_slots)
        
        slots_data = [{
            'id': slot.id,
            'time': f"{slot.start_time.strftime('%I:%M %p')} - {slot.end_time.strftime('%I:%M %p')}"
        } for slot in available_slots]
        
        return JsonResponse({'slots': slots_data})
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid date'}, status=400)