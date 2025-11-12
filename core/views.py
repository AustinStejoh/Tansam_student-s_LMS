from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import login, logout, get_user_model
from django.urls import reverse
from django.utils import timezone
from django.db.models import Avg, Count, Q
from .models import Progress, Course, Topic, TopicCompletion, Assignment, Submission, MCQQuestion, FinalExam, FinalExamQuestion, FinalExamSubmission

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

#------------------- ASSIGNMENT VIEW -------------------
def assignment_page(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    topic_id = request.GET.get('topic')
    assignments = Assignment.objects.filter(course=course).order_by('-created_at')
    if topic_id:
        assignments = assignments.filter(topic_id=topic_id)

    if request.method == 'POST' and request.user.is_authenticated:
        assignment_id = request.POST.get('assignment_id')
        uploaded_file = request.FILES.get('submitted_file')
        if assignment_id and uploaded_file:
            assignment = get_object_or_404(Assignment, id=assignment_id, course=course)
            Submission.objects.create(
                assignment=assignment,
                student=request.user,
                submitted_file=uploaded_file,
            )
            # Track assignment submission for topic completion
            if assignment.topic:
                progress = Progress.objects.filter(student=request.user, course=course).first()
                if progress:
                    completion, _ = TopicCompletion.objects.get_or_create(
                        progress=progress,
                        topic=assignment.topic,
                        defaults={'completed': False}
                    )
                    if not completion.assignment_submitted:
                        completion.assignment_submitted = True
                        completion.assignment_submitted_at = timezone.now()
                        completion.save()
                        completion.check_completion()
            return redirect('student_grading_dashboard', course_id=course.id)

    return render(request, 'assignments/assignment_page.html', {
        'assignments': assignments,
        'course': course,
        'topic_id': topic_id,
    })


@login_required
def student_grading_dashboard(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    submissions = Submission.objects.filter(student=request.user, assignment__course=course).select_related('assignment').order_by('-submitted_at')
    return render(request, 'grading_dashboard.html', {
        'course': course,
        'submissions': submissions,
    })
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
        if progress_record:
            progress_record.update_progress()  # Ensure progress is up to date
            progress_value = progress_record.overall_progress
        else:
            progress_value = 0
        course_progress.append({
            'course': course,
            'progress': progress_value,
            'overall_progress': progress_value,  # For template compatibility
            'topics': getattr(course, 'topics', []).all() if hasattr(course, 'topics') else [],
        })

    # Calculate overall progress across all enrolled courses
    enrolled_course_progress = [cp for cp in course_progress if cp['progress'] > 0]
    if enrolled_course_progress:
        total_progress = sum(cp['progress'] for cp in enrolled_course_progress)
        overall_progress = total_progress / len(enrolled_course_progress)
    else:
        overall_progress = 0

    # Find completed topics
    student_progress_ids = progress_records.values_list('id', flat=True)
    topic_completions = TopicCompletion.objects.filter(progress_id__in=student_progress_ids).select_related('topic')
    completed_topic_ids = {tc.topic_id for tc in topic_completions if tc.completed}

    # Calculate assignment statistics
    enrolled_courses = [pr.course for pr in progress_records]
    all_submissions = Submission.objects.filter(student=user).select_related('assignment')
    total_assignments = Assignment.objects.filter(course__in=enrolled_courses).count()
    submitted_count = all_submissions.count()
    assignment_submission_rate = (submitted_count / total_assignments * 100) if total_assignments > 0 else 0
    
    # Calculate average grade
    graded_submissions = all_submissions.exclude(grade__isnull=True)
    avg_grade = graded_submissions.aggregate(avg=Avg('grade'))['avg'] or 0

    context = {
        'user': user,
        'progress_records': progress_records,
        'courses': courses,
        'course_progress': course_progress,
        'overall_progress': round(overall_progress, 1),
        'completed_topic_ids': completed_topic_ids,
        'assignment_submission_rate': round(assignment_submission_rate, 1),
        'avg_grade': round(float(avg_grade), 1),
        'submitted_count': submitted_count,
        'total_assignments': total_assignments,
        'notifications': 1,
    }
    return render(request, 'dashboard.html', context)


# ------------------- MCQ TOPICS SELECTION VIEW -------------------
@login_required
def course_mcq_topics_view(request, course_id):
    """
    Displays all topics for a course that have MCQs, allowing student to select which topic's quiz to take.
    """
    course = get_object_or_404(Course, id=course_id)
    topics = Topic.objects.filter(course=course).order_by('order')
    
    # Get topics with their MCQ counts
    topics_with_mcqs = []
    for topic in topics:
        mcq_count = MCQQuestion.objects.filter(course=course, topic=topic).count()
        if mcq_count > 0:
            topics_with_mcqs.append({
                'topic': topic,
                'mcq_count': mcq_count,
            })
    
    # Check if course has course-level MCQs (no topic assigned)
    course_level_mcq_count = MCQQuestion.objects.filter(course=course, topic__isnull=True).count()

    # Determine topics whose videos are watched (unlock condition)
    watched_topic_ids = set()
    if request.user.is_authenticated:
        progress = Progress.objects.filter(student=request.user, course=course).first()
        if progress:
            watched_topic_ids = set(
                TopicCompletion.objects.filter(progress=progress, video_watched=True)
                .values_list('topic_id', flat=True)
            )
    
    context = {
        'course': course,
        'topics_with_mcqs': topics_with_mcqs,
        'course_level_mcq_count': course_level_mcq_count,
        'watched_topic_ids': watched_topic_ids,
    }
    return render(request, 'mcq_topics.html', context)


# ------------------- COURSE MCQ VIEW -------------------
@login_required
def course_mcq_view(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    topic_id = request.GET.get('topic')
    topic = None
    
    # Filter MCQs: if topic_id provided, show topic-specific; otherwise show course-level
    mcqs_query = MCQQuestion.objects.filter(course=course)
    if topic_id:
        topic = get_object_or_404(Topic, id=topic_id, course=course)
        mcqs_query = mcqs_query.filter(topic=topic)
    else:
        # Show only course-level MCQs (no topic assigned)
        mcqs_query = mcqs_query.filter(topic__isnull=True)
    
    mcqs = mcqs_query[:10]
    
    if request.method == 'POST':
        submitted = [int(request.POST.get(f'q{i}', 0)) for i in range(len(mcqs))]
        corrects = [int(mcq.correct_option) for mcq in mcqs]
        score = sum([a == b and a != 0 for a, b in zip(submitted, corrects)])
        passed = score >= 7

        # Store minimal result data in session (POST -> Redirect -> GET)
        result_payload = {
            'question_ids': [q.id for q in mcqs],
            'selected': submitted,
            'corrects': corrects,
            'score': score,
            'passed': passed,
            'topic_id': topic_id,  # Store topic_id for result page
        }
        request.session[f'mcq_result_{course_id}'] = result_payload
        return redirect('course_mcq_result', course_id=course_id)

    return render(request, 'mcq.html', {
        'course': course,
        'topic': topic,
        'mcqs': mcqs,
    })
    
    context = {
        'questions': mcqs,
        'course': course,
        'topic': topic,
    }
    return render(request, 'mcq.html', context)


@login_required
def course_mcq_result_view(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    key = f'mcq_result_{course_id}'
    payload = request.session.get(key)
    if not payload:
        return redirect('course_mcq', course_id=course_id)

    # Fetch questions in the same order
    questions = list(MCQQuestion.objects.filter(id__in=payload['question_ids']))
    # Preserve original order
    id_to_q = {q.id: q for q in questions}
    ordered_questions = [id_to_q[qid] for qid in payload['question_ids'] if qid in id_to_q]

    details = []
    for idx, q in enumerate(ordered_questions):
        selected = payload['selected'][idx] if idx < len(payload['selected']) else 0
        correct = payload['corrects'][idx] if idx < len(payload['corrects']) else 0
        details.append({
            'q': q,
            'index': idx + 1,
            'selected': selected,
            'correct': correct,
            'is_correct': (selected == correct and selected != 0),
        })

    score = int(payload['score'])
    percent = int((score / max(len(ordered_questions), 1)) * 100)
    passed = bool(payload['passed'])
    
    # Track MCQ completion if topic-specific MCQ was passed
    topic_id = payload.get('topic_id')
    if topic_id and passed:
        topic = Topic.objects.filter(id=topic_id, course=course).first()
        if topic:
            progress = Progress.objects.filter(student=request.user, course=course).first()
            if progress:
                completion, _ = TopicCompletion.objects.get_or_create(
                    progress=progress,
                    topic=topic,
                    defaults={'completed': False}
                )
                if not completion.mcq_passed:
                    completion.mcq_passed = True
                    completion.mcq_passed_at = timezone.now()
                    completion.save()
                    completion.check_completion()

    context = {
        'course': course,
        'details': details,
        'score_percent': percent,
        'correct_count': score,
        'total_count': len(ordered_questions),
        'passed': passed,
    }
    # Optionally clear session key after showing
    # del request.session[key]
    return render(request, 'mcq_result.html', context)


# ------------------- FINAL EXAM VIEWS -------------------
@login_required
def final_exam_view(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    progress = Progress.objects.filter(student=request.user, course=course).first()
    if not progress:
        messages.error(request, 'You are not enrolled in this course.')
        return redirect('dashboard')

    # Ensure all topics completed
    total_topics = course.topics.count()
    completed_count = TopicCompletion.objects.filter(progress=progress, completed=True).count()
    if total_topics == 0 or completed_count < total_topics:
        messages.warning(request, 'Complete all chapters to unlock the Final Exam.')
        return redirect('course_detail', course_id=course.id)

    exam = FinalExam.objects.filter(course=course, active=True).first()
    if not exam:
        # Create a basic exam placeholder if not present
        exam = FinalExam.objects.create(course=course)

    questions_qs = exam.questions.all()[:exam.num_questions]
    questions = list(questions_qs)

    if request.method == 'POST':
        submitted = [int(request.POST.get(f'q{i}', 0)) for i in range(len(questions))]
        corrects = [int(q.correct_option) for q in questions]
        score = int(sum([a == b and a != 0 for a, b in zip(submitted, corrects)]) / max(len(questions), 1) * 100)
        passed = score >= exam.pass_mark

        # Save submission
        submission = FinalExamSubmission.objects.create(
            student=request.user,
            course=course,
            score=score,
            passed=passed,
            details={
                'question_ids': [q.id for q in questions],
                'selected': submitted,
                'corrects': corrects,
            }
        )

        # Update progress and certificate
        progress.final_exam_score = score
        progress.final_exam_passed = passed
        if passed and not progress.certificate_issued_at:
            progress.certificate_issued_at = timezone.now()
        progress.save()

        return redirect('final_exam_result', course_id=course.id)

    return render(request, 'final_exam.html', {
        'course': course,
        'exam': exam,
        'questions': questions,
    })


@login_required
def final_exam_result_view(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    progress = Progress.objects.filter(student=request.user, course=course).first()
    last_submission = FinalExamSubmission.objects.filter(student=request.user, course=course).first()
    return render(request, 'final_exam_result.html', {
        'course': course,
        'progress': progress,
        'submission': last_submission,
    })


@login_required
def certificate_view(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    progress = Progress.objects.filter(student=request.user, course=course).first()
    if not progress or not progress.final_exam_passed:
        messages.error(request, 'Certificate is available only after passing the final exam.')
        return redirect('course_detail', course_id=course.id)

    return render(request, 'certificate.html', {
        'course': course,
        'progress': progress,
        'student': request.user,
    })
def course_detail_view(request, course_id):
    """
    Displays detailed information about a selected course,
    including its topics, completion status, and progress percentage.
    """
    user = request.user
    course = get_object_or_404(Course, id=course_id)
    topics = Topic.objects.filter(course=course)

    # Get or create student's progress record
    progress, _ = Progress.objects.get_or_create(student=user, course=course)

    # Fetch topic completion records with all status
    topic_completions = {}
    unlocked_topics = set()
    if progress:
        completions = TopicCompletion.objects.filter(progress=progress).select_related('topic')
        for tc in completions:
            topic_completions[tc.topic_id] = tc
            if tc.completed:
                unlocked_topics.add(tc.topic_id)
        
        # Always unlock first topic
        first_topic = topics.order_by('order').first()
        if first_topic:
            unlocked_topics.add(first_topic.id)
        
        # Unlock next topic if previous topic's video is watched (not full completion)
        for topic in topics.order_by('order'):
            if topic.order == 1:
                unlocked_topics.add(topic.id)
            else:
                prev_topic = topics.filter(order=topic.order - 1).first()
                if prev_topic and prev_topic.id in unlocked_topics:
                    prev_completion = topic_completions.get(prev_topic.id)
                    # Unlock next topic if previous video is watched
                    if prev_completion and prev_completion.video_watched:
                        unlocked_topics.add(topic.id)

    # Calculate real progress percentage based on videos watched
    total_topics = topics.count()
    if progress:
        progress.update_progress()  # Updates based on videos watched
        course_progress_percent = progress.overall_progress
    else:
        course_progress_percent = 0

    # Handle video watching tracking (when video is played for 30+ seconds)
    video_watched_param = request.GET.get('video_watched')
    if video_watched_param == 'true':
        selected_topic_id = request.GET.get('topic')
        if selected_topic_id:
            try:
                watched_topic = topics.get(id=selected_topic_id)
                if watched_topic.video_file:
                    completion, _ = TopicCompletion.objects.get_or_create(
                        progress=progress,
                        topic=watched_topic,
                        defaults={'completed': False}
                    )
                    if not completion.video_watched:
                        completion.video_watched = True
                        completion.video_watched_at = timezone.now()
                        completion.save()
                        completion.check_completion()
                        # Update progress immediately
                        progress.update_progress()
                        # Recalculate unlocked topics after video is watched
                        topic_completions[watched_topic.id] = completion
                        # Unlock next topic if this one's video is watched
                        next_topic = topics.filter(order=watched_topic.order + 1).first()
                        if next_topic:
                            unlocked_topics.add(next_topic.id)
            except Topic.DoesNotExist:
                pass

    # Determine selected topic for video playback (via query param ?topic=<id>)
    selected_topic = None
    selected_topic_id = request.GET.get('topic')
    if selected_topic_id:
        try:
            selected_topic = topics.get(id=selected_topic_id)
        except Topic.DoesNotExist:
            selected_topic = None
    else:
        # Default to first unlocked topic
        first_unlocked = topics.filter(id__in=unlocked_topics).order_by('order').first()
        selected_topic = first_unlocked if first_unlocked else topics.first()

    # Check which topics have MCQs (provide as list of IDs for template)
    topic_ids_with_mcqs = [t.id for t in topics if MCQQuestion.objects.filter(topic=t).exists()]
    
    # Check if course has any MCQs (course-level or topic-level)
    has_mcqs = MCQQuestion.objects.filter(course=course).exists()
    
    # Check if selected topic has MCQs
    has_topic_mcqs = False
    if selected_topic:
        has_topic_mcqs = MCQQuestion.objects.filter(topic=selected_topic).exists()
    
    # Prepare topics with completion info for template
    topics_with_completion = []
    for topic in topics.order_by('order'):
        completion = topic_completions.get(topic.id)
        topics_with_completion.append({
            'topic': topic,
            'completion': completion,
            'is_unlocked': topic.id in unlocked_topics,
            'is_completed': completion.completed if completion else False,
        })

    # Determine if final exam is unlocked (all topics completed)
    all_completed = False
    total_topics = topics.count()
    completed_count = len([tc for tc in topic_completions.values() if tc.completed])
    if total_topics > 0 and completed_count == total_topics:
        all_completed = True

    # Get or create exam object lazily (optional in admin too)
    final_exam = FinalExam.objects.filter(course=course, active=True).first()

    context = {
        'course': course,
        'topics': topics,
        'topics_with_completion': topics_with_completion,
        'progress': progress,
        'completed_topics': {tc.topic_id for tc in topic_completions.values() if tc.completed},
        'unlocked_topics': unlocked_topics,
        'course_progress_percent': round(course_progress_percent, 1),
        'selected_topic': selected_topic,
        'selected_completion': topic_completions.get(selected_topic.id) if selected_topic else None,
        'has_mcqs': has_mcqs,
        'has_topic_mcqs': has_topic_mcqs,
        'topic_ids_with_mcqs': topic_ids_with_mcqs,
        'all_topics_completed': all_completed,
        'final_exam': final_exam,
    }
    return render(request, 'course_detail.html', context)


# ------------------- ALL TOPICS VIEW -------------------
@login_required
def all_topics_view(request):
    """
    Displays all courses from backend with their topics in an organized view.
    Shows progress/completion if student has enrolled.
    """
    user = request.user
    
    # Get all courses from backend
    all_courses = Course.objects.all()
    
    # Get all topics for all courses with completion status
    course_topics_data = []
    for course in all_courses:
        topics = Topic.objects.filter(course=course).order_by('order')
        progress = Progress.objects.filter(student=user, course=course).first()
        
        # Get completed topic IDs if progress exists
        completed_topics = set()
        if progress:
            completed_topics = set(
                TopicCompletion.objects.filter(progress=progress, completed=True)
                .values_list('topic_id', flat=True)
            )
        
        # Calculate course progress (0 if no progress record)
        total_topics = topics.count()
        completed_count = len(completed_topics)
        course_progress = (completed_count / total_topics) * 100 if total_topics > 0 else 0
        
        # Check if student is enrolled (has progress record)
        is_enrolled = progress is not None
        
        course_topics_data.append({
            'course': course,
            'topics': topics,
            'completed_topics': completed_topics,
            'progress': round(course_progress, 1),
            'completed_count': completed_count,
            'total_count': total_topics,
            'is_enrolled': is_enrolled,
        })
    
    context = {
        'course_topics_data': course_topics_data,
        'user': user,
    }
    return render(request, 'all_topics.html', context)


# ------------------- TOPIC DETAIL VIEW -------------------
@login_required
def topic_detail_view(request, topic_id):
    """
    Displays full study content and assignment for a single topic.
    Tracks video viewing when video is played.
    """
    topic = get_object_or_404(Topic, id=topic_id)
    course = topic.course
    user = request.user

    # Ensure only enrolled students can access
    progress = Progress.objects.filter(student=user, course=course).first()
    if not progress:
        messages.warning(request, "You are not enrolled in this course.")
        return redirect('dashboard')

    # Check sequential unlocking - ensure previous topic's video is watched
    if topic.order > 1:
        prev_topic = Topic.objects.filter(course=course, order=topic.order - 1).first()
        if prev_topic:
            prev_completion = TopicCompletion.objects.filter(progress=progress, topic=prev_topic).first()
            if not prev_completion or not prev_completion.video_watched:
                messages.warning(request, f"Please watch the video for '{prev_topic.title}' before accessing this topic.")
                return redirect('course_detail', course_id=course.id)

    # Get or create topic completion record
    completion, created = TopicCompletion.objects.get_or_create(
        progress=progress, 
        topic=topic,
        defaults={'completed': False}
    )

    # Track video viewing if video is played (via AJAX or query param)
    if request.GET.get('video_watched') == 'true' and topic.video_file:
        if not completion.video_watched:
            completion.video_watched = True
            completion.video_watched_at = timezone.now()
            completion.save()
            completion.check_completion()
            # Update progress immediately
            progress.update_progress()

    context = {
        'topic': topic,
        'course': course,
        'progress': progress,
        'completion': completion,
    }
    return render(request, 'topic_detail.html', context)
