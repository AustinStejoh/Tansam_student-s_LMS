from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.urls import reverse
from django.http import JsonResponse
from core.models import Course, Topic
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
