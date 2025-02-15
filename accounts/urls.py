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
    path('profile/', update_profile, name='update_profile'),
    path('profile/change-password/', change_password, name='change_password'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('client-dashboard/', client_dashboard, name='client_dashboard'),
    path('book-appointment/', book_appointment, name='book_appointment'),
    path('cancel-appointment/<int:appointment_id>/', cancel_appointment, name='cancel_appointment'),
    path('reschedule-appointment/<int:appointment_id>/', reschedule_appointment, name='reschedule_appointment'),
    path('logout/', views.user_logout, name='logout'),
]