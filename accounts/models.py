from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin, Group, Permission
from django.utils.translation import gettext_lazy as _


class CustomUserManager(BaseUserManager):
    def create_user(self, phone, email, name, class_level, password=None, **extra_fields):
        if not phone:
            raise ValueError('Phone number is required')

        email = self.normalize_email(email)
        user = self.model(
            phone=phone,
            email=email,
            name=name,
            class_level=class_level,
            **extra_fields
        )

        # ✅ Allow users without password (for OTP or phone login)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()

        user.save(using=self._db)
        return user

    def create_superuser(self, phone, email, name, class_level, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'admin')
        extra_fields.setdefault('payment_status', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(phone, email, name, class_level, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    ROLES = (
        ('student', 'Student'),
        ('mentor', 'Mentor'),
        ('admin', 'Admin'),
    )

    CLASS_LEVELS = (
        ('6-8', 'Classes 6-8'),
        ('9-12', 'Classes 9-12'),
    )

    phone = models.CharField(max_length=15, unique=True)
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=100)
    class_level = models.CharField(max_length=5, choices=CLASS_LEVELS)
    role = models.CharField(max_length=10, choices=ROLES, default='student')
    payment_status = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    # Progress tracking fields
    progress = models.IntegerField(default=0)
    stem_progress = models.IntegerField(default=0)
    impact_progress = models.IntegerField(default=0)
    assignments_due = models.IntegerField(default=0)

    # ✅ Keep default relations to avoid FK conflicts
    groups = models.ManyToManyField(
        Group,
        related_name="customuser_set",
        blank=True
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name="customuser_set",
        blank=True
    )

    objects = CustomUserManager()

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = ['email', 'name', 'class_level']

    def __str__(self):
        return self.name
