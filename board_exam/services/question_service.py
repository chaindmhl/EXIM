from .firestore_client import db
from firebase_admin import firestore
import uuid


class QuestionService:

    COLLECTION = "questions"

    @staticmethod
    def create_question(
        question_text,
        choices,
        image_url,
        level,
        source,
        subject_names,
        topic_name,
        board_exam_list=None
    ):

        # -------------------------
        # 1. Build choices safely
        # -------------------------
        formatted_choices = []
        correct_letter = None

        for i, c in enumerate(choices or []):
            letter = chr(65 + i)

            is_correct = bool(c.get("is_correct"))

            formatted_choices.append({
                "letter": letter,
                "text": c.get("text", "").strip(),
                "is_correct": is_correct
            })

            if is_correct:
                correct_letter = letter

        # -------------------------
        # 2. Firestore save
        # -------------------------
        question_id = str(uuid.uuid4())

        db.collection(QuestionService.COLLECTION).document(question_id).set({
            "question_text": question_text,
            "choices": formatted_choices,
            "correct_letter": correct_letter,
            "image": image_url,
            "difficulty": level,
            "source": source,
            "subjects": subject_names if isinstance(subject_names, list) else [subject_names],
            "topic": topic_name,
            "board_exams": board_exam_list or [],
            "usage_count": 0,
            "created_at": firestore.SERVER_TIMESTAMP
        })

        return question_id

    # -------------------------
    # READ OPERATIONS
    # -------------------------
    @staticmethod
    def get(question_id):
        doc = db.collection(QuestionService.COLLECTION).document(question_id).get()
        return doc.to_dict() if doc.exists else None

    @staticmethod
    def get_all():
        docs = db.collection(QuestionService.COLLECTION).stream()
        return [{**d.to_dict(), "id": d.id} for d in docs]

    @staticmethod
    def get_by_subject(subject):
        docs = (
            db.collection(QuestionService.COLLECTION)
            .where("subjects", "array_contains", subject)
            .stream()
        )

        return [{**d.to_dict(), "id": d.id} for d in docs]

    @staticmethod
    def increment_usage(question_id):
        db.collection(QuestionService.COLLECTION).document(question_id).update({
            "usage_count": firestore.Increment(1)
        })