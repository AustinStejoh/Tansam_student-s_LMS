from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin, Group, Permission
from django.utils.translation import gettext_lazy as _

class CustomUserManager(BaseUserManager):
    def create_user(self, phone, email, name, class_level, password=None, **extra_fields):
        if not phone:
            raise ValueError('Phone number is required')
        email = self.normalize_email(email)
        user = self.model(phone=phone, email=email, name=name, class_level=class_level, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, email, name, class_level, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'admin')
        extra_fields.setdefault('payment_status', True)
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

    objects = CustomUserManager()

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = ['email', 'name', 'class_level']

    def __str__(self):
        return self.name

    # Override groups and user_permissions to avoid reverse accessor clashes
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name=_('groups'),
        blank=True,
        help_text=_('The groups this user belongs to. A user will get all permissions granted to each of their groups.'),
        
        # This name must be unique
        related_name='custom_user_groups', 
        
        related_query_name='user',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name=_('user permissions'),
        blank=True,
        help_text=_('Specific permissions for this user.'),
        
        # This name must also be unique (and different from the one for groups)
        related_name='custom_user_permissions', 
        
        related_query_name='user',
    )