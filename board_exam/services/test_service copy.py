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

    @staticmethod
    def get_all_tests():
        docs = db.collection("test_keys").stream()
        return [
            {**doc.to_dict(), "id": doc.id}
            for doc in docs
        ]

    # ---------- ANSWER KEY ----------
    @staticmethod
    def create_answer_key(set_id, data):
        db.collection("answer_keys").document(set_id).set(data)

    @staticmethod
    def get_answer_key(set_id):
        doc = db.collection("answer_keys").document(set_id).get()
        return doc.to_dict() if doc.exists else None
    
    @staticmethod
    def get_by_board_and_subject(board_exam, subject):
        docs = db.collection("test_keys")\
            .where("board_exam", "==", board_exam)\
            .where("subject", "==", subject)\
            .stream()

        return [{**d.to_dict(), "id": d.id} for d in docs]
    
    @staticmethod
    def get_all_board_exams():
        docs = db.collection("board_exams").stream()
        return [doc.id for doc in docs]