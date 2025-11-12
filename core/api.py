from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Course, Topic, Progress, TopicCompletion
from .serializers import (
    CourseSerializer, TopicSerializer,
    ProgressSerializer, TopicCompletionSerializer
)

class CourseViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Course.objects.prefetch_related('topics').all()
    serializer_class = CourseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

class TopicViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Topic.objects.all()
    serializer_class = TopicSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    @action(detail=True, methods=['post'])
    def mark_completed(self, request, pk=None):
        topic = self.get_object()
        progress = Progress.objects.get_or_create(
            student=request.user,
            course=topic.course
        )[0]
        
        topic_completion, created = TopicCompletion.objects.get_or_create(
            progress=progress,
            topic=topic,
            defaults={'completed': True}
        )
        
        if not created and not topic_completion.completed:
            topic_completion.completed = True
            topic_completion.save()
        
        progress.update_progress()
        
        return Response({'status': 'success'})

class ProgressViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ProgressSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Progress.objects.filter(student=self.request.user)