# services/user_service.py

from .firestore_client import db
from datetime import datetime


class UserService:

    # ---------- INTERNAL: GENERATE STUDENT ID ----------
    @staticmethod
    def _generate_student_id():
        year = datetime.now().year

        docs = db.collection("users") \
            .where("role", "==", "student") \
            .stream()

        count = 0

        for doc in docs:
            sid = doc.to_dict().get("student_id", "")
            if sid and sid.startswith(str(year)):
                count += 1

        return f"{year}-{str(count + 1).zfill(4)}"

    # ---------- USERS ----------
    @staticmethod
    def create_user(
        user_id,
        email,
        role,
        is_student=False,
        is_staff=False,
        **extra_fields   # 🔥 VERY IMPORTANT (flexible)
    ):
        student_id = None

        # 🔥 AUTO GENERATE ONLY FOR STUDENTS
        if role == "student":
            student_id = UserService._generate_student_id()

        user_data = {
            "email": email,
            "role": role,
            "is_student": is_student,
            "is_staff": is_staff,
            "student_id": student_id,
            **extra_fields   # 🔥 include name, course, etc.
        }

        db.collection("users").document(user_id).set(user_data)

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