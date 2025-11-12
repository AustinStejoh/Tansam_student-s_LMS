from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from accounts.models import CustomUser
from django.contrib.auth.models import User  # kept for backward compat but we use CustomUser


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
class Assignment(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='assignments')
    topic = models.ForeignKey('Topic', on_delete=models.CASCADE, related_name='assignments', null=True, blank=True, help_text='Optional: attach assignment to specific topic')
    title = models.CharField(max_length=200)
    description = models.TextField()
    file = models.FileField(upload_to='assignments/files/', null=True, blank=True)
    due_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title}-{self.course.title}"
class Submission(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    submitted_file = models.FileField(upload_to='assignments/submissions/')
    submitted_at = models.DateTimeField(auto_now_add=True)
    grade = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    feedback = models.TextField(blank=True, null=True)
    reviewed = models.BooleanField(default=False)

    def is_late(self):
        return self.submitted_at > self.assignment.due_date
    is_late.boolean = True

    def __str__(self):
        student_name = getattr(self.student, 'name', str(self.student))
        return f"{student_name} - {self.assignment.title}"

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
    poster_image = models.ImageField(upload_to='topic_posters/', blank=True, null=True, help_text='Optional poster/thumbnail')
    caption_en_file = models.FileField(upload_to='topic_captions/', blank=True, null=True, help_text='English captions (.vtt)')
    caption_ta_file = models.FileField(upload_to='topic_captions/', blank=True, null=True, help_text='Tamil captions (.vtt)')
    chapters_file = models.FileField(upload_to='topic_chapters/', blank=True, null=True, help_text='Upload WebVTT (.vtt) chapters')
    ppt_file = models.FileField(upload_to='topic_ppts/', blank=True, null=True)
    order = models.PositiveIntegerField()
    assignment = models.JSONField(null=True, blank=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.course.title} - {self.title}"

    def clean(self):
        # Basic filetype validation for admin uploads
        import os
        def has_ext(f, exts):
            return f and os.path.splitext(f.name)[1].lower() in exts

        if self.caption_en_file and not has_ext(self.caption_en_file, {'.vtt'}):
            from django.core.exceptions import ValidationError
            raise ValidationError({'caption_en_file': 'Captions must be WebVTT (.vtt).'})
        if self.caption_ta_file and not has_ext(self.caption_ta_file, {'.vtt'}):
            from django.core.exceptions import ValidationError
            raise ValidationError({'caption_ta_file': 'Captions must be WebVTT (.vtt).'})
        if self.chapters_file and not has_ext(self.chapters_file, {'.vtt'}):
            from django.core.exceptions import ValidationError
            raise ValidationError({'chapters_file': 'Chapters must be WebVTT (.vtt).'})
#-------------------------------
#



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
    final_exam_score = models.FloatField(default=0.0)
    final_exam_passed = models.BooleanField(default=False)
    certificate_issued_at = models.DateTimeField(null=True, blank=True)

    def update_progress(self):
        """
        Updates the student's overall course progress as a percentage.
        Progress considers videos watched (for unlocking and partial progress).
        Full completion requires video + MCQ + assignment.
        """
        total_topics = self.course.topics.count()
        if total_topics > 0:
            # Count topics with videos watched (for progress calculation)
            videos_watched_count = self.topiccompletion_set.filter(video_watched=True).count()
            # Use videos watched for progress (more lenient than full completion)
            self.overall_progress = (videos_watched_count / total_topics) * 100
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
    Completion requires: video watched + MCQ passed + assignment submitted
    """
    progress = models.ForeignKey(Progress, on_delete=models.CASCADE)
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)
    assignment_score = models.FloatField(null=True, blank=True)
    video_watched = models.BooleanField(default=False)
    mcq_passed = models.BooleanField(default=False)
    assignment_submitted = models.BooleanField(default=False)
    video_watched_at = models.DateTimeField(null=True, blank=True)
    mcq_passed_at = models.DateTimeField(null=True, blank=True)
    assignment_submitted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ['progress', 'topic']

    def check_completion(self):
        """Mark topic as completed if all requirements met"""
        if self.video_watched and self.mcq_passed and self.assignment_submitted:
            self.completed = True
            self.save()
            # Update course progress
            self.progress.update_progress()
        return self.completed

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

class MCQQuestion(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='mcqs')
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='mcqs', blank=True, null=True, help_text='Optional: Link MCQ to specific topic')
    question_text = models.TextField()
    image = models.ImageField(upload_to='mcq_images/', blank=True, null=True)
    option_1 = models.CharField(max_length=255)
    option_2 = models.CharField(max_length=255)
    option_3 = models.CharField(max_length=255)
    option_4 = models.CharField(max_length=255)
    correct_option = models.PositiveSmallIntegerField(choices=[(i, f"Option {i}") for i in range(1, 5)])

    class Meta:
        ordering = ['topic__order', 'id']

    def __str__(self):
        topic_str = f" - {self.topic.title}" if self.topic else ""
        return f"{self.course.title}{topic_str} - {self.question_text[:30]}"


# ------------------------------
# Final Exam Models
# ------------------------------
class FinalExam(models.Model):
    course = models.OneToOneField(Course, on_delete=models.CASCADE, related_name='final_exam')
    title = models.CharField(max_length=200, default='Final Examination')
    num_questions = models.PositiveIntegerField(default=20)
    pass_mark = models.PositiveIntegerField(default=70, help_text='Percent required to pass')
    active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.course.title} - Final Exam"


class FinalExamQuestion(models.Model):
    exam = models.ForeignKey(FinalExam, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    image = models.ImageField(upload_to='final_exam_images/', blank=True, null=True)
    option_1 = models.CharField(max_length=255)
    option_2 = models.CharField(max_length=255)
    option_3 = models.CharField(max_length=255)
    option_4 = models.CharField(max_length=255)
    correct_option = models.PositiveSmallIntegerField(choices=[(i, f"Option {i}") for i in range(1, 5)])

    def __str__(self):
        return f"{self.exam.course.title} - {self.question_text[:30]}"


class FinalExamSubmission(models.Model):
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='final_exam_submissions')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='final_exam_submissions')
    score = models.PositiveIntegerField()
    passed = models.BooleanField(default=False)
    submitted_at = models.DateTimeField(auto_now_add=True)
    details = models.JSONField(null=True, blank=True)

    class Meta:
        ordering = ['-submitted_at']

    def __str__(self):
        return f"{self.student.name} - {self.course.title} ({self.score}%)"
