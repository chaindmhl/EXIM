# services/result_service.py

from .firestore_client import db
import uuid

class ResultService:

    @staticmethod
    def create(data):
        result_id = str(uuid.uuid4())
        db.collection("results").document(result_id).set(data)
        return result_id

    @staticmethod
    def get_by_user(user_id):
        docs = db.collection("results")\
            .where("user_id", "==", user_id)\
            .stream()

        return [{**d.to_dict(), "id": d.id} for d in docs]

    @staticmethod
    def get_by_exam(exam_id):
        docs = db.collection("results")\
            .where("exam_id", "==", exam_id)\
            .stream()

        return [{**d.to_dict(), "id": d.id} for d in docs]
    
    @staticmethod
    def get_by_exam_ids(exam_ids):
        docs = db.collection("results")\
            .where("exam_id", "in", exam_ids[:10])\
            .stream()

        return [{**d.to_dict(), "id": d.id} for d in docs]
    
    #exam analytics
    @staticmethod
    def get_all():
        docs = db.collection("results").stream()
        return [{**d.to_dict(), "id": d.id} for d in docs]
