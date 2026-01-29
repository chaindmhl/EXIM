import firebase_admin
from firebase_admin import credentials, firestore, storage, auth

cred = credentials.Certificate("board_exam/firebase/boardmate-key.json")
firebase_admin.initialize_app(cred, {
    'storageBucket': 'boardmate-c162e.firebasestorage.app'
})

db = firestore.client()
bucket = storage.bucket()
