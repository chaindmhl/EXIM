from django import forms
from board_exam.models import CustomUser, Question, Choice, QuestionImage, Teacher, Student # Import your custom user model
from django.contrib.auth.hashers import make_password
from django.forms import inlineformset_factory
from django.contrib.auth.forms import AuthenticationForm


class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(label='Email', max_length=254)

class SignUpForm(forms.ModelForm):
    role = forms.ChoiceField(choices=(('teacher', 'Teacher'), ('student', 'Student')))
    student_id = forms.CharField(max_length=9, required=False)
    course = forms.ChoiceField(choices=(
        ('Civil Engineering', 'Civil Engineering'),
        ('Electrical Engineering', 'Electrical Engineering'),
        ('Electronics Engineering', 'Electronics Engineering'),
        ('Mechanical Engineering', 'Mechanical Engineering'),
    ))
    last_name = forms.CharField(max_length=100)
    first_name = forms.CharField(max_length=100)
    middle_name = forms.CharField(max_length=100)
    birthdate = forms.DateField()
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)
    retype_password = forms.CharField(widget=forms.PasswordInput, label='Retype Password')

    class Meta:
        model = CustomUser
        fields = ['role', 'student_id', 'course', 'last_name', 'first_name', 'middle_name', 'birthdate', 'email', 'password', 'retype_password']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError("This email address is already in use. Please use a different email.")
        return email
    
    def clean_student_id(self):
        student_id = self.cleaned_data.get('student_id')
        if self.cleaned_data.get('role') == 'student' and Student.objects.filter(student_id=student_id).exists():
            raise forms.ValidationError("This student ID is already registered!")
        return student_id
    

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