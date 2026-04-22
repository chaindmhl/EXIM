from .firestore_client import db
from datetime import datetime


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
    
    @staticmethod
    def get_by_id(result_id):
        doc = db.collection("results").document(result_id).get()
        return doc.to_dict() if doc.exists else None
    
    @staticmethod
    def get_by_subject_board_and_date(subject, board_exam, month_num, year):
        docs = db.collection("test_keys") \
            .where("subject", "==", subject) \
            .where("board_exam", "==", board_exam) \
            .stream()

        results = []

        for doc in docs:
            data = doc.to_dict()

            dt = data.get("exam_date")
            if isinstance(dt, str):
                try:
                    dt = datetime.fromisoformat(dt)
                except:
                    dt = None

            if dt and dt.month == month_num and dt.year == year:
                results.append({**data, "id": doc.id})

        return results
    
    @staticmethod
    def search_answer_keys(input_text):
        docs = db.collection("answer_keys").stream()

        return [
            doc.id
            for doc in docs
            if input_text.lower() in doc.id.lower()
        ]
    
    @staticmethod
    def get_all_subjects():
        docs = db.collection("test_keys").stream()

        subjects = set()

        for doc in docs:
            data = doc.to_dict()
            if "subject" in data:
                subjects.add(data["subject"])

        return list(subjects)
    
    
    @staticmethod
    def get_exam_dates_by_board_exam(board_exam):
        docs = db.collection("test_keys") \
            .where("board_exam", "==", board_exam) \
            .stream()

        dates = set()

        for doc in docs:
            data = doc.to_dict()

            dt = data.get("exam_date")

            try:
                if isinstance(dt, str):
                    dt = datetime.fromisoformat(dt)

                if dt:
                    dates.add(dt.strftime("%B-%Y"))
            except:
                continue

        return list(dates)
    
    @staticmethod
    def get_subjects_by_board_exam_and_date(board_exam, exam_date):
        month, year = exam_date.split('-')
        month_num = datetime.strptime(month, "%B").month
        year = int(year)

        docs = db.collection("test_keys") \
            .where("board_exam", "==", board_exam) \
            .stream()

        subjects = set()

        for doc in docs:
            data = doc.to_dict()
            dt = data.get("exam_date")

            try:
                if isinstance(dt, str):
                    dt = datetime.fromisoformat(dt)

                if dt and dt.month == month_num and dt.year == year:
                    subjects.add(data.get("subject"))
            except:
                continue

        return list(subjects)