from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'role', 'phone', 'must_change_password', 'is_staff', 'date_joined']
    list_filter = ['role', 'must_change_password', 'is_staff', 'is_active']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'phone']
    fieldsets = UserAdmin.fieldsets + (
        ('DeviX Academy Role & Profile', {
            'fields': ('role', 'phone', 'must_change_password')
        }),
    )
