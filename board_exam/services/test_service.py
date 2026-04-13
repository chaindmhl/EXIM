# services/test_service.py

from .firestore_client import db

class TestService:

    # ---------- TEST KEY ----------
    @staticmethod
    def create_test(set_id, data):
        db.collection("test_keys").document(set_id).set(data)

    @staticmethod
    def get_test(set_id):
        doc = db.collection("test_keys").document(set_id).get()
        return doc.to_dict() if doc.exists else None

    # ---------- ANSWER KEY ----------
    @staticmethod
    def create_answer_key(set_id, data):
        db.collection("answer_keys").document(set_id).set(data)

    @staticmethod
    def get_answer_key(set_id):
        doc = db.collection("answer_keys").document(set_id).get()
        return doc.to_dict() if doc.exists else None
