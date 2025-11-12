#!/usr/bin/env python
"""Test email sending functionality"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'elearning.settings')
django.setup()

from admin_panel.email_utils import send_password_email, send_password_reset_email

print("=" * 60)
print("Testing Email Sending Functionality")
print("=" * 60)

# Test 1: Send password email
print("\n[Test 1] Sending password email...")
result1 = send_password_email(
    student_email='joeljoel9486@gmail.com',
    student_name='Test Student',
    phone='1234567890',
    password='testpass123'
)
print(f"✓ Password email sent: {result1}" if result1 else f"✗ Password email failed")

# Test 2: Send password reset email
print("\n[Test 2] Sending password reset email...")
result2 = send_password_reset_email(
    student_email='joeljoel9486@gmail.com',
    student_name='Test Student',
    phone='1234567890',
    new_password='newpass456'
)
print(f"✓ Password reset email sent: {result2}" if result2 else f"✗ Password reset email failed")

print("\n" + "=" * 60)
print(f"Overall Result: {'✓ ALL TESTS PASSED' if result1 and result2 else '✗ SOME TESTS FAILED'}")
print("=" * 60)
