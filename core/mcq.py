from django.db import models
from django.core.exceptions import ValidationError
from .models import Topic, Course
from accounts.models import CustomUser
import random

class MCQQuestion(models.Model):
    """
    Represents an MCQ question that can be associated with multiple topics.
    """
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='mcq_questions')
    question_text = models.TextField()
    option_1 = models.CharField(max_length=200)
    option_2 = models.CharField(max_length=200)
    option_3 = models.CharField(max_length=200)
    option_4 = models.CharField(max_length=200)
    correct_option = models.IntegerField(choices=[(1, 'Option 1'), (2, 'Option 2'), (3, 'Option 3'), (4, 'Option 4')])
    
    def __str__(self):
        return f"{self.topic.title} - {self.question_text[:50]}"

class MCQTest(models.Model):
    """
    Represents a test instance for a student with randomly selected questions
    """
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    questions = models.ManyToManyField(MCQQuestion, through='MCQTestQuestion')
    is_completed = models.BooleanField(default=False)
    score = models.FloatField(null=True, blank=True)

    def generate_test(self, num_questions=15):
        """
        Generates a test with random questions for the topic
        """
        available_questions = list(MCQQuestion.objects.filter(topic=self.topic))
        if len(available_questions) < num_questions:
            raise ValidationError(f"Not enough questions available. Need {num_questions}, but only {len(available_questions)} exist.")
        
        selected_questions = random.sample(available_questions, num_questions)
        for question in selected_questions:
            MCQTestQuestion.objects.create(test=self, question=question)

    def calculate_score(self):
        """
        Calculates the score based on submitted answers
        """
        total_questions = self.mcqtestquestion_set.count()
        correct_answers = self.mcqtestquestion_set.filter(is_correct=True).count()
        self.score = (correct_answers / total_questions) * 100
        self.is_completed = True
        self.save()

class MCQTestQuestion(models.Model):
    """
    Represents a question in a specific test instance
    """
    test = models.ForeignKey(MCQTest, on_delete=models.CASCADE)
    question = models.ForeignKey(MCQQuestion, on_delete=models.CASCADE)
    selected_option = models.IntegerField(null=True, blank=True)
    is_correct = models.BooleanField(null=True)

    def check_answer(self):
        """
        Checks if the selected answer is correct
        """
        if self.selected_option:
            self.is_correct = (self.selected_option == self.question.correct_option)
            self.save()