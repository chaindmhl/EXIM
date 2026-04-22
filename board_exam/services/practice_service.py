# services/practice_service.py
from .firestore_client import db
from firebase_admin import firestore


class PracticeService:

    @staticmethod
    def save_result(session_id, data):
        return db.collection("practice_results").document(session_id).set({
            **data,
            "created_at": firestore.SERVER_TIMESTAMP
        })

    @staticmethod
    def get_result(session_id):
        doc = db.collection("practice_results").document(session_id).get()
        return doc.to_dict() if doc.exists else None

    @staticmethod
    def update_analytics(collection, doc_id, data):
        ref = db.collection(collection).document(doc_id)

        doc = ref.get()
        old = doc.to_dict() if doc.exists else {
            "total_items_answered": 0,
            "total_correct": 0,
            "total_attempts": 0,
            "average_time_per_item": 0
        }

        total_items_answered = old["total_items_answered"] + data["total"]
        total_correct = old["total_correct"] + data["correct"]
        total_attempts = old["total_attempts"] + 1

        prev_avg = old["average_time_per_item"]
        prev_total = old["total_items_answered"]

        new_time = (prev_avg * prev_total) + data.get("time", 0)
        avg_time = new_time / total_items_answered if total_items_answered else 0

        ref.set({
            "total_items_answered": total_items_answered,
            "total_correct": total_correct,
            "total_attempts": total_attempts,
            "average_time_per_item": avg_time
        }, merge=True)