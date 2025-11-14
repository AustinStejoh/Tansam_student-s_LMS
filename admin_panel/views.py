from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.urls import reverse
from django.http import JsonResponse
from django.core.exceptions import ValidationError
from django.db.models import Count, Q
from core.models import (
    Course, Topic, Assignment, Submission, Payment, MCQQuestion,
    FinalExam, FinalExamQuestion, FinalExamSubmission, Progress, TopicCompletion
)
from accounts.models import CustomUser
from .email_utils import send_password_email, send_password_reset_email
import logging
import uuid

logger = logging.getLogger(__name__)


def is_admin(user):
    """Check if user is an admin."""
    return user.is_authenticated and user.role == 'admin'


def admin_login_view(request):
    """Admin login page - requires email and password."""
    if request.user.is_authenticated and request.user.role == 'admin':
        return redirect('admin_dashboard')
    
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        try:
            # Find user by email
            admin_user = CustomUser.objects.get(email=email)
            
            # Verify password
            if admin_user.check_password(password) and admin_user.role == 'admin':
                login(request, admin_user)
                messages.success(request, f'Welcome back, {admin_user.name}!')
                return redirect('admin_dashboard')
            else:
                messages.error(request, 'Invalid email or password.')
        except CustomUser.DoesNotExist:
            messages.error(request, 'Admin account not found.')
        except Exception as e:
            logger.error(f"Admin login error: {str(e)}")
            messages.error(request, 'An error occurred during login.')
    
    return render(request, 'admin_login.html')


@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def admin_dashboard(request):
    """Main admin dashboard with student performance overview."""
    courses_count = Course.objects.count()
    topics_count = Topic.objects.count()
    students = CustomUser.objects.filter(role='student')
    students_count = students.count()
    paid_students_count = students.filter(payment_status=True).count()
    students_with_password = students.filter(password_set=True).count()
    
    # Get top performing students
    top_students = students.order_by('-progress')[:5]
    
    # Add completion count for each student
    student_performance = []
    from core.models import TopicCompletion
    # Overall completion stats across all topic completions (for charts)
    try:
        overall_total_completions = TopicCompletion.objects.count()
        overall_completed_completions = TopicCompletion.objects.filter(completed=True).count()
        overall_completion_percentage = int((overall_completed_completions / overall_total_completions * 100) if overall_total_completions > 0 else 0)
    except Exception:
        overall_total_completions = 0
        overall_completed_completions = 0
        overall_completion_percentage = 0
    for student in top_students:
        completed_count = TopicCompletion.objects.filter(
            progress__student=student,
            completed=True
        ).count()
        student_performance.append({
            'student': student,
            'completed_topics': completed_count,
            'progress': student.progress
        })
    
    context = {
        'courses_count': courses_count,
        'topics_count': topics_count,
        'students_count': students_count,
        'paid_students_count': paid_students_count,
        'students_with_password': students_with_password,
        'student_performance': student_performance,
        'all_students': students,
        'overall_total_completions': overall_total_completions,
        'overall_completed_completions': overall_completed_completions,
        'overall_completion_percentage': overall_completion_percentage,
    }
    
    return render(request, 'admin_dashboard.html', context)


@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def manage_students(request):
    """View and manage all students."""
    students = CustomUser.objects.filter(role='student')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        student_id = request.POST.get('student_id')
        
        try:
            student = CustomUser.objects.get(id=student_id)
            
            if action == 'toggle_payment':
                student.payment_status = not student.payment_status
                student.save()
                messages.success(request, f'Payment status updated for {student.name}')
            
            elif action == 'reset_password':
                new_password = str(uuid.uuid4())[:8]
                student.set_password(new_password)
                student.password_set = True
                student.save()
                
                # Send password reset email
                email_sent = send_password_reset_email(
                    student.email,
                    student.name,
                    student.phone,
                    new_password
                )
                
                if email_sent:
                    messages.success(request, f'Password reset successfully! Email sent to {student.email} with the new password.')
                else:
                    messages.warning(request, f'Password reset but email delivery failed. New password: {new_password}')
            
            elif action == 'delete_student':
                student_name = student.name
                student.delete()
                messages.success(request, f'Student {student_name} has been deleted.')
        
        except CustomUser.DoesNotExist:
            messages.error(request, 'Student not found.')
        except Exception as e:
            logger.error(f"Error managing student: {str(e)}")
            messages.error(request, 'An error occurred.')
        
        return redirect('manage_students')
    
    context = {'students': students}
    return render(request, 'manage_students.html', context)


@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def add_student(request):
    """Add a new student manually."""
    if request.method == 'POST':
        phone = request.POST.get('phone')
        email = request.POST.get('email')
        name = request.POST.get('name')
        class_level = request.POST.get('class_level')
        payment_status = request.POST.get('payment_status') == 'on'
        
        # Generate initial password
        initial_password = str(uuid.uuid4())[:8]
        
        try:
            student = CustomUser.objects.create_user(
                phone=phone,
                email=email,
                name=name,
                class_level=class_level,
                password=initial_password
            )
            student.payment_status = payment_status
            student.password_set = True
            student.save()
            
            # Send password email
            email_sent = send_password_email(
                email,
                name,
                phone,
                initial_password
            )
            
            if email_sent:
                messages.success(request, f'Student {name} added successfully! Welcome email with credentials sent to {email}')
            else:
                messages.warning(request, f'Student {name} added but email delivery failed. Password: {initial_password}')
            
            return redirect('manage_students')
        
        except Exception as e:
            logger.error(f"Error adding student: {str(e)}")
            messages.error(request, f'Error: {str(e)}')
    
    context = {'class_levels': CustomUser.CLASS_LEVELS}
    return render(request, 'add_student.html', context)


@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def manage_courses(request):
    """View and manage all courses."""
    courses = Course.objects.all().order_by('title')
    context = {'courses': courses}
    return render(request, 'manage_courses.html', context)


@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def add_course(request):
    """Add a new course."""
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        
        try:
            course = Course.objects.create(
                title=title,
                description=description
            )
            messages.success(request, f'Course "{title}" added successfully!')
            return redirect('manage_courses')
        except Exception as e:
            logger.error(f"Error adding course: {str(e)}")
            messages.error(request, f'Error: {str(e)}')
    
    return render(request, 'add_course.html')


@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def edit_course(request, course_id):
    """Edit an existing course."""
    course = get_object_or_404(Course, id=course_id)
    
    if request.method == 'POST':
        course.title = request.POST.get('title')
        course.description = request.POST.get('description')
        
        try:
            course.save()
            messages.success(request, 'Course updated successfully!')
            return redirect('manage_courses')
        except Exception as e:
            logger.error(f"Error updating course: {str(e)}")
            messages.error(request, f'Error: {str(e)}')
    
    context = {'course': course}
    return render(request, 'edit_course.html', context)


@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def delete_course(request, course_id):
    """Delete a course."""
    course = get_object_or_404(Course, id=course_id)
    course_title = course.title
    
    try:
        course.delete()
        messages.success(request, f'Course "{course_title}" deleted successfully!')
    except Exception as e:
        logger.error(f"Error deleting course: {str(e)}")
        messages.error(request, f'Error: {str(e)}')
    
    return redirect('manage_courses')


@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def student_performance(request, student_id):
    """Show detailed performance of a student."""
    from core.models import TopicCompletion, Progress
    
    student = get_object_or_404(CustomUser, id=student_id, role='student')
    
    # Get student's progress record
    try:
        progress = Progress.objects.get(student=student)
    except Progress.DoesNotExist:
        progress = None
    
    # Get all topic completions for the student
    completions = TopicCompletion.objects.filter(progress__student=student).select_related('topic', 'topic__course')
    
    # Calculate statistics
    total_topics = completions.count()
    completed_topics = completions.filter(completed=True).count()
    completion_percentage = int((completed_topics / total_topics * 100) if total_topics > 0 else 0)
    
    # Group by course
    from django.db.models import Count, Q
    courses_stats = {}
    if progress:
        for completion in completions:
            course = completion.topic.course
            if course.id not in courses_stats:
                courses_stats[course.id] = {
                    'course': course,
                    'total': 0,
                    'completed': 0,
                    'completions': [],
                    'percentage': 0
                }
            courses_stats[course.id]['total'] += 1
            if completion.completed:
                courses_stats[course.id]['completed'] += 1
            courses_stats[course.id]['completions'].append(completion)
        
        # Calculate percentages for each course
        for course_id in courses_stats:
            stats = courses_stats[course_id]
            stats['percentage'] = int((stats['completed'] / stats['total'] * 100) if stats['total'] > 0 else 0)
    
    context = {
        'student': student,
        'progress': progress,
        'total_topics': total_topics,
        'completed_topics': completed_topics,
        'completion_percentage': completion_percentage,
        'courses_stats': list(courses_stats.values()),
        'completions': completions,
    }
    
    return render(request, 'student_performance.html', context)


@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def admin_logout_view(request):
    """Admin logout."""
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('admin_login')


# ===========================
# TOPICS MANAGEMENT
# ===========================
@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def manage_topics(request):
    """View and manage all topics."""
    course_id = request.GET.get('course')
    if course_id:
        topics = Topic.objects.filter(course_id=course_id).order_by('order')
    else:
        topics = Topic.objects.all().order_by('course__title', 'order')
    
    courses = Course.objects.all()
    context = {'topics': topics, 'courses': courses, 'selected_course': course_id}
    return render(request, 'admin/manage_topics.html', context)


@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def api_topics(request):
    """AJAX endpoint: return topics for a course as JSON.

    Query params: ?course=<id>
    Returns: JSON list of {id, title}
    """
    course_id = request.GET.get('course')
    if not course_id:
        return JsonResponse({'error': 'course parameter is required'}, status=400)

    try:
        topics_qs = Topic.objects.filter(course_id=course_id).order_by('order').values('id', 'title')
        topics = list(topics_qs)
        return JsonResponse(topics, safe=False)
    except Exception as e:
        logger.error(f"Error fetching topics for course {course_id}: {e}")
        return JsonResponse({'error': 'internal server error'}, status=500)


@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def add_topic(request):
    """Add a new topic."""
    courses = Course.objects.all()
    # Allow pre-selecting a course via query param ?course=<id>
    selected_course = request.GET.get('course')
    try:
        selected_course = int(selected_course) if selected_course else None
    except (TypeError, ValueError):
        selected_course = None
    if request.method == 'POST':
        course_id = request.POST.get('course')
        title = request.POST.get('title')
        order = request.POST.get('order')
        video_file = request.FILES.get('video_file')
        ppt_file = request.FILES.get('ppt_file')
        poster_image = request.FILES.get('poster_image')
        
        try:
            course = Course.objects.get(id=course_id)
            topic = Topic.objects.create(
                course=course,
                title=title,
                order=int(order) if order else Topic.objects.filter(course=course).count() + 1,
                video_file=video_file,
                ppt_file=ppt_file,
                poster_image=poster_image
            )
            messages.success(request, f'Topic "{title}" added successfully!')
            return redirect('manage_topics')
        except Exception as e:
            logger.error(f"Error adding topic: {str(e)}")
            messages.error(request, f'Error: {str(e)}')
    
    context = {'courses': courses, 'selected_course': selected_course}
    return render(request, 'admin/add_topic.html', context)


@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def edit_topic(request, topic_id):
    """Edit an existing topic."""
    topic = get_object_or_404(Topic, id=topic_id)
    courses = Course.objects.all()
    
    if request.method == 'POST':
        topic.course_id = request.POST.get('course')
        topic.title = request.POST.get('title')
        topic.order = request.POST.get('order')
        
        if request.FILES.get('video_file'):
            topic.video_file = request.FILES.get('video_file')
        if request.FILES.get('ppt_file'):
            topic.ppt_file = request.FILES.get('ppt_file')
        if request.FILES.get('poster_image'):
            topic.poster_image = request.FILES.get('poster_image')
        
        try:
            topic.save()
            messages.success(request, 'Topic updated successfully!')
            return redirect('manage_topics')
        except Exception as e:
            logger.error(f"Error updating topic: {str(e)}")
            messages.error(request, f'Error: {str(e)}')
    
    context = {'topic': topic, 'courses': courses}
    return render(request, 'admin/edit_topic.html', context)


@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def delete_topic(request, topic_id):
    """Delete a topic."""
    topic = get_object_or_404(Topic, id=topic_id)
    topic_title = topic.title
    
    try:
        topic.delete()
        messages.success(request, f'Topic "{topic_title}" deleted successfully!')
    except Exception as e:
        logger.error(f"Error deleting topic: {str(e)}")
        messages.error(request, f'Error: {str(e)}')
    
    return redirect('manage_topics')


# ===========================
# ASSIGNMENTS MANAGEMENT
# ===========================
@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def manage_assignments(request):
    """View and manage all assignments."""
    course_id = request.GET.get('course')
    if course_id:
        assignments = Assignment.objects.filter(course_id=course_id).order_by('-created_at')
    else:
        assignments = Assignment.objects.all().order_by('-created_at')
    
    courses = Course.objects.all()
    context = {'assignments': assignments, 'courses': courses, 'selected_course': course_id}
    return render(request, 'admin/manage_assignments.html', context)


@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def add_assignment(request):
    """Add a new assignment."""
    courses = Course.objects.all()
    # Allow pre-selecting a course via query param ?course=<id>
    selected_course = request.GET.get('course')
    try:
        selected_course = int(selected_course) if selected_course else None
    except (TypeError, ValueError):
        selected_course = None
    if request.method == 'POST':
        course_id = request.POST.get('course')
        topic_id = request.POST.get('topic')
        title = request.POST.get('title')
        description = request.POST.get('description')
        due_date = request.POST.get('due_date')
        file = request.FILES.get('file')
        
        try:
            course = Course.objects.get(id=course_id)
            topic = Topic.objects.get(id=topic_id) if topic_id else None
            assignment = Assignment.objects.create(
                course=course,
                topic=topic,
                title=title,
                description=description,
                due_date=due_date,
                file=file
            )
            messages.success(request, f'Assignment "{title}" added successfully!')
            return redirect('manage_assignments')
        except Exception as e:
            logger.error(f"Error adding assignment: {str(e)}")
            messages.error(request, f'Error: {str(e)}')
    
    context = {'courses': courses, 'selected_course': selected_course}
    return render(request, 'admin/add_assignment.html', context)


@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def edit_assignment(request, assignment_id):
    """Edit an existing assignment."""
    assignment = get_object_or_404(Assignment, id=assignment_id)
    courses = Course.objects.all()
    
    if request.method == 'POST':
        assignment.course_id = request.POST.get('course')
        assignment.topic_id = request.POST.get('topic') or None
        assignment.title = request.POST.get('title')
        assignment.description = request.POST.get('description')
        assignment.due_date = request.POST.get('due_date')
        
        if request.FILES.get('file'):
            assignment.file = request.FILES.get('file')
        
        try:
            assignment.save()
            messages.success(request, 'Assignment updated successfully!')
            return redirect('manage_assignments')
        except Exception as e:
            logger.error(f"Error updating assignment: {str(e)}")
            messages.error(request, f'Error: {str(e)}')
    
    context = {'assignment': assignment, 'courses': courses}
    return render(request, 'admin/edit_assignment.html', context)


@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def delete_assignment(request, assignment_id):
    """Delete an assignment."""
    assignment = get_object_or_404(Assignment, id=assignment_id)
    assignment_title = assignment.title
    
    try:
        assignment.delete()
        messages.success(request, f'Assignment "{assignment_title}" deleted successfully!')
    except Exception as e:
        logger.error(f"Error deleting assignment: {str(e)}")
        messages.error(request, f'Error: {str(e)}')
    
    return redirect('manage_assignments')


# ===========================
# SUBMISSIONS MANAGEMENT & GRADING
# ===========================
@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def manage_submissions(request):
    """View and manage all submissions."""
    assignment_id = request.GET.get('assignment')
    reviewed_filter = request.GET.get('reviewed')
    
    submissions = Submission.objects.select_related('assignment', 'student').order_by('-submitted_at')
    
    if assignment_id:
        submissions = submissions.filter(assignment_id=assignment_id)
    
    if reviewed_filter == 'pending':
        submissions = submissions.filter(reviewed=False)
    elif reviewed_filter == 'reviewed':
        submissions = submissions.filter(reviewed=True)
    
    assignments = Assignment.objects.all()
    context = {
        'submissions': submissions,
        'assignments': assignments,
        'selected_assignment': assignment_id,
        'reviewed_filter': reviewed_filter
    }
    return render(request, 'admin/manage_submissions.html', context)


@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def grade_submission(request, submission_id):
    """Grade a student submission."""
    submission = get_object_or_404(Submission, id=submission_id)
    
    if request.method == 'POST':
        grade = request.POST.get('grade')
        feedback = request.POST.get('feedback')
        
        try:
            submission.grade = float(grade) if grade else None
            submission.feedback = feedback
            submission.reviewed = True
            submission.save()
            messages.success(request, 'Submission graded successfully!')
            return redirect('manage_submissions')
        except Exception as e:
            logger.error(f"Error grading submission: {str(e)}")
            messages.error(request, f'Error: {str(e)}')
    
    context = {'submission': submission}
    return render(request, 'admin/grade_submission.html', context)


# ===========================
# MCQ QUESTIONS MANAGEMENT
# ===========================
@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def manage_mcqs(request):
    """View and manage all MCQ questions."""
    course_id = request.GET.get('course')
    topic_id = request.GET.get('topic')
    
    mcqs = MCQQuestion.objects.select_related('course', 'topic').order_by('topic__order', 'id')
    
    if course_id:
        mcqs = mcqs.filter(course_id=course_id)
    if topic_id:
        mcqs = mcqs.filter(topic_id=topic_id)
    
    courses = Course.objects.all()
    topics = Topic.objects.all() if not course_id else Topic.objects.filter(course_id=course_id)
    
    context = {
        'mcqs': mcqs,
        'courses': courses,
        'topics': topics,
        'selected_course': course_id,
        'selected_topic': topic_id
    }
    return render(request, 'admin/manage_mcqs.html', context)


@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def add_mcq(request):
    """Add a new MCQ question."""
    courses = Course.objects.all()
    # Allow pre-selecting a course via query param ?course=<id>
    selected_course = request.GET.get('course')
    try:
        selected_course = int(selected_course) if selected_course else None
    except (TypeError, ValueError):
        selected_course = None
    if request.method == 'POST':
        course_id = request.POST.get('course')
        topic_id = request.POST.get('topic')
        question_text = request.POST.get('question_text')
        option_1 = request.POST.get('option_1')
        option_2 = request.POST.get('option_2')
        option_3 = request.POST.get('option_3')
        option_4 = request.POST.get('option_4')
        correct_option = request.POST.get('correct_option')
        image = request.FILES.get('image')
        
        try:
            course = Course.objects.get(id=course_id)
            topic = Topic.objects.get(id=topic_id) if topic_id else None
            mcq = MCQQuestion.objects.create(
                course=course,
                topic=topic,
                question_text=question_text,
                option_1=option_1,
                option_2=option_2,
                option_3=option_3,
                option_4=option_4,
                correct_option=int(correct_option),
                image=image
            )
            messages.success(request, 'MCQ question added successfully!')
            return redirect('manage_mcqs')
        except Exception as e:
            logger.error(f"Error adding MCQ: {str(e)}")
            messages.error(request, f'Error: {str(e)}')
    
    context = {'courses': courses, 'selected_course': selected_course}
    return render(request, 'admin/add_mcq.html', context)


@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def edit_mcq(request, mcq_id):
    """Edit an existing MCQ question."""
    mcq = get_object_or_404(MCQQuestion, id=mcq_id)
    courses = Course.objects.all()
    
    if request.method == 'POST':
        mcq.course_id = request.POST.get('course')
        mcq.topic_id = request.POST.get('topic') or None
        mcq.question_text = request.POST.get('question_text')
        mcq.option_1 = request.POST.get('option_1')
        mcq.option_2 = request.POST.get('option_2')
        mcq.option_3 = request.POST.get('option_3')
        mcq.option_4 = request.POST.get('option_4')
        mcq.correct_option = int(request.POST.get('correct_option'))
        
        if request.FILES.get('image'):
            mcq.image = request.FILES.get('image')
        
        try:
            mcq.save()
            messages.success(request, 'MCQ question updated successfully!')
            return redirect('manage_mcqs')
        except Exception as e:
            logger.error(f"Error updating MCQ: {str(e)}")
            messages.error(request, f'Error: {str(e)}')
    
    context = {'mcq': mcq, 'courses': courses}
    return render(request, 'admin/edit_mcq.html', context)


@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def delete_mcq(request, mcq_id):
    """Delete an MCQ question."""
    mcq = get_object_or_404(MCQQuestion, id=mcq_id)
    
    try:
        mcq.delete()
        messages.success(request, 'MCQ question deleted successfully!')
    except Exception as e:
        logger.error(f"Error deleting MCQ: {str(e)}")
        messages.error(request, f'Error: {str(e)}')
    
    return redirect('manage_mcqs')


# ===========================
# PAYMENTS MANAGEMENT
# ===========================
@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def manage_payments(request):
    """View and manage all payments."""
    student_id = request.GET.get('student')
    
    payments = Payment.objects.select_related('student').order_by('-payment_date')
    
    if student_id:
        payments = payments.filter(student_id=student_id)
    
    students = CustomUser.objects.filter(role='student')
    context = {'payments': payments, 'students': students, 'selected_student': student_id}
    return render(request, 'admin/manage_payments.html', context)


@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def add_payment(request):
    """Add a new payment record."""
    students = CustomUser.objects.filter(role='student')
    if request.method == 'POST':
        student_id = request.POST.get('student')
        amount = request.POST.get('amount')
        transaction_id = request.POST.get('transaction_id')
        
        try:
            student = CustomUser.objects.get(id=student_id)
            payment = Payment.objects.create(
                student=student,
                amount=float(amount) if amount else None,
                transaction_id=transaction_id
            )
            messages.success(request, f'Payment of ₹{amount} added for {student.name}!')
            return redirect('manage_payments')
        except Exception as e:
            logger.error(f"Error adding payment: {str(e)}")
            messages.error(request, f'Error: {str(e)}')
    
    context = {'students': students}
    return render(request, 'admin/add_payment.html', context)


@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def edit_payment(request, payment_id):
    """Edit an existing payment."""
    payment = get_object_or_404(Payment, id=payment_id)
    students = CustomUser.objects.filter(role='student')
    
    if request.method == 'POST':
        payment.student_id = request.POST.get('student')
        payment.amount = request.POST.get('amount')
        payment.transaction_id = request.POST.get('transaction_id')
        
        try:
            payment.save()
            messages.success(request, 'Payment updated successfully!')
            return redirect('manage_payments')
        except Exception as e:
            logger.error(f"Error updating payment: {str(e)}")
            messages.error(request, f'Error: {str(e)}')
    
    context = {'payment': payment, 'students': students}
    return render(request, 'admin/edit_payment.html', context)


@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def delete_payment(request, payment_id):
    """Delete a payment record."""
    payment = get_object_or_404(Payment, id=payment_id)
    
    try:
        payment.delete()
        messages.success(request, 'Payment deleted successfully!')
    except Exception as e:
        logger.error(f"Error deleting payment: {str(e)}")
        messages.error(request, f'Error: {str(e)}')
    
    return redirect('manage_payments')


# ===========================
# FINAL EXAM MANAGEMENT
# ===========================
@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def manage_exams(request):
    """View and manage all final exams."""
    exams = FinalExam.objects.select_related('course').all()
    context = {'exams': exams}
    return render(request, 'admin/manage_exams.html', context)


@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def add_exam(request):
    """Add a new final exam."""
    courses = Course.objects.all()
    if request.method == 'POST':
        course_id = request.POST.get('course')
        title = request.POST.get('title')
        num_questions = request.POST.get('num_questions')
        pass_mark = request.POST.get('pass_mark')
        
        try:
            course = Course.objects.get(id=course_id)
            exam = FinalExam.objects.create(
                course=course,
                title=title,
                num_questions=int(num_questions),
                pass_mark=int(pass_mark)
            )
            messages.success(request, f'Exam "{title}" created successfully!')
            return redirect('manage_exams')
        except Exception as e:
            logger.error(f"Error adding exam: {str(e)}")
            messages.error(request, f'Error: {str(e)}')
    
    context = {'courses': courses}
    return render(request, 'admin/add_exam.html', context)


@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def edit_exam(request, exam_id):
    """Edit an existing final exam."""
    exam = get_object_or_404(FinalExam, id=exam_id)
    courses = Course.objects.all()
    
    if request.method == 'POST':
        exam.title = request.POST.get('title')
        exam.num_questions = request.POST.get('num_questions')
        exam.pass_mark = request.POST.get('pass_mark')
        exam.active = request.POST.get('active') == 'on'
        
        try:
            exam.save()
            messages.success(request, 'Exam updated successfully!')
            return redirect('manage_exams')
        except Exception as e:
            logger.error(f"Error updating exam: {str(e)}")
            messages.error(request, f'Error: {str(e)}')
    
    context = {'exam': exam, 'courses': courses}
    return render(request, 'admin/edit_exam.html', context)


# ===========================
# EXAM QUESTIONS MANAGEMENT
# ===========================
@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def manage_exam_questions(request, exam_id):
    """Manage questions for a final exam."""
    exam = get_object_or_404(FinalExam, id=exam_id)
    questions = FinalExamQuestion.objects.filter(exam=exam)
    context = {'exam': exam, 'questions': questions}
    return render(request, 'admin/manage_exam_questions.html', context)


@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def add_exam_question(request, exam_id):
    """Add a question to a final exam."""
    exam = get_object_or_404(FinalExam, id=exam_id)
    
    if request.method == 'POST':
        question_text = request.POST.get('question_text')
        option_1 = request.POST.get('option_1')
        option_2 = request.POST.get('option_2')
        option_3 = request.POST.get('option_3')
        option_4 = request.POST.get('option_4')
        correct_option = request.POST.get('correct_option')
        image = request.FILES.get('image')
        
        try:
            question = FinalExamQuestion.objects.create(
                exam=exam,
                question_text=question_text,
                option_1=option_1,
                option_2=option_2,
                option_3=option_3,
                option_4=option_4,
                correct_option=int(correct_option),
                image=image
            )
            messages.success(request, 'Question added successfully!')
            return redirect('manage_exam_questions', exam_id=exam.id)
        except Exception as e:
            logger.error(f"Error adding exam question: {str(e)}")
            messages.error(request, f'Error: {str(e)}')
    
    context = {'exam': exam}
    return render(request, 'admin/add_exam_question.html', context)


@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def edit_exam_question(request, question_id):
    """Edit a final exam question."""
    question = get_object_or_404(FinalExamQuestion, id=question_id)
    
    if request.method == 'POST':
        question.question_text = request.POST.get('question_text')
        question.option_1 = request.POST.get('option_1')
        question.option_2 = request.POST.get('option_2')
        question.option_3 = request.POST.get('option_3')
        question.option_4 = request.POST.get('option_4')
        question.correct_option = int(request.POST.get('correct_option'))
        
        if request.FILES.get('image'):
            question.image = request.FILES.get('image')
        
        try:
            question.save()
            messages.success(request, 'Question updated successfully!')
            return redirect('manage_exam_questions', exam_id=question.exam.id)
        except Exception as e:
            logger.error(f"Error updating exam question: {str(e)}")
            messages.error(request, f'Error: {str(e)}')
    
    context = {'question': question}
    return render(request, 'admin/edit_exam_question.html', context)


@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def delete_exam_question(request, question_id):
    """Delete a final exam question."""
    question = get_object_or_404(FinalExamQuestion, id=question_id)
    exam_id = question.exam.id
    
    try:
        question.delete()
        messages.success(request, 'Question deleted successfully!')
    except Exception as e:
        logger.error(f"Error deleting exam question: {str(e)}")
        messages.error(request, f'Error: {str(e)}')
    
    return redirect('manage_exam_questions', exam_id=exam_id)
