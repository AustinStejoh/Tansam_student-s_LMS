from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import Payment

# 'get_user_model' and 'User = ...' have been removed from here.

@receiver(post_save, sender=Payment)
def handle_payment(sender, instance, created, **kwargs):
    if created:
        student = instance.student
        student.payment_status = True
        student.save()
        send_mail(
            subject='Welcome to Our E-Learning Portal!',
            message=f'Hi {student.name},\n\nYour account is ready. Login with your phone number at our portal.',
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[student.email],
            fail_silently=False,
        )