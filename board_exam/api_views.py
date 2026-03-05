from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.db import transaction
from .models import QuestionForm, Question, BoardExam, Subject, Topic, DifficultyLevel, Question, QuestionImage, Choice, AnswerKey, TestKey, Teacher, Student, Result, PracticeResult, SubjectAnalytics, TopicAnalytics, DifficultyAnalytics
from .config import BOARD_EXAM_TOPICS
import uuid
import random
import string
import json

# ----------------------------------------
# Simple test endpoint
# ----------------------------------------
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mobile_test(request):
    user = request.user
    return Response({
        "status": "success",
        "message": "EXIM Mobile API is working",
        "user_email": user.email,
        "is_student": user.is_student,
        "is_staff": user.is_staff,
    })



####################### FOR SIGNUP / LOGIN ##############################

@api_view(['POST'])
@permission_classes([AllowAny])
def api_signup(request):
    """
    Mobile student-only signup
    POST data: {
        email, password, student_id, last_name, first_name,
        middle_name, birthdate, course
    }
    """
    data = request.data
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return Response({"error": "Email and password are required"}, status=400)

    if User.objects.filter(email=email).exists():
        return Response({"error": "Email already registered"}, status=400)

    try:
        with transaction.atomic():
            user = User(email=email, is_active=True)
            user.set_password(password)
            user.is_student = True
            user.is_staff = False
            user.save()

            Student.objects.create(
                user=user,
                student_id=data.get('student_id'),
                last_name=data.get('last_name'),
                first_name=data.get('first_name'),
                middle_name=data.get('middle_name', ''),
                birthdate=data.get('birthdate'),
                course=data.get('course', ''),
            )

    except Exception as e:
        return Response({"error": f"Signup failed: {str(e)}"}, status=500)

    return Response({"status": "success", "message": "Student account created successfully"})


@api_view(['POST'])
@permission_classes([AllowAny])
def api_login(request):
    """
    POST data: { "email": "...", "password": "..." }
    """
    email = request.data.get('email')
    password = request.data.get('password')

    if not email or not password:
        return Response({"error": "Email and password are required"}, status=400)

    user = authenticate(request, username=email, password=password)
    if user:
        login(request, user)
        return Response({
            "status": "success",
            "user_email": user.email,
            "is_student": True,
        })
    return Response({"error": "Invalid credentials"}, status=401)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_logout(request):
    logout(request)
    return Response({"status": "success", "message": "Logged out successfully"})


####################### DASHBOARD ROLE ##############################

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_dashboard_redirect(request):
    """
    Mobile is student-only
    """
    return Response({"dashboard": "student"})

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
import numpy as np
import cv2
import gc
import uuid
from .models import AnswerKey, Result, Student, Question, PracticeResult, SubjectAnalytics, TopicAnalytics, DifficultyAnalytics
from django.utils import timezone

# -------------------------------
# Upload exam answer (API)
# -------------------------------
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_upload_answer(request):
    if 'image' not in request.FILES or 'exam_id' not in request.data:
        return Response({"error": "Missing required fields."}, status=400)

    uploaded_image = request.FILES['image']
    exam_id = request.data['exam_id']

    # --- Load models ---
    net_original, classes_original = get_original_model()
    net_cropped, classes_cropped = get_cropped_model()

    # --- Get answer key ---
    answer_key = get_object_or_404(AnswerKey, set_id=exam_id)
    subject = answer_key.subject

    # --- Decode image ---
    nparr = np.frombuffer(uploaded_image.read(), np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    # --- Mask ---
    mask_image = image_to_mask(image)
    if mask_image.ndim == 2:
        mask_image = cv2.cvtColor(mask_image, cv2.COLOR_GRAY2BGR)

    reference_point = (0, 0)
    all_answers = []

    # --- Detect answer boxes ---
    boxes_original, _, class_ids_original = detect_objects(mask_image, net_original, classes_original)

    for i, box in enumerate(boxes_original):
        if classes_original[class_ids_original[i]] != 'answer':
            continue

        x, y, w, h = box
        cropped_object = mask_image[y:y+h, x:x+w]

        # --- Detect bubbles ---
        boxes_cropped, _, class_ids_cropped = detect_objects(cropped_object, net_cropped, classes_cropped)

        object_dict = sort_objects_by_distance(boxes_cropped, class_ids_cropped, classes_cropped, reference_point)
        grouped_boxes = group_and_sequence(object_dict.values(), object_dict.keys())

        seq_num_class_dict = {}
        for seq_num, idx in grouped_boxes.items():
            seq_num_class_dict[seq_num] = classes_cropped[class_ids_cropped[idx - 1]]

        for k in sorted(seq_num_class_dict):
            all_answers.append(seq_num_class_dict[k])

    # --- Compute score ---
    correct_answers = {str(k): v['letter'] for k, v in answer_key.answer_key.items()}
    score = sum(1 for i, a in enumerate(all_answers, start=1) if correct_answers.get(str(i)) == a)
    total_items = len(correct_answers)

    student = get_object_or_404(Student, user_id=request.user)

    if Result.objects.filter(user=request.user, exam_id=exam_id).exists():
        return Response({'warning': 'Answer already uploaded for this exam.'}, status=400)

    # --- Save result ---
    Result.objects.create(
        user=request.user,
        student_id=student.student_id,
        course=student.course,
        student_name=student,
        subject=subject,
        exam_id=exam_id,
        answer=all_answers,
        correct_answer=list(correct_answers.values()),
        score=score,
        total_items=total_items,
        is_submitted=True
    )

    # Cleanup
    del image, mask_image, cropped_object
    gc.collect()

    return Response({
        'score': score,
        'detected': len(all_answers),
        'total_items': total_items
    })


# -------------------------------
# Get random practice exam (API)
# -------------------------------
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_get_practice_exam(request):
    student_course_full = request.user.student.course.strip().lower()
    course_mapping = {
        "civil engineering": "CE",
        "mechanical engineering": "ME",
        "electrical engineering": "EE",
        "electronics engineering": "ECE",
    }
    student_course_code = course_mapping.get(student_course_full)
    if not student_course_code:
        return Response({"error": "Your course is not supported for practice exams."}, status=400)

    subjects = list(BOARD_EXAM_TOPICS.get(student_course_code, {}).keys())
    return Response({"student_course": student_course_code, "subjects": subjects})


# -------------------------------
# Submit practice answers (API)
# -------------------------------
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_submit_practice(request):
    session_id = request.data.get('session_id')
    answers = request.data.get('answers')  # List of {'q_id': int, 'selected': str, 'time_spent': float}

    if not session_id or not answers:
        return Response({"error": "Missing session or answers."}, status=400)

    # Compute score & analytics
    correct_count = 0
    total_time = 0.0
    results = []

    subject_tracker = {}
    topic_tracker = {}
    difficulty_tracker = {}

    for idx, ans in enumerate(answers, start=1):
        q_obj = Question.objects.get(id=ans['q_id'])
        selected = ans['selected']
        time_spent = float(ans.get('time_spent', 0))
        correct_answer = q_obj.choices.filter(is_correct=True).first().text

        is_correct = (selected == correct_answer)
        if is_correct:
            correct_count += 1
        total_time += time_spent

        # Track subject/topic/difficulty
        subject = q_obj.subjects.first().name if q_obj.subjects.exists() else "Unknown"
        topic = q_obj.topic.name if q_obj.topic else "Misc"
        difficulty = q_obj.difficulty.level if q_obj.difficulty else "Unknown"

        # Subject tracker
        subject_tracker.setdefault(subject, {"correct": 0, "total": 0, "time": 0})
        subject_tracker[subject]["total"] += 1
        subject_tracker[subject]["time"] += time_spent
        if is_correct: subject_tracker[subject]["correct"] += 1

        # Topic tracker
        topic_tracker.setdefault(topic, {"correct": 0, "total": 0, "time": 0, "subject": subject})
        topic_tracker[topic]["total"] += 1
        topic_tracker[topic]["time"] += time_spent
        if is_correct: topic_tracker[topic]["correct"] += 1

        # Difficulty tracker
        difficulty_tracker.setdefault(difficulty, {"correct": 0, "total": 0})
        difficulty_tracker[difficulty]["total"] += 1
        if is_correct: difficulty_tracker[difficulty]["correct"] += 1

        results.append({
            "index": idx,
            "q_id": ans['q_id'],
            "selected": selected,
            "correct": correct_answer,
            "is_correct": is_correct,
            "time_spent": time_spent,
        })

    score = correct_count
    total_items = len(answers)
    pct = (score / total_items * 100) if total_items else 0

    # Save practice result
    PracticeResult.objects.create(
        session_id=session_id,
        user=request.user,
        board_exam=student_course_code,
        total_items=total_items,
        score=score,
        percent=pct,
        total_time=total_time,
        answers=results
    )

    return Response({
        "score": score,
        "total_items": total_items,
        "percent": pct,
        "total_time": total_time,
        "results": results
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_analytics_dashboard(request):
    user = request.user
    results = PracticeResult.objects.filter(user=user)

    # Temporary containers
    subject_data = {}
    topic_data = {}
    difficulty_data = {}

    for res in results:
        board_exam = res.board_exam

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
                subject_data[key] = {'total_items_answered': 0, 'total_correct': 0, 'total_time': 0.0}
            subject_data[key]['total_items_answered'] += 1
            subject_data[key]['total_correct'] += int(selected == correct)
            subject_data[key]['total_time'] += time_spent

            # --- TOPIC ---
            key_topic = (topic, subject)
            if key_topic not in topic_data:
                topic_data[key_topic] = {'total_items_answered': 0, 'total_correct': 0, 'total_time': 0.0}
            topic_data[key_topic]['total_items_answered'] += 1
            topic_data[key_topic]['total_correct'] += int(selected == correct)
            topic_data[key_topic]['total_time'] += time_spent

            # --- DIFFICULTY ---
            key_diff = (difficulty, board_exam)
            if key_diff not in difficulty_data:
                difficulty_data[key_diff] = {'total_items_answered': 0, 'total_correct': 0}
            difficulty_data[key_diff]['total_items_answered'] += 1
            difficulty_data[key_diff]['total_correct'] += int(selected == correct)

    # Convert dicts to lists with accuracy
    subject_list = [
        {
            "subject": subj,
            "board_exam": be,
            "total_items_answered": v['total_items_answered'],
            "total_correct": v['total_correct'],
            "average_time_per_item": round(v['total_time']/v['total_items_answered'], 2) if v['total_items_answered'] else 0,
            "accuracy": round(v['total_correct']/v['total_items_answered']*100, 2) if v['total_items_answered'] else 0
        }
        for (subj, be), v in subject_data.items()
    ]

    topic_list = [
        {
            "subject": subj,
            "topic": topic,
            "total_items_answered": v['total_items_answered'],
            "total_correct": v['total_correct'],
            "average_time_per_item": round(v['total_time']/v['total_items_answered'], 2) if v['total_items_answered'] else 0,
            "accuracy": round(v['total_correct']/v['total_items_answered']*100, 2) if v['total_items_answered'] else 0
        }
        for (topic, subj), v in topic_data.items()
    ]

    difficulty_list = [
        {
            "difficulty": diff,
            "board_exam": be,
            "total_items_answered": v['total_items_answered'],
            "total_correct": v['total_correct'],
            "accuracy": round(v['total_correct']/v['total_items_answered']*100, 2) if v['total_items_answered'] else 0
        }
        for (diff, be), v in difficulty_data.items()
    ]

    return Response({
        "subject_analytics": subject_list,
        "topic_analytics": topic_list,
        "difficulty_analytics": difficulty_list,
    })