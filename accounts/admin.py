from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser
from .forms import CustomUserCreationForm, CustomUserChangeForm

class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser
    list_display = ['phone', 'name', 'email', 'class_level', 'role', 'payment_status', 'is_active']
    list_filter = ['role', 'class_level', 'payment_status']
    fieldsets = (
        (None, {'fields': ('phone', 'password')}),
        ('Personal Info', {'fields': ('name', 'email', 'class_level', 'role', 'payment_status')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
    )
    add_fieldsets = (
        (None, {
            'fields': ('phone', 'email', 'name', 'class_level', 'role', 'payment_status', 'password1', 'password2')}
        ),
    )
    search_fields = ['phone', 'name', 'email']
    ordering = ['phone']

admin.site.register(CustomUser, CustomUserAdmin)