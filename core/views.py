from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import login, get_user_model
from .models import Progress, Course, Topic, TopicCompletion
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


# ------------------- HOME VIEW -------------------
def home_view(request):
    return render(request, 'index.html')


# ------------------- LOGIN VIEW -------------------
def login_view(request):
    """
    Passwordless login:
    - If phone number exists in DB and payment_status=True -> auto-login.
    - Otherwise -> show error messages.
    """
    context = {}

    if request.method == 'POST':
        phone_input = request.POST.get('phone')
      
        if not phone_input:
            messages.error(request, 'Please enter a phone number.')
            return render(request, 'login.html', context)

        phone = phone_input.strip()
        logger.info(f"Attempting login with phone: {phone}")
        context['phone_attempted'] = phone

        try:
            user = User.objects.get(phone=phone)
            logger.info(f"User found: {user.name}, Payment: {user.payment_status}, Role: {user.role}")

            # ✅ Allow direct login only for students with confirmed payment
            if user.role == 'student' and user.payment_status:
                login(request, user)
                logger.info(f"Login successful for {user.phone}")
                messages.success(request, f"Welcome {user.name}!")
                return redirect('dashboard')

            elif not user.payment_status:
                messages.error(request, 'Your payment is not confirmed. Please contact admin.')

            else:
                messages.error(request, 'Access restricted to students only.')

        except User.DoesNotExist:
            logger.warning(f"Phone not found in database: {phone}")
            messages.error(request, 'Your mobile number is not registered. Contact your mentor.', extra_tags='not_registered')

    return render(request, 'login.html', context)


# ------------------- DASHBOARD VIEW -------------------
@login_required
def dashboard_view(request):
    user = request.user

    # Ensure only students can access this view
    if getattr(user, 'role', None) != 'student':
        messages.warning(request, "Access restricted to student accounts.")
        logger.warning(f"Unauthorized access attempt by {user.phone} ({user.role})")
        return redirect('home')

    # Retrieve student progress
    progress_records = Progress.objects.filter(student=user).select_related('course')
    courses = Course.objects.all()

    course_progress = []
    for course in courses:
        progress_record = progress_records.filter(course=course).first()
        progress_value = progress_record.overall_progress if progress_record else 0
        course_progress.append({
            'course': course,
            'progress': progress_value,
            'topics': getattr(course, 'topics', []).all() if hasattr(course, 'topics') else [],
        })

    # Calculate overall progress
    num_courses_with_progress = sum(1 for cp in course_progress if cp['progress'] > 0)
    total_progress = sum(cp['progress'] for cp in course_progress if cp['progress'] > 0)
    overall_progress = total_progress / num_courses_with_progress if num_courses_with_progress > 0 else 0

    # Find completed topics
    student_progress_ids = progress_records.values_list('id', flat=True)
    topic_completions = TopicCompletion.objects.filter(progress_id__in=student_progress_ids).select_related('topic')
    completed_topic_ids = {tc.topic_id for tc in topic_completions if tc.completed}

    context = {
        'user': user,
        'progress_records': progress_records,
        'courses': courses,
        'course_progress': course_progress,
        'overall_progress': overall_progress,
        'completed_topic_ids': completed_topic_ids,
        'notifications': 1,
    }
    return render(request, 'dashboard.html', context)
