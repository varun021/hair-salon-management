from .models import Notification
from weasyprint import HTML
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.utils.html import strip_tags

def create_notification(user, type, title, message):
    return Notification.objects.create(
        user=user,
        type=type,
        title=title,
        message=message
    )

def generate_appointment_pdf(appointment):
    """Generate PDF for appointment details"""
    html_string = render_to_string('pdf/appointment_details.html', {
        'appointment': appointment
    })
    html = HTML(string=html_string)
    return html.write_pdf()

def send_appointment_confirmation(appointment):
    """Send appointment confirmation email with PDF attachment"""
    subject = 'Appointment Confirmation'
    from_email = 'noreply@salon.com'
    to = [appointment.client.email]

    html_content = render_to_string('emails/appointment_confirmation.html', {
        'appointment': appointment
    })
    text_content = strip_tags(html_content)

    msg = EmailMultiAlternatives(subject, text_content, from_email, to)
    msg.attach_alternative(html_content, "text/html")

    # Attach PDF
    pdf = generate_appointment_pdf(appointment)
    msg.attach('appointment_details.pdf', pdf, 'application/pdf')
    msg.send() 