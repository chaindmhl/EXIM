# services/user_service.py

from .firestore_client import db

class UserService:

    # ---------- USERS ----------
    @staticmethod
    def create_user(user_id, email, is_student=False, is_staff=False):
        db.collection("users").document(user_id).set({
            "email": email,
            "is_student": is_student,
            "is_staff": is_staff,
        })

    @staticmethod
    def get_user(user_id):
        doc = db.collection("users").document(user_id).get()
        return doc.to_dict() if doc.exists else None

    # ---------- STUDENT ----------
    @staticmethod
    def create_student(user_id, data):
        db.collection("students").document(user_id).set(data)

    @staticmethod
    def get_student(user_id):
        doc = db.collection("students").document(user_id).get()
        return doc.to_dict() if doc.exists else None

    # ---------- TEACHER ----------
    @staticmethod
    def create_teacher(user_id, data):
        db.collection("teachers").document(user_id).set(data)
