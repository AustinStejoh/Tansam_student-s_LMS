from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from accounts.models import CustomUser

# ------------------------------
# Course Model
# ------------------------------
class Course(models.Model):
    """
    Represents a course with title, description, and class level.
    """
    CLASS_LEVELS = (
        ('6-8', 'Classes 6–8'),
        ('9-12', 'Classes 9–12'),
    )

    title = models.CharField(max_length=200)
    description = models.TextField()
    class_level = models.CharField(max_length=5, choices=CLASS_LEVELS)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


# ------------------------------
# Topic Model
# ------------------------------
class Topic(models.Model):
    """
    Represents a topic within a course.
    Each topic can have video and PPT files as study materials.
    """
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='topics')
    title = models.CharField(max_length=200)
    video_file = models.FileField(upload_to='topic_videos/', blank=True, null=True)
    ppt_file = models.FileField(upload_to='topic_ppts/', blank=True, null=True)
    order = models.PositiveIntegerField()
    assignment = models.JSONField(null=True, blank=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.course.title} - {self.title}"


# ------------------------------
# Progress Model
# ------------------------------
class Progress(models.Model):
    """
    Tracks a student's progress in a specific course.
    """
    student = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'student'},
        related_name='progress_records'
    )

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='progress_records'
    )

    completed_topics = models.ManyToManyField('Topic', through='TopicCompletion')
    overall_progress = models.FloatField(default=0.0)

    def update_progress(self):
        """
        Updates the student's overall course progress as a percentage.
        """
        total_topics = self.course.topics.count()
        if total_topics > 0:
            completed_count = self.topiccompletion_set.filter(completed=True).count()
            self.overall_progress = (completed_count / total_topics) * 100
        else:
            self.overall_progress = 0.0

        self.save()

    def __str__(self):
        return f"{self.student.name} - {self.course.title}"


# ------------------------------
# TopicCompletion Model
# ------------------------------
class TopicCompletion(models.Model):
    """
    Tracks whether a topic has been completed by a student.
    """
    progress = models.ForeignKey(Progress, on_delete=models.CASCADE)
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)
    assignment_score = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"{self.progress.student.name} - {self.topic.title}"


# ------------------------------
# Payment Model
# ------------------------------
class Payment(models.Model):
    """
    Records payments made by students.
    """
    student = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'student'},
        related_name='payments'
    )

    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    payment_date = models.DateTimeField(auto_now_add=True)
    transaction_id = models.CharField(max_length=100, unique=True, null=True, blank=True)

    def clean(self):
        if self.amount is not None and self.amount <= 0:
            raise ValidationError("Amount must be greater than zero.")
        if self.amount is None and self.transaction_id:
            raise ValidationError("Amount is required when providing a transaction ID.")

    def save(self, *args, **kwargs):
        self.clean()  # Validate before saving
        super().save(*args, **kwargs)

        # Automatically mark payment_status = True if payment is valid
        if self.student and self.amount and self.amount > 0 and not getattr(self.student, 'payment_status', False):
            self.student.payment_status = True
            self.student.save(update_fields=['payment_status'])

    def __str__(self):
        return f"{self.student.name} - ₹{self.amount or 'No Amount'}"
