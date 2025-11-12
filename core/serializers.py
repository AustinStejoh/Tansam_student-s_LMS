from rest_framework import serializers
from .models import Course, Topic, Progress, TopicCompletion

class TopicSerializer(serializers.ModelSerializer):
    video_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Topic
        fields = ['id', 'title', 'video_url', 'ppt_file', 'order']
    
    def get_video_url(self, obj):
        if obj.video_file:
            return self.context['request'].build_absolute_uri(obj.video_file.url)
        return None

class CourseSerializer(serializers.ModelSerializer):
    topics = TopicSerializer(many=True, read_only=True)
    progress = serializers.SerializerMethodField()
    
    class Meta:
        model = Course
        fields = ['id', 'title', 'description', 'class_level', 'created_at', 'topics', 'progress']
    
    def get_progress(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            progress = Progress.objects.filter(student=request.user, course=obj).first()
            if progress:
                return {
                    'overall_progress': progress.overall_progress,
                    'completed_topics': progress.completed_topics.values_list('id', flat=True)
                }
        return None

class ProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Progress
        fields = ['id', 'student', 'course', 'overall_progress']

class TopicCompletionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TopicCompletion
        fields = ['id', 'progress', 'topic', 'completed', 'assignment_score']