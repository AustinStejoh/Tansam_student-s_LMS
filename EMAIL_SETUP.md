# Email Configuration Guide for Tansam E-Learning Portal

## Overview

The Tansam E-Learning Portal now includes automatic email sending for generated student passwords. When an admin creates a new student or resets an existing student's password, a professional HTML email is automatically sent to the student with their login credentials.

## How It Works

### Password Email Sending Flow

1. **Admin creates a student** via `/panel/students/add/`
   - A random password is generated (8 characters)
   - Student is marked with `password_set = True`
   - Email is sent to student's email address with credentials
   - Admin sees confirmation message

2. **Admin resets a student's password** via `/panel/students/` (Reset Password button)
   - A new random password is generated
   - Email is sent to student with new credentials
   - Admin sees confirmation message

### Email Templates

Two professional HTML email templates are included:

- **`templates/emails/password_email.html`** — Initial account creation email
- **`templates/emails/password_reset_email.html`** — Password reset notification

Both include:
- Company branding (gradient header)
- Clear credential display
- Security notices
- Responsive design for mobile/desktop
- Plain text fallback

### Email Utility Functions

Located in `admin_panel/email_utils.py`:

- `send_password_email(email, name, phone, password)` — Send account creation email
- `send_password_reset_email(email, name, phone, new_password)` — Send password reset email

## Setup Instructions

### 1. Configure SMTP (Email Server)

Update `elearning/settings.py`:

```python
# Email Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'  # or your email provider's SMTP server
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'  # Your email address
EMAIL_HOST_PASSWORD = 'your-app-password'  # App-specific password (not your Gmail password!)
DEFAULT_FROM_EMAIL = 'your-email@gmail.com'
```

### 2. Gmail Setup (Recommended)

If using Gmail:

1. Enable 2-Factor Authentication on your Gmail account
2. Generate an "App Password":
   - Go to https://myaccount.google.com/apppasswords
   - Select "Mail" and "Windows Computer"
   - Google will generate a 16-character password
   - Use this password in `EMAIL_HOST_PASSWORD`
3. Update settings with your email and app password

### 3. Alternative Email Providers

**SendGrid:**
```python
EMAIL_BACKEND = 'sendgrid_backend.SendgridBackend'
SENDGRID_API_KEY = 'your-sendgrid-api-key'
DEFAULT_FROM_EMAIL = 'no-reply@yourdomain.com'
```

**AWS SES:**
```python
EMAIL_BACKEND = 'django_ses.SESBackend'
AWS_SES_REGION_NAME = 'us-east-1'
AWS_SES_REGION_ENDPOINT = 'email.us-east-1.amazonaws.com'
```

### 4. Test Email Configuration

Run this command to test your email setup:

```bash
python manage.py shell
```

Then in the shell:

```python
from django.core.mail import send_mail
from django.conf import settings

send_mail(
    subject='Test Email from Tansam',
    message='If you see this, email is working!',
    from_email=settings.DEFAULT_FROM_EMAIL,
    recipient_list=['your-test-email@example.com'],
    fail_silently=False,
)
print("Email sent successfully!")
```

## Features

### Automatic Email Sending

✅ **When admin creates a student:**
- Generates secure 8-character password
- Sends professional HTML email with credentials
- Shows success/warning message to admin
- Student receives email with login instructions

✅ **When admin resets a student's password:**
- Generates new secure 8-character password
- Sends password reset notification email
- Includes security notice about unauthorized resets
- Admin sees confirmation with student's email

### Email Content Includes

- Student's name and phone number
- Login credentials (phone + password)
- Direct login link (if `PORTAL_URL` is configured)
- Security tips and warnings
- Company branding and footer
- Responsive HTML design
- Plain text fallback for email clients without HTML support

### Error Handling

- If email sending fails, admin sees a warning message (not a hard error)
- Password is still set on the account (admin can share manually)
- Errors are logged for debugging
- System continues to function if email is unavailable

## Configuration Variables

### Optional Settings

Add to `elearning/settings.py` for customization:

```python
# Portal URL for login links in emails (optional)
PORTAL_URL = 'https://yourdomain.com'  # Default: http://127.0.0.1:8000

# Email sender name (optional)
EMAIL_FROM_NAME = 'Tansam E-Learning'
```

## Troubleshooting

### "Failed to send password email" warning

**Possible causes:**
1. **SMTP credentials incorrect** — Verify email and password in settings
2. **Gmail app password not generated** — Follow Gmail setup steps above
3. **Firewall/network blocking** — Check if port 587 is open
4. **Email provider disabled** — Check email account settings

**Solution:**
- Test SMTP connection with `python manage.py shell`
- Check Django error logs for specific error messages
- Verify credentials in settings.py
- For Gmail, ensure 2FA is enabled and use app password

### "AttributeError: 'AnonymousUser'" on admin panel

**Cause:** User trying to access admin panel without logging in

**Solution:**
- Admin login required at `/panel/login/`
- Use email and password (not phone number)
- Default admin: admin@tansam.edu / AdminPass123!

### Email template not rendering

**Cause:** HTML email template not found

**Solution:**
- Ensure `templates/emails/` directory exists
- Verify template files are present and not corrupted
- System automatically falls back to plain text if HTML fails

## Best Practices

1. **Use environment variables for sensitive data:**
   ```python
   import os
   from dotenv import load_dotenv
   
   load_dotenv()
   EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
   EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
   ```

2. **Use app-specific passwords instead of main account password**
   - Increases security
   - Allows revoking access without changing main password

3. **Monitor email logs:**
   - Check `logger.error()` messages in logs
   - Admin messages show if email failed
   - Consider adding email audit trail

4. **Customize email templates:**
   - Edit `templates/emails/password_email.html`
   - Update company name, logo, colors
   - Add custom branding

5. **Set PORTAL_URL in production:**
   - Update login links in emails to point to your domain
   - Helps users access correct portal instance

## Testing Checklist

- [ ] Email provider configured (Gmail/SendGrid/AWS SES)
- [ ] SMTP credentials correct
- [ ] `DEFAULT_FROM_EMAIL` matches email provider
- [ ] Test email sent successfully using shell
- [ ] Create test student and verify email received
- [ ] Check email formatting (HTML rendering)
- [ ] Verify all links in email work
- [ ] Reset student password and verify reset email
- [ ] Check that admin sees success/warning messages

## Support

If email sending fails:

1. Check Django logs for specific error messages
2. Verify SMTP configuration in settings.py
3. Test SMTP connection manually
4. Ensure email provider allows less secure apps (if applicable)
5. Check firewall/network restrictions

For production deployments, consider using a dedicated email service (SendGrid, AWS SES) for better reliability and deliverability.
