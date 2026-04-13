# services/analytics_service.py

from .firestore_client import db

class AnalyticsService:

    # ---------- SUBJECT ----------
    @staticmethod
    def update_subject(user_id, subject, board_exam, data):
        doc_id = f"{user_id}_{board_exam}_{subject}"
        db.collection("subject_analytics").document(doc_id).set(data, merge=True)

    # ---------- TOPIC ----------
    @staticmethod
    def update_topic(user_id, subject, topic, data):
        doc_id = f"{user_id}_{subject}_{topic}"
        db.collection("topic_analytics").document(doc_id).set(data, merge=True)

    # ---------- DIFFICULTY ----------
    @staticmethod
    def update_difficulty(user_id, board_exam, difficulty, data):
        doc_id = f"{user_id}_{board_exam}_{difficulty}"
        db.collection("difficulty_analytics").document(doc_id).set(data, merge=True)
