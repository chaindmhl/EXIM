from django import forms
from board_exam.models import CustomUser, Question, Choice, QuestionImage, Teacher, Student # Import your custom user model
from django.contrib.auth.hashers import make_password
from django.forms import inlineformset_factory
from django.contrib.auth.forms import AuthenticationForm


class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(label='Email', max_length=254)

class SignUpForm(forms.Form):
    ROLE_CHOICES = (
        ('teacher', 'Teacher'),
        ('student', 'Student'),
    )

    role = forms.ChoiceField(choices=ROLE_CHOICES)
    student_id = forms.CharField(max_length=9, required=False)
    course = forms.ChoiceField(
        choices=(
            ('Civil Engineering', 'Civil Engineering'),
            ('Electrical Engineering', 'Electrical Engineering'),
            ('Electronics Engineering', 'Electronics Engineering'),
            ('Mechanical Engineering', 'Mechanical Engineering'),
        ),
        required=False
    )

    last_name = forms.CharField(max_length=100)
    first_name = forms.CharField(max_length=100)
    middle_name = forms.CharField(max_length=100, required=False)
    birthdate = forms.DateField(required=False)

    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)
    retype_password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = CustomUser
        fields = [
            'role', 'student_id', 'course',
            'last_name', 'first_name', 'middle_name',
            'birthdate', 'email', 'password', 'retype_password'
        ]

    def clean_email(self):
        return self.cleaned_data.get('email')

    def clean(self):
        cleaned = super().clean()
        role = cleaned.get('role')

        # password check
        if cleaned.get('password') != cleaned.get('retype_password'):
            self.add_error('retype_password', 'Passwords do not match.')

        # student-specific checks
        if role == 'student':
            if not cleaned.get('student_id'):
                self.add_error('student_id', 'Student ID is required.')
            if not cleaned.get('course'):
                self.add_error('course', 'Course is required.')

        return cleaned

    

class AnswerSheetForm(forms.Form):
    def __init__(self, *args, **kwargs):
        question_choices = kwargs.pop('question_choices')
        super().__init__(*args, **kwargs)

        # Create each question as a ChoiceField
        for i, (q_text, choices, image_url) in enumerate(question_choices):
            # choices = [('A', 'Blue'), ('B', 'Red'), ...]
            self.fields[f'question_{i+1}'] = forms.ChoiceField(
                choices=[(letter, letter) for letter, text in choices],  # LETTER as value
                widget=forms.RadioSelect,
                required=True
            )

ChoiceFormSet = inlineformset_factory(
    Question,
    Choice,
    fields=('text', 'is_correct'),
    extra=5,
    can_delete=False
)

ImageFormSet = inlineformset_factory(
    Question,
    QuestionImage,
    fields=('image',),
    extra=1,
    can_delete=True
)