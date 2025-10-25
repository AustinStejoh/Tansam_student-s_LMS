from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import login, logout, get_user_model
from django.urls import reverse
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
            messages.error(
                request,
                'Your mobile number is not registered. Contact your mentor.',
                extra_tags='not_registered'
            )

    return render(request, 'login.html', context)


# ------------------- LOGOUT VIEW -------------------
def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect(reverse('login'))


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


# ------------------- COURSE DETAIL VIEW -------------------
@login_required
def course_detail_view(request, course_id):
    """
    Displays detailed information about a selected course,
    including its topics, completion status, and progress percentage.
    """
    user = request.user
    course = get_object_or_404(Course, id=course_id)
    topics = Topic.objects.filter(course=course)

    # Get student's progress record
    progress = Progress.objects.filter(student=user, course=course).first()

    # Fetch completed topics
    completed_topics = set()
    if progress:
        completed_topics = set(
            TopicCompletion.objects.filter(progress=progress, completed=True)
            .values_list('topic_id', flat=True)
        )

    # Calculate progress percentage
    total_topics = topics.count()
    completed_count = len(completed_topics)
    course_progress_percent = (completed_count / total_topics) * 100 if total_topics > 0 else 0

    context = {
        'course': course,
        'topics': topics,
        'progress': progress,
        'completed_topics': completed_topics,
        'course_progress_percent': round(course_progress_percent, 1),
    }
    return render(request, 'course_detail.html', context)


# ------------------- TOPIC DETAIL VIEW -------------------
@login_required
def topic_detail_view(request, topic_id):
    """
    Displays full study content and assignment for a single topic.
    """
    topic = get_object_or_404(Topic, id=topic_id)
    course = topic.course
    user = request.user

    # Ensure only enrolled students can access
    progress = Progress.objects.filter(student=user, course=course).first()
    if not progress:
        messages.warning(request, "You are not enrolled in this course.")
        return redirect('dashboard')

    # Optional: Track when a topic is viewed
    TopicCompletion.objects.get_or_create(progress=progress, topic=topic, defaults={'completed': False})

    context = {
        'topic': topic,
        'course': course,
        'progress': progress,
    }
    return render(request, 'topic_detail.html', context)
