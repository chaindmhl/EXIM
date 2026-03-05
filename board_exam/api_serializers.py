from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Student, AnswerKey

User = get_user_model()

# -----------------------------
# User / Auth Serializers
# -----------------------------
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'is_staff', 'is_student', 'username']

class StudentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Student
        fields = ['id', 'user', 'student_id', 'first_name', 'last_name', 'middle_name', 'birthdate', 'course']

# -----------------------------
# Answer Key Serializer
# -----------------------------
class AnswerKeySerializer(serializers.ModelSerializer):
    class Meta:
        model = AnswerKey
        fields = ['set_id', 'subject', 'answer_key']