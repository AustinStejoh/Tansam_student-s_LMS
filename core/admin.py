from django.contrib import admin
from .models import Course, Topic, Progress, TopicCompletion, Payment

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['title', 'class_level', 'created_at']
    list_filter = ['class_level']

@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'order']
    list_filter = ['course']

@admin.register(Progress)
class ProgressAdmin(admin.ModelAdmin):
    list_display = ['student', 'course', 'overall_progress']
    list_filter = ['course']

@admin.register(TopicCompletion)
class TopicCompletionAdmin(admin.ModelAdmin):
    list_display = ['progress', 'topic', 'completed', 'assignment_score']

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['student', 'amount', 'payment_date', 'transaction_id']