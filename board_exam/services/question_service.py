# services/question_service.py

from .firestore_client import db
import uuid

class QuestionService:

    COLLECTION = "questions"

    # CREATE QUESTION
    @staticmethod
    def create(data):
        q_id = str(uuid.uuid4())
        db.collection("questions").document(q_id).set(data)
        return q_id

    # GET QUESTION
    @staticmethod
    def get(question_id):
        doc = db.collection("questions").document(question_id).get()
        return doc.to_dict() if doc.exists else None

    # FILTER BY SUBJECT
    @staticmethod
    def get_by_subject(subject):
        docs = db.collection("questions")\
            .where("subjects", "array_contains", subject)\
            .stream()

        return [{**d.to_dict(), "id": d.id} for d in docs]

    # UPDATE USAGE COUNT
    @staticmethod
    def increment_usage(question_id):
        db.collection("questions").document(question_id).update({
            "usage_count": firestore.Increment(1)
        })
