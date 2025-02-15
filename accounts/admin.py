from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('user_type', 'phone_number')}),
    )
    list_display = ('username', 'email', 'user_type', 'is_staff', 'is_superuser')

    def get_readonly_fields(self, request, obj=None):
        if not request.user.is_superuser:  # Only superusers can change roles
            return ('user_type',)
        return super().get_readonly_fields(request, obj)

admin.site.register(User, CustomUserAdmin)
