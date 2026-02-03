from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from .models import QuestionForm, Question, BoardExam, Subject, Topic, DifficultyLevel, Question, QuestionImage, Choice, AnswerKey, TestKey, Teacher, Student, Result, PracticeResult, SubjectAnalytics, TopicAnalytics, DifficultyAnalytics
from django.views import View
from django.template.loader import render_to_string
from weasyprint import HTML
import random, io, zipfile, uuid, re
import xml.etree.ElementTree as ET
from scripts.check import detect_objects, sort_objects_by_distance, group_and_sequence
from django.http import JsonResponse
import numpy as np
import cv2, time, os, json, base64, traceback
from .forms import loginpForm, ChoiceFormSet, ImageFormSet
from django.contrib.auth import logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from django.views.decorators.csrf import csrf_protect
from django.db import IntegrityError
from django.db.models import Q
from .forms import AnswerSheetForm
from itertools import zip_longest
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils import timezone
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.conf import settings
import PyPDF2
import fitz
import pdfplumber, docx, string
from docx import Document
from PyPDF2 import PdfReader
from django.core.files import File
import pandas as pd
from .config import BOARD_EXAM_TOPICS, LEVELS
from django.db import models
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from django.db.models import Count, Q, Avg, F
from collections import defaultdict
from django.views.decorators.http import require_http_methods
import datetime
import openai
from datetime import datetime



logo_path = os.path.join(settings.BASE_DIR, 'static', 'EXIM2.png')  # full path
# SET_ID_PREFIX = {
#     "Civil Engineering": "CE",
#     "Mechanical Engineering": "ME",
#     "Electronics Engineering": "ECE",
#     "Electrical Engineering": "EE",
# }

####################### FOR SIGNING UP ##############################

from django.contrib.auth import login

@csrf_protect
def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            # Create and save the CustomUser instance
            user = form.save(commit=False)
            user.is_active = True
            user.password = make_password(form.cleaned_data['password'])  # Hash the password

            # Determine role
            role = form.cleaned_data.get('role')
            if role == 'student':
                user.is_student = True  # <-- Automatically mark student
                user.save()

                course = form.cleaned_data.get('course')
                Student.objects.create(
                    user=user,
                    student_id=form.cleaned_data.get('student_id'),
                    last_name=form.cleaned_data.get('last_name'),
                    first_name=form.cleaned_data.get('first_name'),
                    middle_name=form.cleaned_data.get('middle_name'),
                    birthdate=form.cleaned_data.get('birthdate'),
                    course=course,
                )
            elif role == 'teacher':
                user.is_student = False  # <-- Teacher is not student
                user.save()

                Teacher.objects.create(
                    user=user,
                    last_name=form.cleaned_data.get('last_name'),
                    first_name=form.cleaned_data.get('first_name'),
                    middle_name=form.cleaned_data.get('middle_name'),
                    birthdate=form.cleaned_data.get('birthdate'),
                )
            else:
                raise ValidationError("Invalid role selected")

            messages.success(request, "Account successfully signed up!")        
            return redirect('login')
    else:
        form = SignUpForm()
    return render(request, 'signup.html', {'form': form})

homhom
def login_view(request):
    if request.method == 'POST':
        form = EmailAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = authenticate(
                request,
                username=form.cleaned_data.get('username'),
                password=form.cleaned_data.get('password')
            )
            if user:
                login(request, user)
                if is_teacher(user):
                    return redirect('home')
                elif is_student(user):
                    return redirect('home_student')
                else:
                    logout(request)
                    messages.error(request, "No role assigned.")
                    return redirect('login')
            messages.error(request, "Invalid email or password.")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = EmailAuthenticationForm()
    return render(request, 'login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')
####################### FOR DASHBOARD ##############################

def is_teacher(user):
    return hasattr(user, 'teacher') and user.is_staff

def is_student(user):
    return hasattr(user, 'student') and user.is_student


@login_required
def main_dashboard(request):
    if request.user.is_authenticated:
        if is_teacher(request.user):
            return redirect('home')  # Redirect to teacher dashboard
        else:
            return redirect('student_dashboard')  # Redirect to student dashboard
    else:
        return redirect('login')  # Redirect to login page if user is not authenticated

from django.http import HttpResponseForbidden

from django.http import HttpResponseForbidden

@login_required
def home(request):
    # Only allow teachers/staff
    if not request.user.is_staff and not hasattr(request.user, 'teacher'):
        return HttpResponseForbidden("You cannot access this page")
    return render(request, 'home.html')

@login_required
def home_student(request):
    # Only allow students
    if not hasattr(request.user, 'student'):
        return HttpResponseForbidden("You cannot access this page")
    return render(request, 'home_student.html')


def root_redirect(request):
    """Redirect users to the correct dashboard based on role"""
    if not request.user.is_authenticated:
        return redirect('login')  # Not logged in → login page

    # Check user role
    if request.user.is_staff and hasattr(request.user, 'teacher'):
        return redirect('home')  # Teacher/admin
    elif hasattr(request.user, 'student'):
        return redirect('home_student')  # Student
    else:
        # Optional: fallback for logged-in users with no role
        return redirect('login')


@login_required
def student_dashboard(request):
    # Logic for student's dashboard
    return render(request, 'student_dashboard.html')

def logout_view(request):
    logout(request)
    return redirect('login')  

####################### FOR ADDING QUESTION TO QUESTION BANK ##############################

def question_bank(request):
    # Prefetch all related objects for efficiency
    questions = Question.objects.all().prefetch_related(
        'choices',       # Choices
        'images',        # Question images
        'board_exams',   # Board exams
        'subjects',      # Subjects
        'topic'          # Topic (assuming ForeignKey)
    )

    letters = ["A", "B", "C", "D", "E"]

    for q in questions:
        # Map choices to letters A-E
        q.lettered_choices = []
        for i, choice in enumerate(q.choices.all()):
            if i < 5:
                q.lettered_choices.append((letters[i], choice))
        # Pad with None if fewer than 5 choices
        while len(q.lettered_choices) < 5:
            q.lettered_choices.append((None, None))

        # Correct answer text
        correct_choice = next((choice for choice in q.choices.all() if choice.is_correct), None)
        q.correct_answer_text = correct_choice.text if correct_choice else "-"

        # Board exams names
        q.board_exam_names = ", ".join([be.name for be in q.board_exams.all()])

        # Subjects names
        q.subject_names = ", ".join([sub.name for sub in q.subjects.all()])

        # Topic name
        q.topic_name = q.topic.name if q.topic else "-"

        # Difficulty name
        q.level_name = q.difficulty.level if q.difficulty else "-"

        # Image urls (list)
        q.image_urls = [img.image.url for img in q.images.all()] if q.images.exists() else []

    return render(request, 'question_bank.html', {'questions': questions})
class Add_Question(View):
    def get(self, request):
        context = {
            'BOARD_EXAMS': list(BOARD_EXAM_TOPICS.keys()),
            'BOARD_EXAM_TOPICS_JSON': json.dumps(BOARD_EXAM_TOPICS),
            'LEVELS_JSON': json.dumps(LEVELS),
        }
        return render(request, "add_question.html", context)

    def post(self, request):
        # Count dynamically generated questions
        num_questions = sum(1 for key in request.POST.keys() if key.startswith("question_text_"))

        if num_questions == 0:
            messages.error(request, "No questions to save!")
            return redirect("add_question")

        for i in range(1, num_questions + 1):
            board_exam_names = request.POST.getlist(f"board_exam_{i}")  # multiple exams
            subject_names = request.POST.getlist(f"subjects_{i}[]")      # <-- fixed here
            topic_name = request.POST.get(f"topic_{i}")
            level_name = request.POST.get(f"level_{i}")
            question_text = request.POST.get(f"question_text_{i}")
            source = request.POST.get(f"source_{i}", "google.com")

            # Create or get Subject objects
            subjects = []
            for name in subject_names:
                sub_obj, _ = Subject.objects.get_or_create(name=name)
                subjects.append(sub_obj)

            # Create or get Topic and Difficulty
            topic = Topic.objects.get_or_create(name=topic_name, subject=subjects[0])[0]
            level = DifficultyLevel.objects.get_or_create(level=level_name)[0]

            # Create Question
            q = Question.objects.create(
                topic=topic,
                difficulty=level,
                question_text=question_text,
                source=source
            )

            # Add all selected subjects
            q.subjects.set(subjects)

            # Add board exams
            for name in board_exam_names:
                exam = BoardExam.objects.get_or_create(name=name)[0]
                q.board_exams.add(exam)

            # Save uploaded image if any
            image_file = request.FILES.get(f"image_{i}")
            if image_file:
                QuestionImage.objects.create(question=q, image=image_file)

            # Save choices
            for choice_letter in ["A", "B", "C", "D", "E"]:
                choice_text = request.POST.get(f"choice{choice_letter}_{i}")
                if choice_text:
                    is_correct = request.POST.get(f"correct_answer_{i}") == choice_letter
                    Choice.objects.create(
                        question=q,
                        text=choice_text,
                        is_correct=is_correct
                    )

        messages.success(request, f"{num_questions} questions added successfully!")
        return redirect("question_bank")


####################### FOR CREATING EXAMINATION ##############################   

def get_random_questions(num_questions, subject):
    # Retrieve questions from the database filtered by subject
    all_questions = list(Question.objects.filter(subject=subject))

    # Check if the number of requested questions is greater than the available questions
    if num_questions > len(all_questions):
        raise ValueError("Number of requested questions exceeds the available questions for the subject.")

    # Randomly select the specified number of questions
    selected_questions = random.sample(all_questions, num_questions)

    return selected_questions



# reuse your existing config context
context = {
    'BOARD_EXAMS': list(BOARD_EXAM_TOPICS.keys()),
    'BOARD_EXAM_TOPICS_JSON': json.dumps(BOARD_EXAM_TOPICS),
    'LEVELS_JSON': json.dumps(LEVELS),
}

def generate_set_id(board_exam):
    board_exam = board_exam.lower()

    if "civil" in board_exam:
        prefix = "CE"
    elif "mechanical" in board_exam:
        prefix = "ME"
    elif "electronics" in board_exam or "ece" in board_exam:
        prefix = "ECE"
    elif "electrical" in board_exam or "ee" in board_exam:
        prefix = "EE"
    else:
        prefix = "GEN"

    # UUID shortened to 8 characters only
    return f"{prefix}_{uuid.uuid4().hex[:8]}"

def get_shuffled_choices(question):
    choices = list(question.choices.all())
    random.shuffle(choices)
    # Assign letters A, B, C, ... dynamically
    letters = ['A', 'B', 'C', 'D', 'E']
    return [{'letter': letters[i], 'text': choice.text} for i, choice in enumerate(choices)]
    
def shuffle_question_choices(question):
    import random
    choices = list(question.choices.all())
    random.shuffle(choices)
    letters = ['A', 'B', 'C', 'D', 'E']
    return [{'letter': letters[i], 'text': c.text, 'is_correct': c.is_correct} for i, c in enumerate(choices)]


def build_question_data(questions):
    data = []
    for q in questions:
        image_obj = q.images.first()
        data.append({
            'id': q.id,
            'question_text': q.question_text,
            'image': image_obj.image.url if image_obj else None,
            'choices': get_shuffled_choices(q)
        })
    return data


def generate_test(request):
    context = {
        'BOARD_EXAMS': list(BOARD_EXAM_TOPICS.keys()),
        'SUBJECTS_JSON': json.dumps(BOARD_EXAM_TOPICS),
        'LEVELS': LEVELS,
    }

    if request.method == 'POST':
        board_exam = request.POST.get('board_exam')
        subject = request.POST.get('subject', '').strip()
        topic = request.POST.get('topic', '').strip()
        num_questions = int(request.POST.get('num_questions', 0))

        qs = Question.objects.all()
        if board_exam:
            qs = qs.filter(board_exams__name__iexact=board_exam)
        if subject:
            qs = qs.filter(subjects__name__icontains=subject)
        if topic:
            qs = qs.filter(topic__name__icontains=topic)
        if qs.count() < num_questions:
            context['error_message'] = "Not enough questions available."
            return render(request, 'generate_test.html', context)

        # Select random questions
        selected_questions = random.sample(list(qs), num_questions)

        # Shuffle questions for each set independently
        set_a_questions = build_question_data(selected_questions.copy())
        random.shuffle(selected_questions)  # shuffle the original list for Set B
        set_b_questions = build_question_data(selected_questions)

        return render(request, 'generated_test.html', {
            'set_a_questions': set_a_questions,
            'set_b_questions': set_b_questions,
            'board_exam': board_exam,
            'subject': subject,
            'set_a_id': uuid.uuid4().hex,
            'set_b_id': uuid.uuid4().hex,
        })

    return render(request, 'generate_test.html', context)


####################### FOR DOWNLOADING EXAMINATION SHEET ##############################
def map_letter_text(choices_lists, correct_text_dict):
    """
    choices_lists: list of lists, e.g. [choicesA, choicesB, choicesC, ...]
    correct_text_dict: {1: "4", 2: "Blue", ...}
    
    Returns: { "1": {"letter": "A", "text": "4"}, ... }
    """
    answer_key = {}
    num_choices = len(choices_lists)
    letters = list(string.ascii_uppercase[:num_choices])  # ['A','B','C',...]
    
    for i, correct_text in correct_text_dict.items():
        # Map letters to the corresponding choice text
        choice_map = {letters[idx]: choices_lists[idx][i-1] for idx in range(num_choices)}
        correct_letter = next((l for l, t in choice_map.items() if t == correct_text), None)
        answer_key[str(i)] = {"letter": correct_letter, "text": correct_text}
    
    return answer_key

# Helper: extract choice lists from questions
def extract_choices_by_letter(questions):
    letters = ['A', 'B', 'C', 'D', 'E']
    choice_map = {letter: [] for letter in letters}
    for q in questions:
        q_choices = q.get('choices', [])
        for i, letter in enumerate(letters):
            if i < len(q_choices):
                choice_map[letter].append(q_choices[i]['text'])
            else:
                choice_map[letter].append(None)  # pad empty choices
    return choice_map


def build_testkey_choices(question_ids):
    letters = ['A','B','C','D','E']
    result = {l: [] for l in letters}

    for qid in question_ids:
        q = Question.objects.get(id=qid)
        choices = list(q.choices.all().order_by('id'))

        for i, letter in enumerate(letters):
            if i < len(choices):
                result[letter].append(choices[i].text)
            else:
                result[letter].append(None)

    return result

# Helper to build question data including choices
def get_questions_with_choices(question_ids):
    questions = []
    letters = ['A', 'B', 'C', 'D', 'E']
    for qid in question_ids:
        q = Question.objects.get(id=qid)
        image_obj = q.images.first()
        image_url = image_obj.image.url if image_obj else None

        choice_objs = list(q.choices.all().order_by('id'))
        choices = []
        for letter, choice in zip(letters, choice_objs):
            choices.append({
                "letter": letter,
                "text": str(choice.text)
            })

        questions.append({
            "question": str(q.question_text),
            "choices": choices,
            "image_url": str(image_url) if image_url else None
        })
    return questions

# Helper to build answer key (letter-text)
def build_answer_key(question_ids):
    letters = ['A','B','C','D','E']
    answer_key = {}

    for i, qid in enumerate(question_ids, start=1):
        q = Question.objects.get(id=qid)
        choices = list(q.choices.all().order_by('id'))

        for idx, c in enumerate(choices):
            if c.is_correct:
                answer_key[str(i)] = {
                    "letter": letters[idx],
                    "text": str(c.text)
                }
                break

    return answer_key


def download_test_pdf(request):
    if request.method != 'POST':
        return HttpResponse("Invalid request method", status=405)

    try:
        subject_name = request.POST.get('subject')
        board_exam_name = request.POST.get('board_exam')

        set_a_question_ids = request.POST.getlist('set_a_question_ids[]')
        set_b_question_ids = request.POST.getlist('set_b_question_ids[]')

        # Generate unique IDs in format: BOARD_EXAM_UUID
        set_a_id = f"{board_exam_name}_{uuid.uuid4().hex[:8]}"
        set_b_id = f"{board_exam_name}_{uuid.uuid4().hex[:8]}"

        # Build questions and answer keys
        questions_set_a = get_questions_with_choices(set_a_question_ids)
        questions_set_b = get_questions_with_choices(set_b_question_ids)

        set_a_answer_key = build_answer_key(set_a_question_ids)
        set_b_answer_key = build_answer_key(set_b_question_ids)

        set_a_choice_map = extract_choices_by_letter(questions_set_a)
        set_b_choice_map = extract_choices_by_letter(questions_set_b)

        # Save TestKey objects
        TestKey.objects.create(
            set_id=set_a_id,
            board_exam=board_exam_name,
            subject=subject_name,
            questions=questions_set_a,
            choiceA=set_a_choice_map['A'],
            choiceB=set_a_choice_map['B'],
            choiceC=set_a_choice_map['C'],
            choiceD=set_a_choice_map['D'],
            choiceE=set_a_choice_map['E'],
        )

        TestKey.objects.create(
            set_id=set_b_id,
            board_exam=board_exam_name,
            subject=subject_name,
            questions=questions_set_b,
            choiceA=set_b_choice_map['A'],
            choiceB=set_b_choice_map['B'],
            choiceC=set_b_choice_map['C'],
            choiceD=set_b_choice_map['D'],
            choiceE=set_b_choice_map['E'],
        )


        # Save AnswerKey objects
        AnswerKey.objects.create(
            set_id=set_a_id,
            board_exam=board_exam_name,
            subject=subject_name,
            answer_key=set_a_answer_key
        )
        AnswerKey.objects.create(
            set_id=set_b_id,
            board_exam=board_exam_name,
            subject=subject_name,
            answer_key=set_b_answer_key
        )

        # Render PDFs
        context_a = {
            'board_exam': board_exam_name,
            'subject': subject_name,
            'questions': questions_set_a,
            'set_name': "Set A",
            'set_id': set_a_id,
            'answer_key': set_a_answer_key,
            'logo_path': '',  # optional logo path
        }
        context_b = {
            'board_exam': board_exam_name,
            'subject': subject_name,
            'questions': questions_set_b,
            'set_name': "Set B",
            'set_id': set_b_id,
            'answer_key': set_b_answer_key,
            'logo_path': '',
        }

        html_a = render_to_string('pdf_template.html', context_a, request=request)
        html_b = render_to_string('pdf_template.html', context_b, request=request)

        pdf_a = HTML(string=html_a, base_url=request.build_absolute_uri('/')).write_pdf()
        pdf_b = HTML(string=html_b, base_url=request.build_absolute_uri('/')).write_pdf()

        # ZIP the PDFs
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
            zip_file.writestr(f"generated_test_set_a_{set_a_id}.pdf", pdf_a)
            zip_file.writestr(f"generated_test_set_b_{set_b_id}.pdf", pdf_b)

        response = HttpResponse(zip_buffer.getvalue(), content_type='application/zip')
        response['Content-Disposition'] = 'attachment; filename="generated_tests.zip"'
        return response

    except Exception as e:
        print("❌ ERROR in download_test_pdf:", traceback.format_exc())
        return HttpResponse(f"An error occurred: {str(e)}", status=500)

def download_test_interface(request):
    test_keys = TestKey.objects.all().order_by('-id')
    return render(request, 'download_test.html', {'test_keys': test_keys})


def download_existing_test_pdf(request):
    set_id = request.GET.get('set_id')
    if not set_id:
        return HttpResponse("No test selected.", status=400)

    try:
        test = TestKey.objects.get(set_id=set_id)
        questions_data = test.questions or []

        # Pass questions exactly as saved in TestKey
        pdf_questions = []
        for q in questions_data:
            pdf_questions.append({
                'question': q.get('question', ''),
                'choices': q.get('choices', []),   # keep list of dicts with letter & text
                'image_url': q.get('image_url', None)
            })

        answer_obj = AnswerKey.objects.filter(set_id=set_id).first()
        answer_key = answer_obj.answer_key if answer_obj else {}

        context = {
            'board_exam': test.board_exam,
            'subject': test.subject,
            'questions': pdf_questions,
            'set_name': test.set_id,
            'set_id': test.set_id,
            'answer_key': answer_key,
            'logo_path': '',  # optional logo
        }

        html_content = render_to_string('pdf_template.html', context, request=request)
        pdf_file = HTML(string=html_content, base_url=request.build_absolute_uri('/')).write_pdf()

        response = HttpResponse(pdf_file, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="test_{test.set_id}.pdf"'
        return response

    except Exception as e:
        print("❌ ERROR in download_existing_test_pdf:", traceback.format_exc())
        return HttpResponse(f"Error: {str(e)}", status=500)




####################### FOR UPLOADING MOODLE XML FILE (QUESTIONS) TO THE QUESTION BANK  ##############################

def strip_tags(html):
    # Regular expression to remove HTML tags
    return re.sub('<[^<]+?>', '', html)

def extract_and_save_questions(xml_file, subject):
    # Parse the XML file
    tree = ET.parse(xml_file)
    root = tree.getroot()

    # Iterate over each question
    for question in root.findall('.//question'):
        print("Processing question...")
        # Check if 'questiontext' tag exists
        question_text_element = question.find('questiontext')
        if question_text_element is not None:
            # Extract question text and image data
            question_text, image_file = extract_question_text_and_image(question_text_element, subject)
            print('question:', question_text)
            print("Image File:", image_file)
        else:
            question_text = ''
            image_file = None
            print("No 'questiontext' found for this question.") 

        # Print image file for debugging
        print("Image File:", image_file)
        print('question:', question_text)
        # Initialize variables to store correct answer and choices
        correct_answer = ''
        choices = [''] * 5  # Initialize with empty strings

        # Map the correct answer to its corresponding letter (A to E)
        answer_letter_map = {}

        # Check if question has multiple choices
        answers = question.findall('answer')
        if len(answers) < 2:
            # Skip this question if it doesn't have multiple choices
            continue

        # Iterate over each answer
        for i, answer in enumerate(answers):
            text = strip_tags(answer.find('text').text.strip())
            fraction = int(answer.get('fraction'))
            if fraction == 100:
                # Extract the correct answer and map it to the corresponding letter
                correct_answer = chr(65 + i)  # A corresponds to 65 in ASCII
            # Map the choices to letters (A to E)
            # choices[i] = f'{chr(65 + i)}. {text}'
            choices[i] = f'{text}'

        # Skip this question if both question text and choices are empty
        if not any([question_text, any(choices)]):
            continue

        # Save the image file to the local directory and get its path
        if image_file:
            image_path = save_image_locally(image_file)
            print("Image Path:", image_path)
        else:
            image_path = None

        # Print image path for debugging
        print("Image Path:", image_path)

        # Create an instance of your Django model and save it to the database
        question_instance = Question.objects.create(
            subject=subject,
            question_text=question_text,
            image=image_path,
            choiceA=choices[0],
            choiceB=choices[1],
            choiceC=choices[2],
            choiceD=choices[3],
            choiceE=choices[4],
            correct_answer=correct_answer
        )


def extract_question_text_and_image(question_text_element, subject):
    question_text = ''
    image_files = None

    # Check if the 'text' tag exists under 'questiontext'
    text_element = question_text_element.find('./text')
    if text_element is not None:
        # Extract the text content between <p> and </p> tags, or between <p> and <img> tags if present
        text_content = text_element.text.strip()
        if text_content:
            # Extract text between <p> and <img> tags
            match = re.search(r'<p>(.*?)<img', text_content)
            if match:
                question_text = match.group(1).strip()
            else:
                # Extract text between <p> and </p> tags if <img> tag is not present
                match = re.search(r'<p>(.*?)</p>', text_content)
                if match:
                    question_text = match.group(1).strip()

        # Check if there are file tags
        file_elements = question_text_element.findall('./file')
        for file_element in file_elements:
            image_name = file_element.get('name')
            if image_name.endswith('.png') or image_name.endswith('.jpg'):
                # Decode the base64 content of the file element
                file_content_base64 = file_element.text.strip()
                file_data = base64.b64decode(file_content_base64)
                # Create an InMemoryUploadedFile object for the image
                image_file = InMemoryUploadedFile(
                    ContentFile(file_data),
                    None,
                    image_name,  # Use the file name as the image name
                    'image/jpeg',  # Assuming the image is JPEG format
                    len(file_data),
                    None
                )
    else:
        print("No 'text' tag found under 'questiontext'.")

    return question_text, image_file




def save_image_locally(image_file):
    # Get the media directory
    media_dir = os.path.join(settings.MEDIA_ROOT, 'question_images')
    # Ensure the media directory exists
    os.makedirs(media_dir, exist_ok=True)
    # Construct the filename without the '/media/' part
    _, filename = os.path.split(image_file.name)
    # Save the image file to the media directory
    image_path = os.path.join(media_dir, filename)
    with open(image_path, 'wb') as f:
        f.write(image_file.read())
    # return image_path
    return os.path.join('question_images', filename)  # Return the relative path


def upload_xml(request):
    print(request.FILES)  # Print the contents of request.FILES
    if request.method == 'POST' and 'xml_file' in request.FILES:
        xml_file = request.FILES['xml_file']
        subject = request.POST.get('subject') 
        extract_and_save_questions(xml_file, subject)
        return HttpResponse("XML file uploaded. Questions are successfully stored in Question Bank.")
    return render(request, 'upload_xml.html')

# -----------------------------------------
# TEXT EXTRACTORS
# -----------------------------------------

def extract_pdf_text(file):
    reader = PyPDF2.PdfReader(file)
    text = ""
    for page in reader.pages:
        p = page.extract_text() or ""
        text += p + "\n"
    return text

def extract_text_from_docx(file):
    doc = Document(file)
    return "\n".join([p.text for p in doc.paragraphs])

def extract_text_from_txt(file):
    return file.read().decode("utf-8", errors="ignore")

# -----------------------------------------
# SAVE QUESTION
# -----------------------------------------

def save_question(
    question_text,
    choices,
    image_filename,
    level,
    source,
    subject_name,
    topic_name,
    board_exam_list=None,
    image_files=None
):
    # Ensure difficulty is uppercase
    level = str(level).strip().upper()

    print("DEBUG: save_question called for:", question_text[:80], "LEVEL=", level)

    difficulty, _ = DifficultyLevel.objects.get_or_create(level=level)

    subject_obj, _ = Subject.objects.get_or_create(name=(subject_name or "").strip())
    topic_obj = None
    if topic_name:
        topic_obj, _ = Topic.objects.get_or_create(name=topic_name.strip(), subject=subject_obj)

    q = Question.objects.create(
        subject=subject_obj,
        topic=topic_obj,
        difficulty=difficulty,
        source=(source or "google.com"),
        question_text=question_text,
    )

    print("DEBUG: Question created id=", q.id)

    # Board Exams
    if board_exam_list:
        for be in board_exam_list:
            if be:
                exam, _ = BoardExam.objects.get_or_create(name=str(be).strip())
                q.board_exams.add(exam)

    # Choices
    for letter, (text, is_correct) in (choices or {}).items():
        text = (text or "").strip()
        if text:
            Choice.objects.create(question=q, text=text, is_correct=bool(is_correct))

    # Attach image if matched
    if image_filename and image_files:
        target = os.path.basename(str(image_filename)).lower()
        for fname, fobj in image_files.items():
            if os.path.basename(fname).lower() == target:
                QuestionImage.objects.create(question=q, image=fobj)
                break

    return q


# -----------------------------------------
# PARSE TXT / DOCX / PDF (all text-based formats)
# -----------------------------------------

def parse_txt(text, image_files, subject_name, topic_name):
    print("DEBUG: parse_txt called, length=", len(text or ""))

    lines = [l.rstrip() for l in (text or "").splitlines()]
    i = 0
    source = "google.com"

    ALL_LEVELS = ["VE", "E", "M", "D", "VD"]

    while i < len(lines):
        line = lines[i].strip()

        if not line:
            i += 1
            continue

        # Source line (applies to all following questions)
        if line.startswith("Source:"):
            source = line.replace("Source:", "").strip()
            i += 1
            continue

        # Start of question
        if line.startswith("<Q>"):
            question_text = line.replace("<Q>", "").strip()
            i += 1

            choices = {}
            image_filename = None
            difficulty = "E"
            board_exam_list = []

            # Read until next <Q> or EOF
            while i < len(lines) and not lines[i].strip().startswith("<Q>"):
                l = lines[i].strip()
                if not l:
                    i += 1
                    continue

                # Image line
                if l.startswith("Img:"):
                    image_filename = l.replace("Img:", "").strip()
                    i += 1
                    continue

                # Correct answer >>>X.
                if l.startswith(">>>"):
                    rest = l[3:].lstrip()
                    if rest:
                        letter = rest[0].upper()
                        after = rest[1:].lstrip()
                        if after.startswith("."):
                            after = after[1:].lstrip()
                        choices[letter] = (after, True)
                    i += 1
                    continue

                # Normal choices A. B. C. D. E.
                if len(l) >= 2 and l[1] == ".":
                    letter = l[0].upper()
                    choices[letter] = (l[2:].strip(), False)
                    i += 1
                    continue

                # Difficulty
                if l.upper() in ALL_LEVELS:
                    difficulty = l.upper()
                    i += 1

                    # NEXT LINE IS BOARD EXAM LIST
                    if i < len(lines):
                        be_line = lines[i].strip()
                        if be_line and "," in be_line:  # basic validation
                            board_exam_list = [x.strip() for x in be_line.split(",")]
                            i += 1

                    continue

                i += 1

            # SAVE QUESTION
            save_question(
                question_text=question_text,
                choices=choices,
                image_filename=image_filename,
                level=difficulty,
                source=source,
                subject_name=subject_name,
                topic_name=topic_name,
                board_exam_list=board_exam_list,
                image_files=image_files
            )
            continue

        i += 1



# -----------------------------------------
# PARSE XLSX
# -----------------------------------------

def parse_xlsx(df, image_map=None, subject=None, topic=None):
    """
    Parse an XLSX DataFrame and save all questions to the database using save_question().
    """
    # Normalize column names
    normalized_cols = {"".join(str(c).lower().replace("\xa0","").split()): c for c in df.columns}
    def get_col(name):
        key = "".join(name.lower().replace("\xa0","").split())
        return normalized_cols.get(key, None)

    # Map columns
    q_col = get_col("question")
    a_col = get_col("choicea")
    b_col = get_col("choiceb")
    c_col = get_col("choicec")
    d_col = get_col("choiced")
    e_col = get_col("choicee")
    ans_col = get_col("correctanswer")
    lvl_col = get_col("level")
    img_col = get_col("image")
    src_col = get_col("source")
    be_col = get_col("boardexam")

    print("DEBUG XLSX columns mapping:", normalized_cols)
    print("DEBUG Board Exam column:", be_col)

    for _, row in df.iterrows():
        question_text = str(row.get(q_col, "")).strip() if q_col else ""
        source = str(row.get(src_col, "")).strip() if src_col else "google.com"
        level = str(row.get(lvl_col, "")).strip().upper() if lvl_col else "E"
        image = str(row.get(img_col, "")).strip() if img_col else ""
        if image_map and image in image_map:
            image = image_map[image]

        # Choices
        choices_raw = {
            "A": str(row.get(a_col,"")).strip() if a_col else "",
            "B": str(row.get(b_col,"")).strip() if b_col else "",
            "C": str(row.get(c_col,"")).strip() if c_col else "",
            "D": str(row.get(d_col,"")).strip() if d_col else "",
            "E": str(row.get(e_col,"")).strip() if e_col else "",
        }

        # Correct answer
        correct = str(row.get(ans_col,"")).strip().upper() if ans_col else ""
        choices = {letter: (text, letter==correct) for letter, text in choices_raw.items() if text}

        # Board exams
        board_exam_list = []
        if be_col and pd.notna(row.get(be_col, "")):
            raw_be = str(row[be_col])
            clean_be = re.sub(r"[\s\xa0]+", " ", raw_be)
            parts = [p.strip() for p in clean_be.split(",") if p.strip()]
            board_exam_list = [p.upper() for p in parts]

        # Ensure non-None
        board_exam_list = board_exam_list or []
        choices = choices or {}

        print("DEBUG Question:", question_text[:50])
        print("DEBUG Board Exams:", board_exam_list)
        print("DEBUG Correct Answer:", correct)
        print("DEBUG Choices:", choices)

        # Save the question
        save_question(
            question_text=question_text,
            choices=choices,
            image_filename=image,
            level=level,
            source=source,
            subject_name=subject,
            topic_name=topic,
            board_exam_list=board_exam_list,
            image_files=image_map
        )

# -------------------------------
# UPLOAD VIEW
# -------------------------------
def upload_file(request):
    if request.method == 'POST':
        uploaded_items = request.FILES.getlist('folder_upload')
        subject = request.POST.get('subject')
        topic = request.POST.get('topic')

        main_file = None
        image_map = {}

        # Separate main file and images
        for f in uploaded_items:
            ext = os.path.splitext(f.name)[1].lower()
            if ext in ['.docx', '.pdf', '.txt', '.xlsx']:
                main_file = f
            elif ext in ['.jpg', '.jpeg', '.png']:
                image_map[os.path.basename(f.name)] = f

        if not main_file:
            return HttpResponse("<script>alert('No main file found!');</script>")

        ext = os.path.splitext(main_file.name)[1].lower()

        try:
            if ext == '.pdf':
                text = extract_pdf_text(main_file)
                parse_txt(text, image_map, subject, topic)
            elif ext == '.docx':
                text = extract_text_from_docx(main_file)
                parse_txt(text, image_map, subject, topic)
            elif ext == '.txt':
                text = extract_text_from_txt(main_file)
                parse_txt(text, image_map, subject, topic)
            elif ext == '.xlsx':
                df = pd.read_excel(main_file)
                parse_and_save_xlsx(df, image_map=image_map, subject=subject, topic=topic)
            else:
                return HttpResponse("<script>alert('Invalid file type.');</script>")

        except Exception as e:
            print("ERROR:", e)
            return HttpResponse(f"<script>alert('Error: {str(e)}');</script>")

        # Redirect safely to question bank page
        from django.urls import reverse
        redirect_url = reverse('question_bank')  # replace with your URL name
        return redirect(redirect_url)

    # GET request – render upload page
    context = {
        'BOARD_EXAMS': list(BOARD_EXAM_TOPICS.keys()),
        'BOARD_EXAM_TOPICS_JSON': json.dumps(BOARD_EXAM_TOPICS),
        'LEVELS_JSON': json.dumps(LEVELS),
    }
    return render(request, 'upload_file.html', context)


####################### FOR UPLOADING AND CHECKING OF ANSWER SHEET (IMAGE) ##############################

def get_exam_id_suggestions(request):
    input_text = request.GET.get('input', '')

    # Filter AnswerKey objects based on partial match of input_text
    suggestions = AnswerKey.objects.filter(set_id__icontains=input_text).values_list('set_id', flat=True)

    return JsonResponse(list(suggestions), safe=False)

def get_subjects(request):
    subjects = TestKey.objects.values_list('subject', flat=True).distinct()
    return JsonResponse({'subjects': list(subjects)})

def get_testkeys_by_subject(request):
    subject = request.GET.get('subject')
    testkeys = []
    if subject:
        testkeys = list(
            AnswerKey.objects.filter(subject=subject)
            .values_list('set_id', flat=True)
        )
    return JsonResponse({'testkeys': testkeys})

def download_answer_page(request):
    return render(request, 'download_answer_key.html')

def download_exam_results_page(request):
    return render(request, 'download_exam_results.html')

def get_exam_dates_by_board_exam(request):
    board_exam = request.GET.get('board_exam')
    dates = TestKey.objects.filter(board_exam=board_exam).values_list('exam_date', flat=True).distinct()
    # Convert to MMMM-YYYY
    formatted_dates = [d.strftime("%B-%Y") for d in dates]
    return JsonResponse({'dates': formatted_dates})

def get_subjects_by_board_exam_and_date(request):
    board_exam = request.GET.get('board_exam')
    exam_date = request.GET.get('exam_date')

    month, year = exam_date.split('-')
    month_num = datetime.strptime(month, "%B").month

    subjects = (
        TestKey.objects
        .filter(
            board_exam=board_exam,
            exam_date__month=month_num,
            exam_date__year=int(year)
        )
        .values_list('subject', flat=True)
        .distinct()
    )

    return JsonResponse({"subjects": list(subjects)})


def view_answer_key(request):
    exam_id = request.GET.get('exam_id')
    answer_key = get_object_or_404(AnswerKey, set_id=exam_id)

    return render(request, 'view_answer_key.html', {
        'exam_id': exam_id,
        'answer_key': answer_key.answer_key
    })

def download_answer_key(request):
    exam_id = request.GET.get('exam_id', None)

    if exam_id is None:
        return JsonResponse({'error': 'Exam ID is required'})

    answer_key = AnswerKey.objects.filter(set_id=exam_id).first()

    if answer_key is None:
        return JsonResponse({'error': 'Answer key not found for the provided exam ID'})

    # Generate file name
    file_name = f'answer_key_{exam_id}.txt'

    # Create readable text format
    answer_key_str = (
        f"Board Exam/Course: {answer_key.board_exam}\n"
        f"Subject: {answer_key.subject}\n"
        # f"Topic: {answer_key.topic}\n"
        f"Test Key: {answer_key.set_id}\n"
        f"{'-'*40}\n"
        + '\n'.join([f'{key}: {value}' for key, value in answer_key.answer_key.items()])
    )

    # Return as downloadable text file
    response = HttpResponse(answer_key_str, content_type='text/plain')
    response['Content-Disposition'] = f'attachment; filename="{file_name}"'
    return response


# Get distinct board exams
def get_board_exams(request):
    exams = list(BoardExam.objects.values_list('name', flat=True))
    return JsonResponse({'board_exams': exams})


# Get distinct subjects by board exam
def get_subjects_by_board_exam(request):
    board_exam = request.GET.get('board_exam')
    subjects = []
    if board_exam:
        subjects = list(
            Question.objects.filter(board_exams__name=board_exam)
            .values_list('subject__name', flat=True)
            .distinct()
        )
    return JsonResponse({'subjects': subjects})


# Get distinct topics by subject
def get_topics_by_subject(request):
    subject = request.GET.get('subject')
    topics = []
    if subject:
        topics = list(
            Question.objects.filter(subject=subject)
            .values_list('topic', flat=True)
            .distinct()
        )
    return JsonResponse({'topics': topics})


# Get test keys by topic (from AnswerKey)
def get_testkeys_by_topic(request):
    topic = request.GET.get('topic')
    testkeys = []
    if topic:
        # If your AnswerKey has 'subject' field, we can match it to Question.subject of this topic
        subject = Question.objects.values_list('subject', flat=True).first()
        if subject:
            testkeys = list(
                AnswerKey.objects.filter(subject=subject)
                .values_list('set_id', flat=True)
            )
    return JsonResponse({'testkeys': testkeys})

def download_exam_results(request):
    subject = request.GET.get('subject')
    exam_date = request.GET.get('exam_date')

    if not subject or not exam_date:
        return JsonResponse({'error': 'Subject and exam date are required'})

    try:
        month, year = exam_date.split('-')
        month_num = datetime.strptime(month, "%B").month
        year = int(year)
    except ValueError:
        return JsonResponse({'error': 'Invalid exam date format'})

    # 🔹 Get all SET IDs for same subject + date
    exam_ids = TestKey.objects.filter(
        subject=subject,
        exam_date__month=month_num,
        exam_date__year=year
    ).values_list('set_id', flat=True)

    if not exam_ids.exists():
        return JsonResponse({'error': 'No exams found for this subject/date'})

    # 🔹 Merge results across all sets
    results = Result.objects.filter(
        exam_id__in=exam_ids
    ).order_by('student_name')

    if not results.exists():
        return JsonResponse({'message': 'No results yet for this subject/date.'})

    # 🔹 Board exam (take from TestKey)
    board_exam = TestKey.objects.filter(set_id__in=exam_ids).first().board_exam

    # ================== EXCEL GENERATION ==================
    wb = Workbook()
    ws = wb.active
    ws.title = f"{subject} Results"

    ws["A1"] = "Board Exam:"
    ws["B1"] = board_exam
    ws["A2"] = "Subject:"
    ws["B2"] = subject
    ws["A3"] = "Exam Date:"
    ws["B3"] = exam_date

    ws.append([])
    ws.append(["Student Name", "Score", "Exam Set"])

    bold_font = Font(bold=True)
    center_align = Alignment(horizontal="center", vertical="center")
    header_fill = PatternFill(start_color="B7DEE8", end_color="B7DEE8", fill_type="solid")
    thin_border = Border(
        left=Side(style="thin"), right=Side(style="thin"),
        top=Side(style="thin"), bottom=Side(style="thin")
    )

    for cell in ws[5]:
        cell.font = bold_font
        cell.alignment = center_align
        cell.fill = header_fill
        cell.border = thin_border

    # 🔹 Data rows
    for result in results:
        ws.append([
            result.student_name,
            result.score,
            result.exam_id   # optional but useful
        ])

    # Styling
    for row in ws.iter_rows(min_row=6, max_row=ws.max_row, min_col=1, max_col=3):
        for cell in row:
            cell.border = thin_border
            cell.alignment = Alignment(vertical="center")

    # Auto-width
    for col in ws.columns:
        max_length = max(len(str(cell.value)) if cell.value else 0 for cell in col)
        ws.column_dimensions[col[0].column_letter].width = max_length + 2

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    filename = f"Results_for_{board_exam}_Board_Exam-{subject}-{exam_date}.xlsx"
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    wb.save(response)

    return response



def image_to_mask(image):
    # Convert image to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Apply adaptive thresholding
    _, mask = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    
    # Apply morphological operations to clean up the mask
    kernel_size = (2, 2)
    kernel = np.ones(kernel_size, np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    
    return mask

def upload_answer(request):
    if request.method == 'POST' and request.FILES['image']:
        # Handle the uploaded image
        uploaded_image = request.FILES['image']
        # Extract exam_id from the POST request
        exam_id = request.POST.get('exam_id')
        # Retrieve the answer key from the database using exam_id
        answer_key = get_object_or_404(AnswerKey, set_id=exam_id)
        subject = answer_key.subject
        # Read the uploaded image using OpenCV
        # nparr = np.fromstring(uploaded_image.read(), np.uint8)
        nparr = np.frombuffer(uploaded_image.read(), np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Convert image to mask using image_to_mask function
        mask = image_to_mask(image)

        # Save the mask as an image
        # cv2.imwrite('mask.jpg', mask)
        
        # Generate a unique filename for the mask image using timestamp and UUID
        unique_filename = f'mask_{int(time.time())}_{uuid.uuid4()}.jpg'

        # Create the directory if it doesn't exist
        directory = os.path.join('media', 'mask_images')

        if not os.path.exists(directory):
            os.makedirs(directory)

        # Save the mask as an image with the unique filename
        cv2.imwrite(os.path.join(directory, unique_filename), mask)
        # Specify the path to YOLOv4 models and class names files
        model1_weights_path = "model1/model1.weights"
        model1_cfg_path = "model1/model1.cfg"
        model1_names_path = "model1/model1.names"

        model2_weights_path = "model2/model2.weights"
        model2_cfg_path = "model2/model2.cfg"
        model2_names_path = "model2/model2.names"

        # Load YOLOv4 models and class names
        net_original = cv2.dnn.readNet(model1_weights_path, model1_cfg_path)
        classes_original = []
        with open(model1_names_path, "r") as f:
            classes_original = [line.strip() for line in f.readlines()]

        net_cropped = cv2.dnn.readNet(model2_weights_path, model2_cfg_path)
        classes_cropped = []
        with open(model2_names_path, "r") as f:
            classes_cropped = [line.strip() for line in f.readlines()]

        # Specify the reference point from which to measure the distance
        reference_point = (0, 0)  # Example point, you should specify your desired point here

        # mask_image = cv2.imread('mask.jpg')
        mask_image = cv2.imread(os.path.join('media', 'mask_images', unique_filename))

        # Perform object detection with the first model
        boxes_original, _, class_ids_original = detect_objects(mask_image, net_original, classes_original)

        # Crop detected objects and perform detection with the second model
        for i, box in enumerate(boxes_original):
            x, y, w, h = box
            cropped_object = mask_image[y:y+h, x:x+w]

            # Get the class name corresponding to the detected object
            class_name_original = classes_original[class_ids_original[i]]

            # Check if class name is 'answer'
            if class_name_original == 'answer':
                # Perform object detection with the second model
                boxes_cropped, _, class_ids_cropped = detect_objects(cropped_object, net_cropped, classes_cropped)

                # Sort detected objects by distance from the reference point
                object_dict = sort_objects_by_distance(boxes_cropped, class_ids_cropped, classes_cropped, reference_point)

                # Group and assign sequence numbers to the detected objects
                grouped_boxes = group_and_sequence(object_dict.values(), object_dict.keys())

                # Create a dictionary to store seq_num:class pairs
                seq_num_class_dict = {}

                # Display the cropped object with bounding boxes, class labels, and reference point
                for seq_num, i in grouped_boxes.items():
                    # Find the corresponding box coordinates for the class
                    box = boxes_cropped[i - 1]  # Subtract 1 since sequence numbers start from 1
                    x, y, w, h = box

                    # Draw bounding box
                    cv2.rectangle(cropped_object, (x, y), (x+w, y+h), (0, 255, 0), 2)

                    # Put class label above the bounding box
                    cv2.putText(cropped_object, f"{seq_num}:{classes_cropped[class_ids_cropped[i - 1]]}", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

                    # Find the corresponding class name using the class ID
                    class_name = classes_cropped[class_ids_cropped[i - 1]]  # Subtract 1 since sequence numbers start from 1
                    seq_num_class_dict[seq_num] = class_name

                    # Draw reference point
                    cv2.circle(cropped_object, reference_point, 5, (255, 0, 0), -1)

                correct_answers = {str(k): v['letter'] for k, v in answer_key.answer_key.items()}
                submitted_answers = seq_num_class_dict.values()

                # # Calculate the score based on similarities between correct and submitted answers
                # score = sum(correct_answer == submitted_answer for correct_answer, submitted_answer in zip(correct_answers.values(), submitted_answers))

                # Calculate score
                score = 0
                comparison_results = {}
                for seq_num, submitted_answer in seq_num_class_dict.items():
                    correct_answer = correct_answers.get(str(seq_num))
                   
                    if correct_answer is not None:
                        is_correct = submitted_answer == correct_answer
                        comparison_results[seq_num] = {'submitted_answer': submitted_answer, 'correct_answer': correct_answer, 'is_correct': is_correct}
                        if is_correct:
                            score += 1

                # Get the user_id from the request
                user_id = request.user
                print("User ID:", user_id)

                # Get the student corresponding to the user_id
                student = get_object_or_404(Student, user_id=user_id)
                print("Student:", student)
                print("Subject:", subject)
                existing_results = Result.objects.filter(user=user_id)
                print("Existing Results for User:", existing_results)
                if Result.objects.filter(user=user_id, exam_id=exam_id).exists():
                    # If a Result entry already exists for the user and exam_id, return a warning message
                    return JsonResponse({'warning': 'An answer is already uploaded for this user and exam ID'})
                else: 
                    try:
                        # Create a Result object and save it
                        result = Result.objects.create(
                            user = user_id,
                            student_id=student.student_id,
                            course=student.course,
                            student_name = student,
                            subject= subject,  # Replace "Your subject" with the subject name
                            exam_id=exam_id,
                            # answer=list(submitted_answers),
                            answer = [seq_num_class_dict[k] for k in sorted(seq_num_class_dict.keys())],
                            correct_answer=list(correct_answers.values()),
                            score=score,
                            is_submitted=True
                        )
                        print("Result:", result)  # Debug statement

                    except IntegrityError:
                        # If IntegrityError occurs (duplicate key), return a warning message
                        return JsonResponse({'warning': 'An answer is already uploaded for this user and exam ID'})

                    return JsonResponse({'score': score})  # Return an HttpResponse with the score

        # If no 'answer' class is detected
        return JsonResponse({'error': 'No answer class detected in the image'})

    else:
        return render(request, 'upload_answer.html')

def answer_sheet_view(request):
    if request.method == 'POST':
        form = AnswerSheetForm(request.POST)
        if form.is_valid():
            # Process the form data and save it to the database
            # Redirect to a success page or render a confirmation message
            pass  # Placeholder for processing form data
    else:
        form = AnswerSheetForm()
    return render(request, 'answer_sheet.html', {'form': form})

def online_answer_test(request):
    if request.method != 'POST':
        return render(request, 'answer_test_form.html')

    subject = request.POST.get('subject')
    board_exam = request.POST.get('board_exam')

    set_a_id = f"{board_exam}_{uuid.uuid4().hex[:8]}"
    set_b_id = f"{board_exam}_{uuid.uuid4().hex[:8]}"

    set_a_question_ids = request.POST.getlist('set_a_question_ids[]')
    set_b_question_ids = request.POST.getlist('set_b_question_ids[]')

    # Build questions and answer keys using existing helpers
    questions_set_a = get_questions_with_choices(set_a_question_ids)
    questions_set_b = get_questions_with_choices(set_b_question_ids)

    set_a_answer_key = build_answer_key(set_a_question_ids)
    set_b_answer_key = build_answer_key(set_b_question_ids)

    set_a_choice_map = extract_choices_by_letter(questions_set_a)
    set_b_choice_map = extract_choices_by_letter(questions_set_b)

    # Save TestKey & AnswerKey
    if not TestKey.objects.filter(set_id=set_a_id).exists():
        TestKey.objects.create(
            set_id=set_a_id,
            board_exam=board_exam,
            subject=subject,
            questions=questions_set_a,
            choiceA=set_a_choice_map['A'],
            choiceB=set_a_choice_map['B'],
            choiceC=set_a_choice_map['C'],
            choiceD=set_a_choice_map['D'],
            choiceE=set_a_choice_map['E']
        )
        AnswerKey.objects.create(
            set_id=set_a_id,
            board_exam=board_exam,
            subject=subject,
            answer_key=set_a_answer_key
        )

    if not TestKey.objects.filter(set_id=set_b_id).exists():
        TestKey.objects.create(
            set_id=set_b_id,
            board_exam=board_exam,
            subject=subject,
            questions=questions_set_b,
            choiceA=set_b_choice_map['A'],
            choiceB=set_b_choice_map['B'],
            choiceC=set_b_choice_map['C'],
            choiceD=set_b_choice_map['D'],
            choiceE=set_b_choice_map['E']
        )
        AnswerKey.objects.create(
            set_id=set_b_id,
            board_exam=board_exam,
            subject=subject,
            answer_key=set_b_answer_key
        )

    # Prepare questions for preview (optional)
    set_a_questions_choices = questions_set_a
    set_b_questions_choices = questions_set_b

    return render(request, 'answer_test.html', {
        'subject': subject,
        'board_exam': board_exam,
        'set_a_questions_choices': set_a_questions_choices,
        'set_b_questions_choices': set_b_questions_choices,
        'set_a_id': set_a_id,
        'set_b_id': set_b_id,
    })



def answer_test_preview(request, subject, board_exam, set_a_id, set_b_id):
    test_a = TestKey.objects.get(set_id=set_a_id)
    test_b = TestKey.objects.get(set_id=set_b_id)

    answer_a = AnswerKey.objects.get(set_id=set_a_id)
    answer_b = AnswerKey.objects.get(set_id=set_b_id)

    return render(request, 'answer_test.html', {
        'subject': subject,
        'board_exam': board_exam,
        'test_a': test_a,
        'test_b': test_b,
        'answer_a': answer_a,
        'answer_b': answer_b,
    })


####################### FOR ANSWERING ONLINE ##############################

import random

def answer_online_exam(request):
    testkeys = TestKey.objects.all()
    data = {}

    for tk in testkeys:
        board = tk.board_exam
        exam_date = tk.exam_date
        month_key = exam_date.strftime("%Y-%m")
        subject = tk.subject

        # Initialize dicts
        data.setdefault(board, {})
        data[board].setdefault(month_key, {})

        if subject not in data[board][month_key]:
            # Get all sets for this board, subject, and month
            sets_for_subject = TestKey.objects.filter(
                board_exam=board,
                subject=subject,
                exam_date__year=exam_date.year,
                exam_date__month=exam_date.month
            )
            random_set = random.choice(list(sets_for_subject))
            data[board][month_key][subject] = {
                "set_id": random_set.set_id,
                "subject_group": random_set.subject_group
            }

    return render(
        request,
        "answer_online_exam.html",
        {
            "board_exams": data.keys(),
            "exam_data_json": json.dumps(data),
        }
    )

from django.utils.dateparse import parse_datetime

def exam_form(request, set_id):
    test_key = get_object_or_404(TestKey, set_id=set_id)
    student = get_object_or_404(Student, user=request.user)

    # ===============================
    # ACCESS CONTROL
    # ===============================
    student_course = student.course.strip().lower()
    exam_code = test_key.board_exam.strip().upper()

    if "civil engineering" in student_course:
        allowed_exam = "CE"
    elif "mechanical engineering" in student_course:
        allowed_exam = "ME"
    elif "electrical engineering" in student_course:
        allowed_exam = "EE"
    elif "electronics engineering" in student_course:
        allowed_exam = "ECE"
    else:
        allowed_exam = None

    if allowed_exam != exam_code:
        messages.error(request, "You are not allowed to access this exam.")
        return redirect("answer_online_exam")

    # ===============================
    # PREVENT DOUBLE SUBMISSION
    # ===============================
    result = Result.objects.filter(user=request.user, subject=test_key.subject).first()

    if result and result.is_submitted:
        messages.error(request, "You have already submitted this subject.")
        return redirect("warning_page")

    # reset session flag only if no result exists
    if not result:
        request.session.pop("form_submitted", None)

    # ===============================
    # PREPARE QUESTIONS
    # ===============================
    question_choices = []
    letters = list(string.ascii_uppercase)[:5]  # A–E

    for i, question in enumerate(test_key.questions):
        question_text = question.get("question_text") or question.get("question")
        image_url = question.get("image_url") or question.get("image") or ""

        choice_texts = [
            test_key.choiceA[i],
            test_key.choiceB[i],
            test_key.choiceC[i],
            test_key.choiceD[i],
            test_key.choiceE[i],
        ]

        random.shuffle(choice_texts)
        choices = list(zip(letters, choice_texts))
        question_choices.append((question_text, choices, image_url))

    total_items = len(question_choices)

    MAX_ITEMS = 100
    MAX_TIME_SECONDS = 4 * 60 * 60
    total_time_limit = int((total_items / MAX_ITEMS) * MAX_TIME_SECONDS)
    per_question_time_limit = total_time_limit / max(total_items, 1)

    # ===============================
    # POST: SUBMIT EXAM
    # ===============================
    if request.method == "POST":

        if request.session.get("form_submitted"):
            messages.error(request, "You have already submitted this exam.")
            return redirect("warning_page")

        # -------- Collect answers --------
        submitted_answers = []
        for i in range(total_items):
            ans = request.POST.get(f"question_{i + 1}")
            if not ans:
                messages.error(
                    request, f"Please select an answer for question {i + 1}."
                )
                return render(
                    request,
                    "exam_form.html",
                    {
                        "test_key": test_key,
                        "question_choices": question_choices,
                        "total_items": total_items,
                        "total_time_limit": total_time_limit,
                        "per_question_time_limit": per_question_time_limit,
                        "start_time": timezone.now().isoformat(),
                    },
                )
            submitted_answers.append(ans)

        # -------- Elapsed time (FIXED) --------
        elapsed_time = None
        start_time_str = request.POST.get("start_time")

        if start_time_str:
            start_time = parse_datetime(start_time_str)
            if start_time and timezone.is_naive(start_time):
                start_time = timezone.make_aware(start_time)

            if start_time:
                elapsed_td = timezone.now() - start_time
                h, r = divmod(int(elapsed_td.total_seconds()), 3600)
                m, s = divmod(r, 60)
                elapsed_time = f"{h}hr {m}min {s}sec"

        # mark session submitted
        request.session["form_submitted"] = True

        # -------- Scoring --------
        score = 0
        answer_key = get_object_or_404(AnswerKey, set_id=set_id)
        answer_key_dict = answer_key.answer_key

        correct_text_answers = []

        for i, key in enumerate(sorted(answer_key_dict.keys(), key=int)):
            correct_text = answer_key_dict[key].get("text", "")
            correct_text_answers.append(correct_text)

            if submitted_answers[i] == correct_text:
                score += 1

        # -------- Save result --------
        try:
            result = Result.objects.create(
                user=request.user,
                student_id=student.student_id,
                course=student.course,
                student_name=str(student),
                subject=test_key.subject,
                exam_id=set_id,
                answer=submitted_answers,
                correct_answer=correct_text_answers,
                score=score,
                total_items=total_items,
                is_submitted=True,
                timestamp=timezone.now(),
                elapsed_time=elapsed_time,
            )

            return redirect("result_page", result_id=result.id)

        except IntegrityError:
            messages.error(request, "There was an error saving your result.")
            return redirect("warning_page")

    # ===============================
    # GET REQUEST
    # ===============================
    return render(
        request,
        "exam_form.html",
        {
            "test_key": test_key,
            "question_choices": question_choices,
            "total_items": total_items,
            "total_time_limit": total_time_limit,
            "per_question_time_limit": per_question_time_limit,
            "start_time": timezone.now().isoformat(),
        },
    )



def result_page(request, result_id):
    result = Result.objects.get(id=result_id)
    percent = 0
    if result.total_items:
        percent = round((result.score / result.total_items) * 100, 2)
    return render(request, 'result_page.html', {
        'result': result,
        'percent': percent
    })


def warning_page(request):
    home_student_url = reverse('home_student')  # Assuming 'home_student' is the name of the URL pattern for home_student.html
    return render(request, 'submit_warning.html', {'home_student_url': home_student_url})

@login_required
def view_results(request):
    # Get the results for the logged-in user only
    user_results = Result.objects.filter(user=request.user).order_by('-timestamp')
    return render(request, 'view_results.html', {'results': user_results})

def question_analytics(request):
    # Fetch all questions with related data
    questions = Question.objects.prefetch_related('board_exams').select_related('subject', 'difficulty')

    board_exam_counts = {}
    subject_counts = {}
    difficulty_counts = {}

    for q in questions:
        board_exams = list(q.board_exams.all())
        if not board_exams:
            board_exams = [None]  # handle questions with no board exam

        for be in board_exams:
            be_name = be.name if be else "No Board Exam"
            board_exam_counts[be_name] = board_exam_counts.get(be_name, 0) + 1

            subject_name = q.subject.name if q.subject else "Unknown Subject"
            key = (be_name, subject_name)
            subject_counts[key] = subject_counts.get(key, 0) + 1

        difficulty_name = q.difficulty.level if q.difficulty else "Unknown Difficulty"
        difficulty_counts[difficulty_name] = difficulty_counts.get(difficulty_name, 0) + 1

    # Convert dicts into list of dicts for template
    course_stats = [{"board_exam": k, "total": v} for k, v in board_exam_counts.items()]
    subject_distribution = [
        {"board_exam": be, "subject": subj, "total_questions": count}
        for (be, subj), count in subject_counts.items()
    ]

    # Chart data
    course_labels = list(board_exam_counts.keys())
    total_questions = list(board_exam_counts.values())

    difficulty_labels = list(difficulty_counts.keys())
    difficulty_values = list(difficulty_counts.values())

    context = {
        "course_stats": course_stats,
        "subject_distribution": subject_distribution,
        "course_labels": json.dumps(course_labels),
        "total_questions": json.dumps(total_questions),
        "difficulty_labels": json.dumps(difficulty_labels),
        "difficulty_counts": json.dumps(difficulty_values),
    }

    return render(request, "question_analytics.html", context)

def test_analytics(request):
    results = Result.objects.all()
    courses = results.values_list('course', flat=True).distinct()
    course_data = {}

    for course in courses:
        course_results = results.filter(course=course)

        # Pass/Fail
        passed_counts = course_results.filter(score__gte=0.6 * F('total_items')).count()
        failed_counts = course_results.filter(score__lt=0.6 * F('total_items')).count()

        # Average score
        avg_score = course_results.aggregate(avg=Avg('score'))['avg'] or 0

        # Per question correct/wrong
        question_stats = defaultdict(lambda: {'correct': 0, 'wrong': 0})
        for r in course_results:
            answers = r.answer or []
            correct_answers = r.correct_answer or []
            for idx, ans in enumerate(answers):
                correct_ans = correct_answers[idx] if idx < len(correct_answers) else None
                if ans == correct_ans:
                    question_stats[idx]['correct'] += 1
                else:
                    question_stats[idx]['wrong'] += 1

        question_labels = [f'Q{i+1}' for i in range(len(question_stats))]
        correct_counts = [question_stats[i]['correct'] for i in range(len(question_stats))]
        wrong_counts = [question_stats[i]['wrong'] for i in range(len(question_stats))]

        # Top students
        top_students = course_results.order_by('-score')[:10]

        # Pre-serialize JSON for template
        passed_json = json.dumps({"passed": passed_counts, "failed": failed_counts})
        avg_json = json.dumps({"avg": avg_score})
        question_json = json.dumps({"labels": question_labels, "correct": correct_counts, "wrong": wrong_counts})

        course_data[course] = {
            'passed_counts': passed_counts,
            'failed_counts': failed_counts,
            'avg_score': avg_score,
            'question_labels': question_labels,
            'correct_counts': correct_counts,
            'wrong_counts': wrong_counts,
            'top_students': top_students,
            'passed_json': passed_json,
            'avg_json': avg_json,
            'question_json': question_json
        }

    return render(request, 'test_analytics.html', {'course_data': course_data})

# ---- Practice: start ----
@require_http_methods(["GET", "POST"])
def practice_start(request):
    # 1. Map student's course to exam code
    student_course_full = request.user.student.course.strip().lower()

    course_mapping = {
        "civil engineering": "CE",
        "mechanical engineering": "ME",
        "electrical engineering": "EE",
        "electronics engineering": "ECE",
    }

    student_course_code = course_mapping.get(student_course_full)
    if not student_course_code:
        messages.error(request, "Your course is not supported for practice exams.")
        return redirect("home")  # Or any page

    # 2. Load subjects for this course only

    subjects = list(BOARD_EXAM_TOPICS.get(student_course_code, {}).keys())


    if request.method == "POST":
        subject_name = request.POST.get("subject")

        try:
            num_items = int(request.POST.get("num_items") or 5)
        except ValueError:
            num_items = 5

        # Filter questions for the student's mapped course + chosen subject
        qs = Question.objects.filter(
            board_exams__name=student_course_code,
            subjects__name=subject_name
        ).distinct()


        if not qs.exists():
            messages.error(request, "No questions found for this subject!")
            return redirect("practice_start")

        available = qs.count()
        if num_items > available:
            messages.error(request, f"You selected {num_items} but only {available} questions exist!")
            return redirect("practice_start")

        # Random selection
        questions = list(qs)
        random.shuffle(questions)
        chosen = questions[:num_items]

        payload = []
        for q in chosen:
            payload.append({
                'id': q.id,
                'text': q.question_text,
                'image_url': q.images.first().image.url if q.images.exists() else None,
                'choices': [
                    {"key": c.id, "text": c.text, "is_correct": c.is_correct} for c in q.choices.all()
                ],
                "correct": next((c.text for c in q.choices.all() if c.is_correct), None),
            })

        session_id = str(uuid.uuid4())
        request.session[f"practice_{session_id}"] = {
            "board_exam": student_course_code,
            "subject": subject_name,
            "questions": payload,
            "total_items": len(payload),
        }
        request.session.modified = True

        return redirect('practice_take', session_id=session_id)

    return render(request, "practice_start.html", {
        "subjects": subjects,
        "student_course": student_course_code,
    })




# ---- Practice: take (render questions + timer) ----
def practice_take(request, session_id):
    sess_key = f'practice_{session_id}'
    data = request.session.get(sess_key)
    if not data:
        messages.error(request, "Practice session not found or expired.")
        return redirect('practice_start')

    # pass questions without exposing 'correct' on client (we'll keep a server copy)
    letters = list(string.ascii_uppercase)  # ['A','B','C','D',...]

    questions_for_client = []
    for qi, q in enumerate(data['questions'], start=1):
        choices = q['choices'].copy()
        random.shuffle(choices)
        for idx, choice in enumerate(choices):
            choice['display_letter'] = letters[idx]
        questions_for_client.append({
            'instance_id': qi,
            'q_id': q['id'],
            'text': q['text'],
            'image_url': q['image_url'],
            'choices': choices
        })

    context = {
        'session_id': session_id,
        'board_exam': data['board_exam'],
        'questions': questions_for_client,
        'total_items': data['total_items'],
        'total_time_limit': data.get('total_time_limit'),
        'per_question_time_limit': data.get('per_question_time_limit'),
    }
    return render(request, 'practice_take.html', context)



# ---- Practice: submit (grade & analytics) ----
@require_http_methods(["POST"])
def practice_submit(request, session_id):
    sess_key = f'practice_{session_id}'
    data = request.session.get(sess_key)
    if not data:
        messages.error(request, "Practice session not found or expired.")
        return redirect('practice_start')

    questions = data['questions']
    total_items = len(questions)
    results = []
    correct_count = 0
    total_time_elapsed = 0.0

    # ---- Analytics temporary containers ----
    subject_tracker = {}   # {subject: {"correct": x, "total": y, "time": seconds}}
    topic_tracker = {}     # {topic: {"correct": x, "total": y, "time": seconds}}
    difficulty_tracker = {}  # {difficulty: {"correct": x, "total": y}}
    # -----------------------------------------

    for i, q in enumerate(questions, start=1):
        ans = request.POST.get(f'answer_{i}')
        time_spent = float(request.POST.get(f'time_{i}', '0') or 0)

        correct_key = q['correct']
        is_correct = (ans == correct_key)

        # Fetch real question object
        q_obj = Question.objects.get(id=q['id'])
        subject = q_obj.subjects.first().name if q_obj.subjects.exists() else "Unknown"
        topic = q_obj.topic.name if q_obj.topic else "Misc"
        difficulty = q_obj.difficulty.level if q_obj.difficulty else "Unknown"

        # ------- Subject Tracker -------
        if subject not in subject_tracker:
            subject_tracker[subject] = {"correct": 0, "total": 0, "time": 0}
        subject_tracker[subject]["total"] += 1
        subject_tracker[subject]["time"] += time_spent
        if is_correct:
            subject_tracker[subject]["correct"] += 1

        # ------- Topic Tracker -------
        if topic not in topic_tracker:
            topic_tracker[topic] = {"correct": 0, "total": 0, "time": 0, "subject": subject}
        topic_tracker[topic]["total"] += 1
        topic_tracker[topic]["time"] += time_spent
        if is_correct:
            topic_tracker[topic]["correct"] += 1

        # ------- Difficulty Tracker -------
        if difficulty not in difficulty_tracker:
            difficulty_tracker[difficulty] = {"correct": 0, "total": 0}
        difficulty_tracker[difficulty]["total"] += 1
        if is_correct:
            difficulty_tracker[difficulty]["correct"] += 1

        # Count correct answers
        if is_correct:
            correct_count += 1

        total_time_elapsed += time_spent

        results.append({
            'index': i,
            'q_id': q['id'],
            'text': q['text'],
            'image_url': q.get('image_url'),
            'selected': ans,
            'correct': correct_key,
            'is_correct': is_correct,
            'time_spent': time_spent,
        })

    # Final score
    score = correct_count
    pct = (score / total_items * 100) if total_items else 0

    # ---- Update SUBJECT ANALYTICS with weighted average ----
    for subject, stats in subject_tracker.items():
        obj, _ = SubjectAnalytics.objects.get_or_create(
            user=request.user,
            subject=subject,
            board_exam=data['board_exam']
        )

        # Weighted average time calculation
        total_prev_time = obj.average_time_per_item * obj.total_items_answered
        total_new_time = total_prev_time + stats["time"]
        obj.total_items_answered += stats["total"]
        obj.total_correct += stats["correct"]
        obj.total_attempts += 1
        obj.average_time_per_item = total_new_time / obj.total_items_answered

        obj.save()

    # ---- Update TOPIC ANALYTICS with weighted average ----
    for topic, stats in topic_tracker.items():
        obj, _ = TopicAnalytics.objects.get_or_create(
            user=request.user,
            subject=stats["subject"],  # use correct subject
            topic=topic
        )

        total_prev_time = obj.average_time_per_item * obj.total_items_answered
        total_new_time = total_prev_time + stats["time"]
        obj.total_items_answered += stats["total"]
        obj.total_correct += stats["correct"]
        obj.average_time_per_item = total_new_time / obj.total_items_answered

        obj.save()

    # ---- Update DIFFICULTY ANALYTICS ----
    for difficulty, stats in difficulty_tracker.items():
        obj, _ = DifficultyAnalytics.objects.get_or_create(
            user=request.user,
            board_exam=data['board_exam'],
            difficulty=difficulty
        )
        obj.total_items_answered += stats["total"]
        obj.total_correct += stats["correct"]
        obj.save()

    # ---- Save raw practice result ----
    PracticeResult.objects.create(
        session_id=session_id,
        user=request.user,
        board_exam=data['board_exam'],
        total_items=total_items,
        score=score,
        percent=pct,
        total_time=total_time_elapsed,
        answers=results
    )

    # Keep results in session
    request.session[f'practice_result_{session_id}'] = {
        'score': score,
        'total_items': total_items,
        'percent': pct,
        'results': results,
        'total_time': total_time_elapsed,
        'board_exam': data['board_exam'],
        'created_at': timezone.now().isoformat(),
    }
    request.session.modified = True

    return redirect('practice_result_page', session_id=session_id)


def practice_result_page(request, session_id):
    res = request.session.get(f'practice_result_{session_id}')
    if not res:
        messages.error(request, "No practice results found for that session.")
        return redirect('practice_start')
    return render(request, 'practice_result.html', {'res': res})

from django.core.serializers.json import DjangoJSONEncoder

@login_required
def analytics_dashboard(request):
    user = request.user
    results = PracticeResult.objects.filter(user=user)

    # Temporary containers
    subject_data = {}
    topic_data = {}
    difficulty_data = {}

    for res in results:
        board_exam = res.board_exam  # e.g., "ECE", "EE"

        for ans in res.answers:
            q_id = ans['q_id']
            selected = ans['selected']
            correct = ans['correct']
            time_spent = ans.get('time_spent', 0.0)

            # Fetch question object
            try:
                q = Question.objects.get(id=q_id)
            except Question.DoesNotExist:
                continue

            # --- Pick subject that matches this board exam ---
            subject = "Unknown"
            for subj in q.subjects.all():
                if subj.name in BOARD_EXAM_TOPICS.get(board_exam, {}):
                    subject = subj.name
                    break

            topic = q.topic.name if q.topic else "Misc"
            difficulty = q.difficulty.level if q.difficulty else "Unknown"

            # --- SUBJECT ---
            key = (subject, board_exam)
            if key not in subject_data:
                subject_data[key] = {
                    'total_items_answered': 0,
                    'total_correct': 0,
                    'total_time': 0.0,
                }
            subject_data[key]['total_items_answered'] += 1
            subject_data[key]['total_correct'] += int(selected == correct)
            subject_data[key]['total_time'] += time_spent

            # --- TOPIC ---
            key_topic = (topic, subject)
            if key_topic not in topic_data:
                topic_data[key_topic] = {
                    'total_items_answered': 0,
                    'total_correct': 0,
                    'total_time': 0.0,
                }
            topic_data[key_topic]['total_items_answered'] += 1
            topic_data[key_topic]['total_correct'] += int(selected == correct)
            topic_data[key_topic]['total_time'] += time_spent

            # --- DIFFICULTY ---
            key_diff = (difficulty, board_exam)
            if key_diff not in difficulty_data:
                difficulty_data[key_diff] = {
                    'total_items_answered': 0,
                    'total_correct': 0,
                }
            difficulty_data[key_diff]['total_items_answered'] += 1
            difficulty_data[key_diff]['total_correct'] += int(selected == correct)

    # Convert dicts to list with calculated accuracy
    subject_list = []
    for (subj, be), v in subject_data.items():
        avg_time = v['total_time'] / v['total_items_answered'] if v['total_items_answered'] else 0
        acc = (v['total_correct'] / v['total_items_answered'] * 100) if v['total_items_answered'] else 0
        subject_list.append({
            "subject": subj,
            "board_exam": be,
            "total_items_answered": v['total_items_answered'],
            "total_correct": v['total_correct'],
            "average_time_per_item": round(avg_time, 2),
            "accuracy": round(acc, 2),
        })

    topic_list = []
    for (topic, subj), v in topic_data.items():
        avg_time = v['total_time'] / v['total_items_answered'] if v['total_items_answered'] else 0
        acc = (v['total_correct'] / v['total_items_answered'] * 100) if v['total_items_answered'] else 0
        topic_list.append({
            "subject": subj,
            "topic": topic,
            "total_items_answered": v['total_items_answered'],
            "total_correct": v['total_correct'],
            "average_time_per_item": round(avg_time, 2),
            "accuracy": round(acc, 2),
        })

    difficulty_list = []
    for (diff, be), v in difficulty_data.items():
        acc = (v['total_correct'] / v['total_items_answered'] * 100) if v['total_items_answered'] else 0
        difficulty_list.append({
            "difficulty": diff,
            "board_exam": be,
            "total_items_answered": v['total_items_answered'],
            "total_correct": v['total_correct'],
            "accuracy": round(acc, 2),
        })

    return render(request, "analytics_dashboard.html", {
        "subject_analytics": json.dumps(subject_list, cls=DjangoJSONEncoder),
        "topic_analytics": json.dumps(topic_list, cls=DjangoJSONEncoder),
        "difficulty_analytics": json.dumps(difficulty_list, cls=DjangoJSONEncoder),
        "ai_suggestions": "",  # Optional: call AI here if you want
    })
