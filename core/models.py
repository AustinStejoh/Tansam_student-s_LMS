from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from accounts.models import CustomUser

# Define Course model
class Course(models.Model):
    """
    Model representing a course with a title, description, and class level.
    """
    CLASS_LEVELS = (
        ('6-8', 'Classes 6-8'),
        ('9-12', 'Classes 9-12'),
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    class_level = models.CharField(max_length=5, choices=CLASS_LEVELS)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

# Define Topic model
class Topic(models.Model):
    """
    Model representing a topic within a course, with content and order.
    """
    course = models.ForeignKey('Course', on_delete=models.CASCADE, related_name='topics')
    title = models.CharField(max_length=200)
    content = models.TextField()
    order = models.PositiveIntegerField()
    assignment = models.JSONField(null=True, blank=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.course.title} - {self.title}"

# Define Progress model
class Progress(models.Model):
    """
    Model tracking a student's progress in a course, including completed topics.
    """
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE, limit_choices_to={'role': 'student'}, related_name='progress_records')
    
    # --- CHANGED THIS FIELD ---
    course = models.ForeignKey(
        Course, 
        on_delete=models.CASCADE,
        null=False,  # Removed null=True to ensure a course is always assigned
        blank=False  # Removed blank=True to enforce course selection
    )
    
    completed_topics = models.ManyToManyField('Topic', through='TopicCompletion')
    overall_progress = models.FloatField(default=0.0)

    def update_progress(self):
        """
        Updates the overall_progress based on completed topics.
        """
        total_topics = self.course.topics.count()
        if total_topics == 0:
            self.overall_progress = 0
        else:
            completed_count = self.topiccompletion_set.filter(completed=True).count()
            self.overall_progress = (completed_count / total_topics * 100) if total_topics > 0 else 0.0
        
        self.save()

    def __str__(self):
        course_title = self.course.title if self.course else "No Course Assigned"
        return f"{self.student.name} - {course_title}"

# Define TopicCompletion model
class TopicCompletion(models.Model):
    """
    Model tracking completion status of a topic for a student's progress.
    """
    progress = models.ForeignKey('Progress', on_delete=models.CASCADE)
    
    # --- CHANGED THIS FIELD ---
    topic = models.ForeignKey(
        'Topic', 
        on_delete=models.CASCADE,
        null=False,  # Removed null=True to ensure a topic is always assigned
        blank=False  # Removed blank=True to enforce topic selection
    )
    
    completed = models.BooleanField(default=False)
    assignment_score = models.FloatField(null=True, blank=True)

    def __str__(self):
        topic_title = self.topic.title if self.topic else "No Topic Assigned"
        return f"{self.progress.student.name} - {topic_title}"

# Define Payment model
class Payment(models.Model):
    """
    Model representing a payment made by a student.
    """
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE, limit_choices_to={'role': 'student'}, related_name='payments')
    
    amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        null=True,  # Allow database NULL
        blank=True  # Allow admin to be blank
    )
    payment_date = models.DateTimeField(auto_now_add=True)
    
    transaction_id = models.CharField(
        max_length=100, 
        unique=True,
        null=True,  # Allow database NULL
        blank=True  # Allow admin to be blank
    )

    def clean(self):
        # --- UPDATED THIS LOGIC ---
        if self.amount is not None and self.amount <= 0:
            raise ValidationError("Amount must be greater than zero.")
        if self.amount is None and self.transaction_id:  # Require amount if transaction_id is provided
            raise ValidationError("Amount is required when providing a transaction ID.")

    def save(self, *args, **kwargs):
        self.clean()  # Validate before saving
        super().save(*args, **kwargs)
        
        # Update payment_status only if amount is provided and payment_status is False
        if self.student and self.amount is not None and self.amount > 0 and not self.student.payment_status:
            self.student.payment_status = True
            self.student.save()

    def __str__(self):
        return f"{self.student.name} - {self.amount or 'No Amount'}"