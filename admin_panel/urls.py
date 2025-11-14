from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.admin_login_view, name='admin_login'),
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('logout/', views.admin_logout_view, name='admin_logout'),
    
    # Students Management
    path('students/', views.manage_students, name='manage_students'),
    path('students/add/', views.add_student, name='add_student'),
    path('students/<int:student_id>/performance/', views.student_performance, name='student_performance'),
    
    # Courses Management
    path('courses/', views.manage_courses, name='manage_courses'),
    path('courses/add/', views.add_course, name='add_course'),
    path('courses/<int:course_id>/edit/', views.edit_course, name='edit_course'),
    path('courses/<int:course_id>/delete/', views.delete_course, name='delete_course'),
    
    # Topics Management
    path('topics/', views.manage_topics, name='manage_topics'),
    path('topics/add/', views.add_topic, name='add_topic'),
    path('topics/<int:topic_id>/edit/', views.edit_topic, name='edit_topic'),
    path('topics/<int:topic_id>/delete/', views.delete_topic, name='delete_topic'),
    # Ajax endpoints
    path('api/topics/', views.api_topics, name='api_topics'),
    
    # Assignments Management
    path('assignments/', views.manage_assignments, name='manage_assignments'),
    path('assignments/add/', views.add_assignment, name='add_assignment'),
    path('assignments/<int:assignment_id>/edit/', views.edit_assignment, name='edit_assignment'),
    path('assignments/<int:assignment_id>/delete/', views.delete_assignment, name='delete_assignment'),
    
    # Submissions & Grading
    path('submissions/', views.manage_submissions, name='manage_submissions'),
    path('submissions/<int:submission_id>/grade/', views.grade_submission, name='grade_submission'),
    
    # MCQ Questions Management
    path('mcqs/', views.manage_mcqs, name='manage_mcqs'),
    path('mcqs/add/', views.add_mcq, name='add_mcq'),
    path('mcqs/<int:mcq_id>/edit/', views.edit_mcq, name='edit_mcq'),
    path('mcqs/<int:mcq_id>/delete/', views.delete_mcq, name='delete_mcq'),
    
    # Payments Management
    path('payments/', views.manage_payments, name='manage_payments'),
    path('payments/add/', views.add_payment, name='add_payment'),
    path('payments/<int:payment_id>/edit/', views.edit_payment, name='edit_payment'),
    path('payments/<int:payment_id>/delete/', views.delete_payment, name='delete_payment'),
    
    # Final Exams Management
    path('exams/', views.manage_exams, name='manage_exams'),
    path('exams/add/', views.add_exam, name='add_exam'),
    path('exams/<int:exam_id>/edit/', views.edit_exam, name='edit_exam'),
    path('exams/<int:exam_id>/questions/', views.manage_exam_questions, name='manage_exam_questions'),
    path('exams/<int:exam_id>/questions/add/', views.add_exam_question, name='add_exam_question'),
    path('exam-questions/<int:question_id>/edit/', views.edit_exam_question, name='edit_exam_question'),
    path('exam-questions/<int:question_id>/delete/', views.delete_exam_question, name='delete_exam_question'),
]
