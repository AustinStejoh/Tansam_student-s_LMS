from django.contrib import admin
from .models import Course, Topic, Progress, TopicCompletion, Payment

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'class_level', 'created_at')
    list_filter = ('class_level',)
    search_fields = ('title', 'description')

@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'order', 'video_file', 'ppt_file')
    list_filter = ('course',)
    search_fields = ('title',)
    # Enable file uploads in the admin
    fields = ('course', 'title', 'video_file', 'ppt_file', 'order', 'assignment')

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

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('student', 'amount', 'payment_date', 'transaction_id')
    list_filter = ('payment_date', 'student__class_level')
    search_fields = ('student__name', 'transaction_id')