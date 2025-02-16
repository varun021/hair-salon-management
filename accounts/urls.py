from django.contrib.auth.views import LogoutView
from django.urls import path
from . import views
from .views import user_logout, client_dashboard, book_appointment, cancel_appointment, reschedule_appointment, \
    update_profile, change_password, complete_appointment

urlpatterns = [
    path('', views.landing_page, name='landing_page'),
    path('signin/', views.signin, name='signin'),
    path('signup/', views.signup, name='signup'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/<str:token>/', views.reset_password, name='reset_password'),
    path('profile/', views.update_profile, name='profile'),
    path('profile/change-password/', views.change_password, name='change_password'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('client-dashboard/', client_dashboard, name='client_dashboard'),
    path('book-appointment/', book_appointment, name='book_appointment'),
    path('complete-appointment/<int:appointment_id>/', complete_appointment, name='complete_appointment'),
    path('cancel-appointment/<int:appointment_id>/', cancel_appointment, name='cancel_appointment'),
    path('reschedule-appointment/<int:appointment_id>/', reschedule_appointment, name='reschedule_appointment'),
    path('logout/', views.user_logout, name='logout'),
    path('employee-dashboard/', views.employee_dashboard, name='employee_dashboard'),
    path('services/add/', views.add_service, name='add_service'),
    path('services/edit/<int:service_id>/', views.edit_service, name='edit_service'),
    path('services/delete/<int:service_id>/', views.delete_service, name='delete_service'),
    path('appointments/update-status/<int:appointment_id>/<str:new_status>/', 
         views.update_appointment_status, name='update_appointment_status'),
    path('payment/<int:appointment_id>/', views.process_payment, name='process_payment'),
    path('payment/confirmation/<int:payment_id>/', views.payment_confirmation, name='payment_confirmation'),
    path('notifications/<int:notification_id>/mark-read/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    path('dashboard/admin/', views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/admin/add-employee/', views.admin_add_employee, name='admin_add_employee'),
    path('dashboard/admin/edit-user/<int:user_id>/', views.admin_edit_user, name='admin_edit_user'),
    path('dashboard/admin/services/', views.admin_service_management, name='admin_service_management'),
    path('dashboard/admin/reports/', views.admin_reports, name='admin_reports'),
    path('dashboard/admin/settings/', views.admin_settings, name='admin_settings'),
    path('dashboard/admin/user/<int:user_id>/activate/', views.activate_user, name='activate_user'),
    path('dashboard/admin/user/<int:user_id>/deactivate/', views.deactivate_user, name='deactivate_user'),
]