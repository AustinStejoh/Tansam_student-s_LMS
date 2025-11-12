from django.contrib import admin
from .models import Course, Topic, Progress, TopicCompletion, Payment, Assignment, Submission, FinalExam, FinalExamQuestion, FinalExamSubmission
from .admin_views import grading_dashboard_view
from django.urls import path
from django.utils.html import format_html 

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'class_level', 'created_at')
    list_filter = ('class_level',)
    search_fields = ('title', 'description')

@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'topic', 'due_date', 'created_at')
    list_filter = ('course', 'topic', 'due_date')
    search_fields = ('title', 'course__title', 'topic__title')

@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('assignment', 'student', 'submitted_at', 'is_late', 'grade', 'reviewed')
    list_filter = ('assignment__course', 'submitted_at', 'reviewed')
    search_fields = ('student__username', 'assignment__title')
    list_editable = ('grade', 'reviewed')

    actions = ['mark_as_reviewed']

    @admin.action(description="Mark selected submissions as reviewed")
    def mark_as_reviewed(self, request, queryset):
        updated = queryset.update(reviewed=True)
        self.message_user(request, f"{updated} submissions marked as reviewed ✅")


    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('grading-dashboard/', self.admin_site.admin_view(grading_dashboard_view),
                 name='grading-dashboard'),
        ]
        return custom_urls + urls

    def grading_dashboard_link(self, obj):
        return format_html('<a href="/admin/grading-dashboard/"> Go to  Dashboard</a>')

@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'order', 'video_file', 'poster_image', 'ppt_file')
    list_filter = ('course',)
    search_fields = ('title',)
    # Enable file uploads in the admin
    fields = (
        'course', 'title', 'order',
        'video_file', 'poster_image',
        'caption_en_file', 'caption_ta_file', 'chapters_file',
        'ppt_file', 'assignment'
    )

@admin.register(Progress)
class ProgressAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'overall_progress')
    list_filter = ('course', 'student__class_level')
    search_fields = ('student__name',)

@admin.register(TopicCompletion)
class TopicCompletionAdmin(admin.ModelAdmin):
    list_display = ('progress', 'topic', 'completed', 'assignment_score')
    list_filter = ('completed', 'progress__course')
    search_fields = ('progress__student__name', 'topic__title')
from .models import MCQQuestion

@admin.register(MCQQuestion)
class MCQQuestionAdmin(admin.ModelAdmin):
    list_display = ('question_text', 'course', 'topic', 'correct_option')
    list_filter = ('course', 'topic')
    search_fields = ('question_text', 'course__title', 'topic__title')
    fields = ('course', 'topic', 'question_text', 'image', 'option_1', 'option_2', 'option_3', 'option_4', 'correct_option')
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('course', 'topic')

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('student', 'amount', 'payment_date', 'transaction_id')
    list_filter = ('payment_date', 'student__class_level')
    search_fields = ('student__name', 'transaction_id')


@admin.register(FinalExam)
class FinalExamAdmin(admin.ModelAdmin):
    list_display = ('course', 'title', 'num_questions', 'pass_mark', 'active')
    list_filter = ('active',)


@admin.register(FinalExamQuestion)
class FinalExamQuestionAdmin(admin.ModelAdmin):
    list_display = ('exam', 'question_text')
    search_fields = ('question_text',)


@admin.register(FinalExamSubmission)
class FinalExamSubmissionAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'score', 'passed', 'submitted_at')
    list_filter = ('passed', 'submitted_at')