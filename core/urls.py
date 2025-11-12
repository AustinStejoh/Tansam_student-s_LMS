from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.home_view, name='home'),
    path('login/', views.login_view, name='login'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('logout/', views.logout_view, name='logout'),
    path('all-topics/', views.all_topics_view, name='all_topics'),
    path('course/<int:course_id>/', views.course_detail_view, name='course_detail'),
    path('topic/<int:topic_id>/', views.topic_detail_view, name='topic_detail'),  # ✅ Added for Learn button
    path('course/<int:course_id>/mcq/', views.course_mcq_topics_view, name='course_mcq_topics'),
    path('course/<int:course_id>/mcq/quiz/', views.course_mcq_view, name='course_mcq'),
    path('course/<int:course_id>/mcq/result/', views.course_mcq_result_view, name='course_mcq_result'),
    path('course/<int:course_id>/final-exam/', views.final_exam_view, name='final_exam'),
    path('course/<int:course_id>/final-exam/result/', views.final_exam_result_view, name='final_exam_result'),
    path('course/<int:course_id>/certificate/', views.certificate_view, name='certificate'),
    path('course/<int:course_id>/assignments/', views.assignment_page, name='assignment_page'),
    path('course/<int:course_id>/grading-dashboard/', views.student_grading_dashboard, name='student_grading_dashboard'),
    path('topic/<int:topic_id>/mcq/start/', views.course_mcq_view, name='start_mcq_test'),
    path('topic/<int:topic_id>/assignments/', views.assignment_page, name='assignment_list'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
