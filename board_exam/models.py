from django.db import models
from django import forms
from django.utils import timezone
from django.utils.html import format_html
from PIL import Image
from io import BytesIO
from .config import BOARD_EXAM_TOPICS, LEVELS
from django.contrib.auth import get_user_model
import os, django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Electronic_exam.settings")
django.setup()

# check/create superuser safely
User = get_user_model()
if not User.objects.filter(is_superuser=True).exists():
    User.objects.create_superuser("admin", "admin@example.com", "admin@03")

def get_board_exam_choices():
    return [(exam, exam) for exam in BOARD_EXAM_TOPICS.keys()]

def get_level_choices():
    return [(lvl, lvl) for lvl in LEVELS]


class Question(models.Model):
    board_exams = models.ManyToManyField("BoardExam")  # Can select multiple
    subjects = models.ManyToManyField("Subject")       
    topic = models.ForeignKey("Topic", on_delete=models.SET_NULL, null=True, blank=True)
    difficulty = models.ForeignKey("DifficultyLevel", on_delete=models.SET_NULL, null=True)
    source = models.CharField(max_length=255, default="google.com", null=False)
    question_text = models.TextField()

    def __str__(self):
        return f"Q{self.id}: {self.question_text[:50]}"



class QuestionImage(models.Model):
    question = models.ForeignKey(
        "Question",
        on_delete=models.CASCADE,
        related_name="images"
    )
    image = models.ImageField(upload_to='question_images/')


class Choice(models.Model):
    question = models.ForeignKey(
        "Question",
        on_delete=models.CASCADE,
        related_name="choices"
    )
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.question.id} - {self.text}"


class BoardExam(models.Model):
    name = models.CharField(max_length=50, choices=get_board_exam_choices(), default="General")

    def __str__(self):
        return self.name


class Subject(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class Topic(models.Model):
    name = models.CharField(max_length=255)
    subject = models.ForeignKey("Subject", on_delete=models.CASCADE, related_name="topics")

    def __str__(self):
        return self.name


class DifficultyLevel(models.Model):
    level = models.CharField(max_length=50, choices=get_level_choices(), default="E")

    def __str__(self):
        return self.level


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = [
            'board_exams',
            'subjects',   # updated field
            'topic',
            'difficulty',
            'source',
            'question_text',
        ]
        widgets = {
            'board_exams': forms.CheckboxSelectMultiple(),
            'subjects': forms.CheckboxSelectMultiple(),  # allow selecting multiple
        }



class AnswerKey(models.Model):
    board_exam = models.CharField(max_length=100) 
    subject = models.CharField(max_length=100)
    # topic = models.CharField(max_length=100, default="Misc")      
    set_id = models.CharField(max_length=32, unique=True)
    answer_key = models.JSONField()

    def __str__(self):
        return f"Answer Key for {self.board_exam} - {self.subject} ({self.set_id})"
    

class TestKey(models.Model):
    set_id = models.CharField(max_length=32, unique=True)
    board_exam = models.CharField(max_length=50)
    subject = models.CharField(max_length=100)
    exam_date = models.DateField(default=timezone.now)
    subject_group = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Logical group: BOARD-YYYY-MM-SUBJECT"
    )

    questions = models.JSONField(null=True, blank=True)
    image = models.ImageField(null=True, blank=True)
    choiceA = models.JSONField(null=True)
    choiceB = models.JSONField(null=True)    
    choiceC = models.JSONField(null=True)
    choiceD = models.JSONField(null=True)
    choiceE = models.JSONField(null=True)

    def __str__(self):
        return f"{self.board_exam} - {self.subject} ({self.exam_date.strftime('%B %Y')})"

    def add_question(self, question_text, image=None):
        """
        Adds a question to the test with an optional image.
        If the image is provided, store the image URL in the question dictionary.
        If no image is provided, store None.
        """
        question = {
            "question_text": question_text,
            "image": image.url if image else None,  # Store image URL or None
        }
        if not self.questions:
            self.questions = []
        self.questions.append(question)
        self.save()

    def get_question_images(self):
        # Safely access the 'image' key using .get() to avoid KeyError
        return [q.get("image_url") for q in self.questions if q.get("image_url")]



from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email

class Teacher(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    last_name = models.CharField(max_length=100, default = None)
    first_name = models.CharField(max_length=100, default = None)
    middle_name = models.CharField(max_length=100, default = None)
    birthdate = models.DateField(null=True, blank=True)

    # Add other fields as needed

    def __str__(self):
        return f"{self.last_name}, {self.first_name} {self.middle_name}"

class Student(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    student_id = models.CharField(max_length=9, default = None)
    last_name = models.CharField(max_length=100, default = None)
    first_name = models.CharField(max_length=100, default = None)
    middle_name = models.CharField(max_length=100, default = None)
    birthdate = models.DateField(null=True, blank=True)
    course = models.CharField(max_length=100, default = None)
    # Add other fields as needed

    def __str__(self):
        return f"{self.last_name}, {self.first_name} {self.middle_name}"

class Result(models.Model):
    timestamp = models.DateTimeField(default=timezone.now)

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="results",
        default=1,
    )

    student_id = models.CharField(max_length=9)
    course = models.CharField(max_length=100)
    student_name = models.CharField(max_length=100)

    subject = models.CharField(max_length=100)  # UNIQUE PER USER
    exam_id = models.CharField(max_length=32)  # can be different set IDs

    answer = models.JSONField(null=True)
    correct_answer = models.JSONField(null=True)

    score = models.IntegerField()
    total_items = models.IntegerField(default=0)
    is_submitted = models.BooleanField(default=False)
    elapsed_time = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        unique_together = ("user", "subject")  # ❌ prevent multiple attempts per subject

    
User = get_user_model()

class PracticeResult(models.Model):
    session_id = models.UUIDField(unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    board_exam = models.CharField(max_length=50)
    total_items = models.IntegerField()
    score = models.IntegerField()
    percent = models.FloatField()
    total_time = models.FloatField(help_text="Total time in seconds")
    answers = models.JSONField(help_text="List of student's answers with question_id, selected, correct, time_spent")
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} - {self.board_exam} ({self.session_id})"
    
class SubjectAnalytics(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    subject = models.CharField(max_length=255)
    board_exam = models.CharField(max_length=50)

    total_items_answered = models.IntegerField(default=0)
    total_correct = models.IntegerField(default=0)
    total_attempts = models.IntegerField(default=0)

    average_time_per_item = models.FloatField(default=0.0)
    last_practice_date = models.DateTimeField(auto_now=True)

    def accuracy(self):
        if self.total_items_answered == 0:
            return 0
        return round((self.total_correct / self.total_items_answered) * 100, 2)

    def __str__(self):
        return f"{self.user.username} - {self.subject}"

class TopicAnalytics(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    subject = models.CharField(max_length=255)
    topic = models.CharField(max_length=255)

    total_items_answered = models.IntegerField(default=0)
    total_correct = models.IntegerField(default=0)

    average_time_per_item = models.FloatField(default=0.0)
    last_practice_date = models.DateTimeField(auto_now=True)

    def accuracy(self):
        if self.total_items_answered == 0:
            return 0
        return round((self.total_correct / self.total_items_answered) * 100, 2)

    def __str__(self):
        return f"{self.user.username} - {self.subject} - {self.topic}"

class DifficultyAnalytics(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    board_exam = models.CharField(max_length=50)
    difficulty = models.CharField(max_length=50)  # Easy, Moderate, Hard

    total_items_answered = models.IntegerField(default=0)
    total_correct = models.IntegerField(default=0)

    last_practice_date = models.DateTimeField(auto_now=True)

    def accuracy(self):
        if self.total_items_answered == 0:
            return 0
        return round((self.total_correct / self.total_items_answered) * 100, 2)

    def __str__(self):
        return f"{self.user.username} - {self.difficulty}"

