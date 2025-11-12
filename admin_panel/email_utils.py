from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def send_password_email(student_email, student_name, phone, password):
    """
    Send password email to student when admin creates or resets their password.
    
    Args:
        student_email: Email address of the student
        student_name: Full name of the student
        phone: Phone number of the student
        password: The generated/reset password
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        subject = 'Your Tansam E-Learning Portal Credentials'
        
        portal_url = getattr(settings, 'PORTAL_URL', 'http://127.0.0.1:8000')
        login_url = f"{portal_url}/login/"
        
        context = {
            'student_name': student_name,
            'phone': phone,
            'password': password,
            'portal_url': portal_url,
            'login_url': login_url
        }
        
        # Try to render HTML email template, fall back to plain text
        try:
            html_message = render_to_string('emails/password_email.html', context)
        except Exception as e:
            logger.warning(f"Could not render HTML email template: {str(e)}")
            html_message = None
        
        message = f"""
Dear {student_name},

Your account has been created on the Tansam E-Learning Portal!

LOGIN CREDENTIALS:
Phone: {phone}
Password: {password}

You can now log in at: {context['login_url']}

Please keep your password safe and do not share it with anyone.

If you have any questions, contact the admin.

Best regards,
Tansam E-Learning Team
        """.strip()
        
        # Send email
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[student_email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Password email sent successfully to {student_email}")
        return True
    
    except Exception as e:
        logger.error(f"Failed to send password email to {student_email}: {str(e)}")
        return False


def send_password_reset_email(student_email, student_name, phone, new_password):
    """
    Send password reset email to student when admin resets their password.
    
    Args:
        student_email: Email address of the student
        student_name: Full name of the student
        phone: Phone number of the student
        new_password: The newly generated password
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        subject = 'Your Tansam Portal Password Has Been Reset'
        
        portal_url = getattr(settings, 'PORTAL_URL', 'http://127.0.0.1:8000')
        login_url = f"{portal_url}/login/"
        
        context = {
            'student_name': student_name,
            'phone': phone,
            'password': new_password,
            'portal_url': portal_url,
            'login_url': login_url
        }
        
        # Try to render HTML email template, fall back to plain text
        try:
            html_message = render_to_string('emails/password_reset_email.html', context)
        except Exception as e:
            logger.warning(f"Could not render HTML email template: {str(e)}")
            html_message = None
        
        message = f"""
Dear {student_name},

Your password on the Tansam E-Learning Portal has been reset by an administrator.

NEW LOGIN CREDENTIALS:
Phone: {phone}
Password: {new_password}

You can now log in at: {context['login_url']}

Please keep your password safe and do not share it with anyone.

If you did not request this change, please contact the admin immediately.

Best regards,
Tansam E-Learning Team
        """.strip()
        
        # Send email
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[student_email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Password reset email sent successfully to {student_email}")
        return True
    
    except Exception as e:
        logger.error(f"Failed to send password reset email to {student_email}: {str(e)}")
        return False
