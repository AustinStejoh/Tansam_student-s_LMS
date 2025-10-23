from django.contrib.auth import login, logout
from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse
from .models import CustomUser
import logging

logger = logging.getLogger(__name__)

def login_view(request):
    if request.method == 'POST':
        phone = request.POST.get('phone')
        logger.info(f"Attempting login with phone: {phone}")
        print(phone)
        try:
            user = CustomUser.objects.get(phone=phone)
            logger.info(f"Found user: {user.phone}, Payment Status: {user.payment_status}, Password Usable: {user.has_usable_password()}")
            if user.payment_status:
                login(request, user)
                messages.success(request, 'Login successful! Redirecting to dashboard.')
                return redirect(reverse('dashboard'))
            else:
                messages.error(request, 'Access denied. Only paid students can log in.')
        except CustomUser.DoesNotExist:
            logger.info(f"Phone {phone} not found in database")
            messages.error(request, 'Phone number not found.')
    else:
        return render(request, 'login.html')
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect(reverse('login'))