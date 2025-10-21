# core/views.py

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Progress, Course, Topic, TopicCompletion # Added TopicCompletion# Make sure Topic is imported
# Import get_user_model to reliably get your CustomUser model
from django.contrib.auth import login, get_user_model # Removed authenticate
import logging

logger = logging.getLogger(__name__)

# Get your custom user model
User = get_user_model()

# Home view (landing page)
def home_view(request):
    return render(request, 'index.html')

# Login view - Reverted to passwordless logic for students
def login_view(request):
    context = {}
    if request.method == 'POST':
        phone_input = request.POST.get('phone') # Get raw input

        if not phone_input:
            messages.error(request, 'Please enter a phone number.')
            return render(request, 'login.html', context) # Pass context

        phone = phone_input.strip() # Clean input
        logger.info(f"Attempting login with cleaned phone: {phone}")
        context['phone_attempted'] = phone # Add to context

        try:
            # Find the user directly by phone number
            user = User.objects.get(phone=phone)
            logger.info(f"User found: {user.name}, Payment Status: {user.payment_status}")

            # Check if the user has paid
            if user.payment_status:
                # Log the user in directly, no password check
                login(request, user)
                logger.info(f"Login successful for user {user.phone}. Redirecting to dashboard.")
                return redirect('dashboard') # Assumes URL name 'dashboard' exists
            else:
                # User exists, but has not paid
                logger.warning(f"Login failed for user {user.phone}: Payment not confirmed.")
                messages.error(request, 'This account is not active. Please complete your payment.')

        except User.DoesNotExist:
            # No user with this phone number was found - Correct error message
            logger.warning(f"Login failed: Phone number {phone} not found.")
            messages.error(
                request,
                f'The phone number {phone} is not registered. Kindly contact the help center.',
                extra_tags='not_registered' # Tag for template logic
            )
            # Add contact info as separate messages if needed
            messages.info(request, 'Mobile: 12345678910', extra_tags='contact_phone')
            messages.info(request, 'WhatsApp: 9876543210', extra_tags='contact_whatsapp')

    # If GET request or if login fails, render the login page with context
    return render(request, 'login.html', context)


# Dashboard view - Simplified for student role ONLY
@login_required
def dashboard_view(request):
    user = request.user

    if hasattr(user, 'role') and user.role == 'student':
        progress_records = Progress.objects.filter(student=user).select_related('course')
        courses = Course.objects.all()

        stem_progress_record = progress_records.filter(course__title='STEM').first()
        stem_topics = []
        stem_progress_value = 0
        if stem_progress_record and stem_progress_record.course:
            stem_topics = stem_progress_record.course.topics.all()
            stem_progress_value = stem_progress_record.overall_progress

        impact_progress_record = progress_records.filter(course__title='IMPACT').first()
        impact_progress_value = 0
        if impact_progress_record:
             impact_progress_value = impact_progress_record.overall_progress

        num_courses_with_progress = 0
        total_progress = 0
        if stem_progress_record:
            num_courses_with_progress += 1
            total_progress += stem_progress_value
        if impact_progress_record:
            num_courses_with_progress += 1
            total_progress += impact_progress_value
        overall_progress = total_progress / num_courses_with_progress if num_courses_with_progress > 0 else 0

        # --- ADDED LOGIC: Fetch Topic Completions for the student ---
        # Get all progress IDs for the student
        student_progress_ids = progress_records.values_list('id', flat=True)
        # Fetch completions linked to those progress records
        topic_completions = TopicCompletion.objects.filter(progress_id__in=student_progress_ids).select_related('topic')
        # Optional: Create a dictionary for easy lookup in the template if needed
        # completed_topic_ids = set(tc.topic_id for tc in topic_completions if tc.completed)
        # --- End Added Logic ---

        context = {
            'user': user,
            'progress_records': progress_records, 
            'courses': courses,
            'stem_progress': stem_progress_value, 
            'impact_progress': impact_progress_value,
            'overall_progress': overall_progress,
            'stem_topics': stem_topics, 
            # --- Add completions to context ---
            'topic_completions': topic_completions, # Pass the queryset
            # 'completed_topic_ids': completed_topic_ids, # Pass the set of IDs if using that approach
        }
        
        return render(request, 'dashboard.html', context) # Use dashboard.html

    # Handle non-student users
    logger.warning(f"User {user.phone} with role '{getattr(user, 'role', 'unknown')}' attempted to access student dashboard.")
    messages.warning(request, "Access restricted.")
    return redirect('home')