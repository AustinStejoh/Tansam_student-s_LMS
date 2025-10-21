from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser
from django import forms

class CustomUserCreationForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ('phone', 'email', 'name', 'class_level', 'role', 'payment_status')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_unusable_password()  # ensures password is not required
        if commit:
            user.save()
        return user


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    model = CustomUser
    list_display = ('name', 'phone', 'email', 'class_level', 'role', 'payment_status', 'is_active')
    list_filter = ('role', 'class_level', 'payment_status', 'is_active')

    fieldsets = (
        (None, {'fields': ('phone', 'email', 'name', 'class_level', 'role', 'payment_status')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone', 'email', 'name', 'class_level', 'role', 'payment_status'),
        }),
    )

    search_fields = ('phone', 'email', 'name')
    ordering = ('phone',)
