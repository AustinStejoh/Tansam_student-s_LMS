from django.db import models
from django.utils import timezone
from .models import Topic
from accounts.models import CustomUser

class Assignment(models.Model):
    """
    Represents an assignment that can be created by admin and submitted by students
    """
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='assignments')
    title = models.CharField(max_length=200)
    description = models.TextField()
    file_attachment = models.FileField(upload_to='assignments/', blank=True, null=True)
    due_date = models.DateTimeField()
    max_score = models.FloatField(default=100.0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.topic.title} - {self.title}"

    @property
    def is_past_due(self):
        return timezone.now() > self.due_date

class AssignmentSubmission(models.Model):
    """
    Represents a student's submission for an assignment
    """
    STATUS_CHOICES = [
        ('submitted', 'Submitted'),
        ('graded', 'Graded'),
        ('returned', 'Returned for revision')
    ]

    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'student'},
        related_name='assignment_submissions'
    )
    submission_file = models.FileField(upload_to='assignment_submissions/')
    submitted_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='submitted')
    score = models.FloatField(null=True, blank=True)
    feedback = models.TextField(blank=True)

    class Meta:
        unique_together = ['assignment', 'student']

    def __str__(self):
        return f"{self.student.name} - {self.assignment.title}"

    @property
    def is_late(self):
        return self.submitted_at > self.assignment.due_date