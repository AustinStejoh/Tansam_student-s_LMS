from django.db import models

class Course(models.Model):
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

class Topic(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='topics')
    title = models.CharField(max_length=200)
    content = models.TextField()
    order = models.PositiveIntegerField()
    assignment = models.JSONField(null=True, blank=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.course.title} - {self.title}"

class Progress(models.Model):
    student = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE, limit_choices_to={'role': 'student'})
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    completed_topics = models.ManyToManyField(Topic, through='TopicCompletion')
    overall_progress = models.FloatField(default=0.0)

    def update_progress(self):
        total_topics = self.course.topics.count()
        completed_count = self.topiccompletion_set.filter(completed=True).count()
        self.overall_progress = (completed_count / total_topics * 100) if total_topics > 0 else 0
        self.save()

    def __str__(self):
        return f"{self.student.name} - {self.course.title}"

class TopicCompletion(models.Model):
    progress = models.ForeignKey(Progress, on_delete=models.CASCADE)
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)
    assignment_score = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"{self.progress.student.name} - {self.topic.title}"

class Payment(models.Model):
    student = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE, limit_choices_to={'role': 'student'})
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)
    transaction_id = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return f"{self.student.name} - {self.amount}"